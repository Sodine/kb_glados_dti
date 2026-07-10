# KB GLaDOS

Aplicacao Flask para alimentar a tabela `bot_atendimento_ti.base_conhecimento` no Supabase.

## Recursos

- Login com usuario e senha.
- CRUD da base de conhecimento.
- Painel de usuarios.
- Permissoes separadas para leitura, criacao, edicao, exclusao e gerenciamento de usuarios.
- Dockerfile pronto para EasyPanel.

## Tabelas

A tabela existente deve estar no schema `bot_atendimento_ti`:

```sql
base_conhecimento (
  id,
  assunto,
  resumo,
  instrucao
)
```

Crie a tabela de usuarios executando no SQL Editor do Supabase:

```sql
-- arquivo: sql/001_create_usuarios_painel.sql
```

Ela sera criada com colunas em portugues: `usuario`, `senha_hash`, `pode_ler`, `pode_criar`, `pode_editar`, `pode_excluir`, `pode_gerenciar_usuarios`, `ativo`, `criado_em` e `atualizado_em`.

No Supabase, confirme tambem se o schema `bot_atendimento_ti` esta exposto em `Project Settings > API > Exposed schemas`, pois a aplicacao usa a API REST do Supabase com esse schema.

## Variaveis de ambiente

Copie `.env.example` para `.env` no desenvolvimento local ou cadastre as mesmas variaveis no EasyPanel.

Obrigatorias:

```env
FLASK_SECRET_KEY=troque-por-uma-chave-grande-e-aleatoria
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=cole-sua-service-role-key-aqui
SUPABASE_SCHEMA=bot_atendimento_ti
KB_TABLE=base_conhecimento
USERS_TABLE=usuarios_painel
```

Administrador inicial:

```env
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
BOOTSTRAP_ADMIN=true
```

Quando a tabela `usuarios_painel` estiver vazia, a aplicacao cria esse usuario automaticamente. Depois do primeiro acesso, altere a senha no painel de usuarios.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app wsgi run --debug
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app wsgi run --debug
```

## Docker

```bash
docker compose up --build
```

A aplicacao sobe na porta `8000`.

## EasyPanel

1. Crie um novo app usando este projeto/repo.
2. Selecione deploy por Dockerfile.
3. Configure o dominio `sp.supersupply.tech`.
4. Cadastre as variaveis do `.env.example` no painel.
5. Aponte a porta interna para `8000`.
6. Faca o deploy.

Use `SESSION_COOKIE_SECURE=true` quando o acesso estiver por HTTPS.

Healthcheck opcional: `/healthz`.
