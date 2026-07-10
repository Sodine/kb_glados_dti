from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from .security import (
    PERMISSIONS,
    current_user_can,
    login_required,
    normalize_username,
    permission_required,
)
from .supabase_gateway import SupabaseError

bp = Blueprint("main", __name__)


def _wants_next():
    next_url = request.args.get("next") or request.form.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return None


def _kb_payload():
    return {
        "assunto": request.form.get("assunto", "").strip(),
        "resumo": request.form.get("resumo", "").strip(),
        "instrucao": request.form.get("instrucao", "").strip(),
    }


def _validate_kb_payload(data):
    errors = []
    if not data["assunto"]:
        errors.append("Informe o assunto.")
    if len(data["assunto"]) > 180:
        errors.append("O assunto deve ter no maximo 180 caracteres.")
    if not data["resumo"]:
        errors.append("Informe o resumo.")
    if not data["instrucao"]:
        errors.append("Informe a instrucao.")
    return errors


def _user_payload(include_password=False):
    data = {
        "username": normalize_username(request.form.get("username")),
        "can_read": "can_read" in request.form,
        "can_create": "can_create" in request.form,
        "can_edit": "can_edit" in request.form,
        "can_delete": "can_delete" in request.form,
        "can_manage_users": "can_manage_users" in request.form,
        "is_active": "is_active" in request.form,
    }

    password = request.form.get("password", "")
    if include_password or password:
        data["password_hash"] = generate_password_hash(password)
    return data


def _validate_user_payload(data, creating=False):
    errors = []
    password = request.form.get("password", "")

    if not data["username"]:
        errors.append("Informe o usuario.")
    if len(data["username"]) > 80:
        errors.append("O usuario deve ter no maximo 80 caracteres.")
    if creating and not password:
        errors.append("Informe a senha inicial.")
    if password and len(password) < 6:
        errors.append("A senha deve ter pelo menos 6 caracteres.")
    if not any(data.get(permission) for permission in PERMISSIONS):
        errors.append("Selecione pelo menos uma permissao.")
    return errors


@bp.get("/")
def index():
    if not g.user:
        return redirect(url_for("main.login"))
    if current_user_can("can_read"):
        return redirect(url_for("main.kb_list"))
    if current_user_can("can_create"):
        return redirect(url_for("main.kb_new"))
    if current_user_can("can_manage_users"):
        return redirect(url_for("main.users_list"))
    return render_template("no_access.html")


@bp.get("/healthz")
def healthz():
    return {"status": "ok"}


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = normalize_username(request.form.get("username"))
        password = request.form.get("password", "")

        try:
            user = current_app.supabase.get_user_by_username(username)
        except SupabaseError as exc:
            flash(str(exc), "error")
            return render_template("login.html", next_url=_wants_next())

        if (
            user
            and user.get("is_active")
            and check_password_hash(user.get("password_hash", ""), password)
        ):
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            flash("Acesso liberado.", "success")
            return redirect(_wants_next() or url_for("main.index"))

        flash("Usuario ou senha invalidos.", "error")

    return render_template("login.html", next_url=_wants_next())


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Sessao encerrada.", "success")
    return redirect(url_for("main.login"))


@bp.get("/base")
@permission_required("can_read")
def kb_list():
    try:
        records = current_app.supabase.list_kb()
    except SupabaseError as exc:
        flash(str(exc), "error")
        records = []

    return render_template("kb/list.html", records=records)


@bp.route("/base/novo", methods=["GET", "POST"])
@permission_required("can_create")
def kb_new():
    record = {"assunto": "", "resumo": "", "instrucao": ""}

    if request.method == "POST":
        record = _kb_payload()
        errors = _validate_kb_payload(record)

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            try:
                created = current_app.supabase.create_kb(record)
                flash("Registro criado.", "success")
                return redirect(url_for("main.kb_edit", record_id=created["id"]))
            except SupabaseError as exc:
                flash(str(exc), "error")

    return render_template("kb/form.html", record=record, mode="create")


@bp.route("/base/<record_id>/editar", methods=["GET", "POST"])
@permission_required("can_edit")
def kb_edit(record_id):
    try:
        record = current_app.supabase.get_kb(record_id)
    except SupabaseError as exc:
        flash(str(exc), "error")
        return redirect(url_for("main.kb_list"))

    if not record:
        abort(404)

    if request.method == "POST":
        payload = _kb_payload()
        errors = _validate_kb_payload(payload)

        if errors:
            for error in errors:
                flash(error, "error")
            record.update(payload)
        else:
            try:
                current_app.supabase.update_kb(record_id, payload)
                flash("Registro atualizado.", "success")
                return redirect(url_for("main.kb_list"))
            except SupabaseError as exc:
                flash(str(exc), "error")
                record.update(payload)

    return render_template("kb/form.html", record=record, mode="edit")


@bp.post("/base/<record_id>/excluir")
@permission_required("can_delete")
def kb_delete(record_id):
    try:
        current_app.supabase.delete_kb(record_id)
        flash("Registro excluido.", "success")
    except SupabaseError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.kb_list"))


@bp.get("/usuarios")
@permission_required("can_manage_users")
def users_list():
    try:
        users = current_app.supabase.list_users()
    except SupabaseError as exc:
        flash(str(exc), "error")
        users = []

    return render_template("users/list.html", users=users)


@bp.route("/usuarios/novo", methods=["GET", "POST"])
@permission_required("can_manage_users")
def users_new():
    user = {
        "username": "",
        "can_read": True,
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_manage_users": False,
        "is_active": True,
    }

    if request.method == "POST":
        payload = _user_payload(include_password=True)
        errors = _validate_user_payload(payload, creating=True)

        if errors:
            for error in errors:
                flash(error, "error")
            user.update(payload)
        else:
            try:
                current_app.supabase.create_user(payload)
                flash("Usuario criado.", "success")
                return redirect(url_for("main.users_list"))
            except SupabaseError as exc:
                flash(str(exc), "error")
                user.update(payload)

    return render_template("users/form.html", user=user, mode="create")


@bp.route("/usuarios/<user_id>/editar", methods=["GET", "POST"])
@permission_required("can_manage_users")
def users_edit(user_id):
    try:
        user = current_app.supabase.get_user(user_id)
    except SupabaseError as exc:
        flash(str(exc), "error")
        return redirect(url_for("main.users_list"))

    if not user:
        abort(404)

    if request.method == "POST":
        payload = _user_payload(include_password=False)

        if user_id == g.user["id"]:
            payload["is_active"] = True
            payload["can_manage_users"] = True

        errors = _validate_user_payload(payload, creating=False)

        if errors:
            for error in errors:
                flash(error, "error")
            user.update(payload)
        else:
            try:
                current_app.supabase.update_user(user_id, payload)
                flash("Usuario atualizado.", "success")
                return redirect(url_for("main.users_list"))
            except SupabaseError as exc:
                flash(str(exc), "error")
                user.update(payload)

    return render_template("users/form.html", user=user, mode="edit")


@bp.post("/usuarios/<user_id>/excluir")
@permission_required("can_manage_users")
def users_delete(user_id):
    if user_id == g.user["id"]:
        flash("Nao e possivel excluir o proprio usuario em uso.", "error")
        return redirect(url_for("main.users_list"))

    try:
        current_app.supabase.delete_user(user_id)
        flash("Usuario excluido.", "success")
    except SupabaseError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.users_list"))


@bp.app_errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message="Requisicao invalida."), 400


@bp.app_errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, message="Acesso negado."), 403


@bp.app_errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="Registro nao encontrado."), 404
