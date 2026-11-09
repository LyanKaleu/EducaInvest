"""Controle de acesso por perfil, compartilhado pelos Blueprints (RNF04)."""
from flask import abort, redirect, session, url_for


def exigir_perfil(perfil: str):
    """Cria a verificação `before_request` que só deixa passar o `perfil` informado.

    Args:
        perfil: perfil exigido ("ALUNO" ou "PROFESSOR").

    Returns:
        Função para `Blueprint.before_request`: sem login redireciona para
        /login; com outro perfil responde 403.
    """
    def verificar():
        if "usuario_id" not in session:
            return redirect(url_for("auth.login"))
        if session.get("perfil") != perfil:
            abort(403)
        return None

    return verificar
