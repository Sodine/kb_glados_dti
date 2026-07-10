from urllib.parse import quote

import requests
from werkzeug.security import generate_password_hash


class SupabaseError(RuntimeError):
    pass


class SupabaseGateway:
    def __init__(self, url, key, schema, kb_table, users_table, timeout=20):
        self.url = url
        self.key = key
        self.schema = schema
        self.kb_table = kb_table
        self.users_table = users_table
        self.timeout = timeout
        self.session = requests.Session()

    USER_DB_TO_APP = {
        "usuario": "username",
        "senha_hash": "password_hash",
        "pode_ler": "can_read",
        "pode_criar": "can_create",
        "pode_editar": "can_edit",
        "pode_excluir": "can_delete",
        "pode_gerenciar_usuarios": "can_manage_users",
        "ativo": "is_active",
        "criado_em": "created_at",
        "atualizado_em": "updated_at",
    }
    USER_APP_TO_DB = {app: db for db, app in USER_DB_TO_APP.items()}
    USER_SELECT_PUBLIC = (
        "id,usuario,pode_ler,pode_criar,pode_editar,pode_excluir,"
        "pode_gerenciar_usuarios,ativo,criado_em,atualizado_em"
    )
    USER_SELECT_PRIVATE = (
        "id,usuario,senha_hash,pode_ler,pode_criar,pode_editar,pode_excluir,"
        "pode_gerenciar_usuarios,ativo,criado_em,atualizado_em"
    )

    @property
    def configured(self):
        return bool(self.url and self.key)

    def _headers(self, method, prefer="return=representation"):
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": prefer,
        }
        if method.upper() in {"GET", "HEAD"}:
            headers["Accept-Profile"] = self.schema
        else:
            headers["Content-Profile"] = self.schema
            headers["Accept-Profile"] = self.schema
        return headers

    def _request(self, method, table, params=None, json=None, prefer="return=representation"):
        if not self.configured:
            raise SupabaseError(
                "Supabase nao configurado. Defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
            )

        endpoint = f"{self.url}/rest/v1/{quote(table)}"

        try:
            response = self.session.request(
                method,
                endpoint,
                params=params,
                json=json,
                headers=self._headers(method, prefer=prefer),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise SupabaseError(f"Falha de conexao com o Supabase: {exc}") from exc

        if response.status_code >= 400:
            detail = response.text.strip() or response.reason
            raise SupabaseError(f"Supabase retornou HTTP {response.status_code}: {detail}")

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise SupabaseError("Resposta invalida recebida do Supabase.") from exc

    def _user_from_db(self, row):
        if not row:
            return row
        user = {"id": row.get("id")}
        for db_key, app_key in self.USER_DB_TO_APP.items():
            user[app_key] = row.get(db_key)
        return user

    def _users_from_db(self, rows):
        return [self._user_from_db(row) for row in rows or []]

    def _user_to_db(self, data):
        db_data = {}
        for key, value in data.items():
            db_data[self.USER_APP_TO_DB.get(key, key)] = value
        return db_data

    def list_kb(self):
        return self._request(
            "GET",
            self.kb_table,
            params={
                "select": "id,assunto,resumo,instrucao",
                "order": "assunto.asc",
            },
        )

    def get_kb(self, record_id):
        rows = self._request(
            "GET",
            self.kb_table,
            params={
                "select": "id,assunto,resumo,instrucao",
                "id": f"eq.{record_id}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def create_kb(self, data):
        rows = self._request("POST", self.kb_table, json=data)
        return rows[0] if rows else None

    def update_kb(self, record_id, data):
        rows = self._request(
            "PATCH",
            self.kb_table,
            params={"id": f"eq.{record_id}"},
            json=data,
        )
        return rows[0] if rows else None

    def delete_kb(self, record_id):
        self._request(
            "DELETE",
            self.kb_table,
            params={"id": f"eq.{record_id}"},
            prefer="return=minimal",
        )

    def list_users(self, limit=None):
        params = {
            "select": self.USER_SELECT_PUBLIC,
            "order": "usuario.asc",
        }
        if limit:
            params["limit"] = str(limit)
        rows = self._request("GET", self.users_table, params=params)
        return self._users_from_db(rows)

    def get_user(self, user_id):
        rows = self._request(
            "GET",
            self.users_table,
            params={
                "select": self.USER_SELECT_PRIVATE,
                "id": f"eq.{user_id}",
                "limit": "1",
            },
        )
        return self._user_from_db(rows[0]) if rows else None

    def get_user_by_username(self, username):
        rows = self._request(
            "GET",
            self.users_table,
            params={
                "select": self.USER_SELECT_PRIVATE,
                "usuario": f"eq.{username}",
                "limit": "1",
            },
        )
        return self._user_from_db(rows[0]) if rows else None

    def create_user(self, data):
        rows = self._request("POST", self.users_table, json=self._user_to_db(data))
        return self._user_from_db(rows[0]) if rows else None

    def update_user(self, user_id, data):
        rows = self._request(
            "PATCH",
            self.users_table,
            params={"id": f"eq.{user_id}"},
            json=self._user_to_db(data),
        )
        return self._user_from_db(rows[0]) if rows else None

    def delete_user(self, user_id):
        self._request(
            "DELETE",
            self.users_table,
            params={"id": f"eq.{user_id}"},
            prefer="return=minimal",
        )


def bootstrap_default_admin(gateway, username, password, logger=None):
    if not gateway.configured:
        return

    normalized = (username or "admin").strip().lower()
    password = password or "admin123"

    try:
        existing = gateway.list_users(limit=1)
        if existing:
            return

        gateway.create_user(
            {
                "username": normalized,
                "password_hash": generate_password_hash(password),
                "can_read": True,
                "can_create": True,
                "can_edit": True,
                "can_delete": True,
                "can_manage_users": True,
                "is_active": True,
            }
        )
        if logger:
            logger.warning("Usuario administrador inicial criado: %s", normalized)
    except SupabaseError as exc:
        if logger:
            logger.warning("Nao foi possivel criar o administrador inicial: %s", exc)
