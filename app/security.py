from functools import wraps
from secrets import token_urlsafe

from flask import abort, current_app, g, redirect, request, session, url_for

from .supabase_gateway import SupabaseError


PERMISSIONS = {
    "can_read": "Leitura",
    "can_create": "Criacao",
    "can_edit": "Edicao",
    "can_delete": "Exclusao",
    "can_manage_users": "Usuarios",
}


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = token_urlsafe(32)
    return session["_csrf_token"]


def validate_csrf():
    expected = session.get("_csrf_token")
    received = request.form.get("_csrf_token")
    return bool(expected and received and expected == received)


def normalize_username(username):
    return (username or "").strip().lower()


def current_user_can(permission):
    user = getattr(g, "user", None)
    return bool(user and user.get(permission))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "user", None):
            return redirect(url_for("main.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user_can(permission):
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def register_security_hooks(app):
    @app.before_request
    def load_user_and_protect_forms():
        g.user = None
        g.supabase_error = None

        if request.endpoint == "static":
            return None

        if request.method == "POST" and not validate_csrf():
            abort(400)

        user_id = session.get("user_id")
        if not user_id:
            return None

        try:
            user = current_app.supabase.get_user(user_id)
        except SupabaseError as exc:
            g.supabase_error = str(exc)
            return None

        if not user or not user.get("is_active"):
            session.clear()
            return None

        g.user = user
        return None

    @app.context_processor
    def inject_security_helpers():
        return {
            "PERMISSIONS": PERMISSIONS,
            "current_user_can": current_user_can,
        }
