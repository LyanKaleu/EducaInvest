"""Rotas de cadastro, login e logout (RF01).

O aluno se cadastra com o código da turma; o professor, sem código.
"""

from datetime import UTC, datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.typing import ResponseReturnValue

from app.db import obter_conexao
from app.repositories.turma_repo import TurmaRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.services import auth_service
from app.services.erros import ErroValidacao
from app.services.limite_service import LimiteDeTentativas

bp = Blueprint("auth", __name__)

MSG_ERRO_FORM = "Não foi possível continuar. Confira os campos destacados."
MSG_LOGIN_INVALIDO = "E-mail ou senha incorretos."
# Esta mensagem revela se um e-mail já tem conta (enumeração). Risco ACEITO no
# MVP (ver ESTADO.md): sem envio de e-mail não dá para o "cadastro silencioso",
# e limitar por IP brigaria com a turma saindo pelo mesmo Wi-Fi da escola. A UX
# de mandar logar vale mais.
MSG_EMAIL_EM_USO = "Este e-mail já está cadastrado."
MSG_MUITAS_TENTATIVAS = (
    "Muitas tentativas para este e-mail. Espere 15 minutos e tente de novo."
)

# Contra senha por tentativa e erro: 5 senhas erradas bloqueiam o e-mail por 15
# min. Conta por e-mail, não por IP: a turma inteira sai pelo mesmo Wi-Fi da
# escola.
FALHAS_DE_LOGIN = 5
JANELA_DE_LOGIN_SEGUNDOS = 15 * 60


def _limite_de_login() -> LimiteDeTentativas:
    """Um contador por app (os testes criam um app novo a cada teste)."""
    return current_app.extensions.setdefault(
        "limite_de_login",
        LimiteDeTentativas(FALHAS_DE_LOGIN, JANELA_DE_LOGIN_SEGUNDOS),
    )


def destino_do_perfil(perfil: str) -> str:
    """Página inicial de cada perfil depois de entrar."""
    return (
        url_for("professor.turmas")
        if perfil == auth_service.PERFIL_PROFESSOR
        else url_for("painel.ver")
    )


def _iniciar_sessao(usuario: dict) -> ResponseReturnValue:
    # Descarta qualquer sessão anterior (evita fixação de sessão).
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["perfil"] = usuario["perfil"]
    session["apelido"] = usuario[
        "apelido"
    ]  # só para mostrar no topo; o acesso usa o perfil
    return redirect(destino_do_perfil(usuario["perfil"]))


def _render_cadastro(
    *, professor: bool, erros: dict[str, str] | None = None, status: int = 200
) -> ResponseReturnValue:
    # Nunca devolve a senha para a página: o template não preenche esse campo.
    html = render_template(
        "auth/cadastro.html",
        professor=professor,
        form=request.form,
        erros=erros or {},
    )
    return html, status


def _cadastro_invalido(erros: dict, *, professor: bool) -> ResponseReturnValue:
    """Avisa o erro (flash) e devolve o cadastro preenchido, com 400."""
    flash(MSG_ERRO_FORM, "erro")
    return _render_cadastro(professor=professor, erros=erros, status=400)


# ---------------------------------------------------------------------------
# Cadastro
# ---------------------------------------------------------------------------


@bp.get("/cadastro")
def cadastro() -> ResponseReturnValue:
    """Formulário de cadastro do aluno."""
    return _render_cadastro(professor=False)


@bp.post("/cadastro")
def cadastrar_aluno() -> ResponseReturnValue:
    """Cadastra o aluno na turma do código e já entra na conta."""
    usuarios = UsuarioRepository(obter_conexao())
    turmas = TurmaRepository(obter_conexao())
    try:
        dados = auth_service.validar_cadastro_aluno(request.form)
    except ErroValidacao as erro:
        return _cadastro_invalido(erro.erros, professor=False)

    erros = {}
    turma = turmas.buscar_por_codigo(dados["codigo_turma"])
    if turma is None:
        erros["codigo_turma"] = "Código de turma inválido."
    if usuarios.buscar_por_email(dados["email"]):
        erros["email"] = MSG_EMAIL_EM_USO
    if erros:
        return _cadastro_invalido(erros, professor=False)

    with obter_conexao():
        usuario = usuarios.criar(
            auth_service.PERFIL_ALUNO,
            dados["apelido"],
            dados["email"],
            auth_service.gerar_hash_senha(dados["senha"]),
            consentimento_em=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        turmas.matricular(usuario["id"], turma["id"])
    return _iniciar_sessao(usuario)


@bp.get("/cadastro/professor")
def cadastro_professor() -> ResponseReturnValue:
    """Formulário de cadastro do professor."""
    return _render_cadastro(professor=True)


@bp.post("/cadastro/professor")
def cadastrar_professor() -> ResponseReturnValue:
    """Cadastra o professor e já entra na conta."""
    usuarios = UsuarioRepository(obter_conexao())
    try:
        dados = auth_service.validar_cadastro_professor(request.form)
    except ErroValidacao as erro:
        return _cadastro_invalido(erro.erros, professor=True)

    if usuarios.buscar_por_email(dados["email"]):
        return _cadastro_invalido({"email": MSG_EMAIL_EM_USO}, professor=True)

    with obter_conexao():
        usuario = usuarios.criar(
            auth_service.PERFIL_PROFESSOR,
            dados["apelido"],
            dados["email"],
            auth_service.gerar_hash_senha(dados["senha"]),
        )
    return _iniciar_sessao(usuario)


# ---------------------------------------------------------------------------
# Login e logout
# ---------------------------------------------------------------------------


@bp.get("/login")
def login() -> ResponseReturnValue:
    """Formulário de login."""
    return render_template("auth/login.html", form={}, erros={})


@bp.post("/login")
def entrar() -> ResponseReturnValue:
    """Confere e-mail e senha, com limite de tentativas, e abre a sessão."""
    try:
        dados = auth_service.validar_login(request.form)
    except ErroValidacao as erro:
        return render_template(
            "auth/login.html", form=request.form, erros=erro.erros
        ), 400

    limite = _limite_de_login()
    # A tentativa conta antes de conferir a senha: chutes simultâneos não furam
    # o teto.
    if not limite.tentar(dados["email"]):
        # Bloqueia mesmo com a senha certa: senão o chute continuaria até
        # acertar.
        flash(MSG_MUITAS_TENTATIVAS, "erro")
        return render_template(
            "auth/login.html", form=request.form, erros={}
        ), 429

    usuarios = UsuarioRepository(obter_conexao())
    usuario = usuarios.buscar_por_email(dados["email"])
    confere, hash_novo = False, None
    if usuario is not None:
        confere, hash_novo = auth_service.conferir_senha(
            usuario["senha_hash"], dados["senha"]
        )
    if not confere:
        # Mesma mensagem nos dois casos: não revela quais e-mails estão
        # cadastrados.
        flash(MSG_LOGIN_INVALIDO, "erro")
        return render_template(
            "auth/login.html", form=request.form, erros={}
        ), 401
    if hash_novo:
        # Conta antiga (scrypt) ou parâmetros desatualizados: regrava em
        # Argon2id.
        with obter_conexao():
            usuarios.atualizar_senha_hash(usuario["id"], hash_novo)
    limite.limpar(dados["email"])
    return _iniciar_sessao(usuario)


@bp.post("/logout")
def sair() -> ResponseReturnValue:
    """Encerra a sessão e volta para o login."""
    session.clear()
    return redirect(url_for("auth.login"))
