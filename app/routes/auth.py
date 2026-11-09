"""Rotas de cadastro (aluno com código de turma, professor), login e logout (RF01)."""
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.db import obter_conexao
from app.repositories.turma_repo import TurmaRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import auth_service
from app.services.erros import ErroValidacao

bp = Blueprint("auth", __name__)

MSG_ERRO_FORM = "Não foi possível continuar. Confira os campos destacados."
MSG_LOGIN_INVALIDO = "E-mail ou senha incorretos."
MSG_EMAIL_EM_USO = "Este e-mail já está cadastrado."


def destino_do_perfil(perfil: str) -> str:
    """Página inicial de cada perfil depois de entrar."""
    return url_for("professor.turmas") if perfil == auth_service.PERFIL_PROFESSOR else url_for("lancamentos.listar")


def _iniciar_sessao(usuario: dict):
    session.clear()  # descarta qualquer sessão anterior (evita fixação de sessão)
    session["usuario_id"] = usuario["id"]
    session["perfil"] = usuario["perfil"]
    return redirect(destino_do_perfil(usuario["perfil"]))


def _render_cadastro(professor: bool, erros=None, status=200):
    # Nunca devolve a senha para a página: o template não preenche esse campo.
    html = render_template("auth/cadastro.html", professor=professor,
                           form=request.form, erros=erros or {})
    return html, status


def _cadastro_invalido(professor: bool, erros: dict):
    """Avisa o erro (flash) e devolve o formulário de cadastro preenchido, com 400."""
    flash(MSG_ERRO_FORM, "erro")
    return _render_cadastro(professor, erros, 400)


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------

@bp.get("/cadastro")
def cadastro():
    return _render_cadastro(professor=False)


@bp.post("/cadastro")
def cadastrar_aluno():
    usuarios = UsuarioRepository(obter_conexao())
    turmas = TurmaRepository(obter_conexao())
    try:
        dados = auth_service.validar_cadastro_aluno(request.form)
    except ErroValidacao as erro:
        return _cadastro_invalido(False, erro.erros)

    erros = {}
    turma = turmas.buscar_por_codigo(dados["codigo_turma"])
    if turma is None:
        erros["codigo_turma"] = "Código de turma inválido."
    if usuarios.buscar_por_email(dados["email"]):
        erros["email"] = MSG_EMAIL_EM_USO
    if erros:
        return _cadastro_invalido(False, erros)

    with obter_conexao():
        usuario = usuarios.criar(
            auth_service.PERFIL_ALUNO, dados["apelido"], dados["email"],
            auth_service.gerar_hash_senha(dados["senha"]),
            consentimento_em=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        turmas.matricular(usuario["id"], turma["id"])
    return _iniciar_sessao(usuario)


@bp.get("/cadastro/professor")
def cadastro_professor():
    return _render_cadastro(professor=True)


@bp.post("/cadastro/professor")
def cadastrar_professor():
    usuarios = UsuarioRepository(obter_conexao())
    try:
        dados = auth_service.validar_cadastro_professor(request.form)
    except ErroValidacao as erro:
        return _cadastro_invalido(True, erro.erros)

    if usuarios.buscar_por_email(dados["email"]):
        return _cadastro_invalido(True, {"email": MSG_EMAIL_EM_USO})

    with obter_conexao():
        usuario = usuarios.criar(auth_service.PERFIL_PROFESSOR, dados["apelido"], dados["email"],
                                 auth_service.gerar_hash_senha(dados["senha"]))
    return _iniciar_sessao(usuario)


# ---------------------------------------------------------------------------
# Login e logout
# ---------------------------------------------------------------------------

@bp.get("/login")
def login():
    return render_template("auth/login.html", form={}, erros={})


@bp.post("/login")
def entrar():
    try:
        dados = auth_service.validar_login(request.form)
    except ErroValidacao as erro:
        return render_template("auth/login.html", form=request.form, erros=erro.erros), 400

    usuario = UsuarioRepository(obter_conexao()).buscar_por_email(dados["email"])
    if usuario is None or not auth_service.senha_confere(usuario["senha_hash"], dados["senha"]):
        # Mesma mensagem nos dois casos: não revela quais e-mails estão cadastrados.
        flash(MSG_LOGIN_INVALIDO, "erro")
        return render_template("auth/login.html", form=request.form, erros={}), 401
    return _iniciar_sessao(usuario)


@bp.post("/logout")
def sair():
    session.clear()
    return redirect(url_for("auth.login"))
