"""Fábrica da aplicação: cria o app Flask, configura, liga o banco e registra as rotas."""
import os
import secrets

from flask import Flask, redirect, session, url_for

from app import db
from app.filtros import registrar_filtros
from app.routes.auth import bp as auth_bp
from app.routes.auth import destino_do_perfil
from app.routes.lancamentos import bp as lancamentos_bp
from app.routes.missoes import bp as missoes_bp
from app.routes.professor import bp as professor_bp


def create_app(config: dict | None = None) -> Flask:
    """Cria o app. `config` sobrescreve os valores padrão (usado em testes e no run.py).

    Raises:
        RuntimeError: se não houver SECRET_KEY e o app não estiver em teste nem em debug.
    """
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        # instance/ fica fora do Git (.gitignore) e guarda o arquivo do banco.
        DATABASE=os.path.join(app.instance_path, "educainvest.db"),
        # Cookie de sessão não é enviado em POST vindo de outro site (reduz CSRF).
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    if not app.config["SECRET_KEY"]:
        if not (app.config.get("TESTING") or app.config.get("DEBUG")):
            raise RuntimeError(
                "Defina a variável de ambiente SECRET_KEY antes de iniciar o app. "
                'Gere uma com: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        # Só em teste/desenvolvimento: chave aleatória (sessões caem ao reiniciar).
        app.config["SECRET_KEY"] = secrets.token_hex(32)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    registrar_filtros(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(missoes_bp)
    app.register_blueprint(professor_bp)

    @app.get("/")
    def inicio():
        if "usuario_id" not in session:
            return redirect(url_for("auth.login"))
        return redirect(destino_do_perfil(session["perfil"]))

    return app
