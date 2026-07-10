from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config
from .routes import bp
from .security import csrf_token, register_security_hooks
from .supabase_gateway import SupabaseGateway, bootstrap_default_admin


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    app.supabase = SupabaseGateway(
        url=app.config["SUPABASE_URL"],
        key=app.config["SUPABASE_SERVICE_ROLE_KEY"],
        schema=app.config["SUPABASE_SCHEMA"],
        kb_table=app.config["KB_TABLE"],
        users_table=app.config["USERS_TABLE"],
        timeout=app.config["SUPABASE_TIMEOUT"],
    )

    register_security_hooks(app)
    app.jinja_env.globals["csrf_token"] = csrf_token
    app.register_blueprint(bp)

    if app.config["BOOTSTRAP_ADMIN"]:
        bootstrap_default_admin(
            app.supabase,
            username=app.config["DEFAULT_ADMIN_USERNAME"],
            password=app.config["DEFAULT_ADMIN_PASSWORD"],
            logger=app.logger,
        )

    return app
