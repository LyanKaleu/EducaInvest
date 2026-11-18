"""Fluxo HTTP de cadastro com código de turma, login, logout e acesso por perfil (RF01, RNF04, HU5)."""
import pytest
from werkzeug.security import generate_password_hash

from app.db import conectar
from app.repositories.usuario_repo import UsuarioRepository
from app.services import auth_service
from tests.conftest import SENHA, cadastrar_aluno, cadastrar_professor, entrar


def caminho(resposta):
    return resposta.headers["Location"]


# ---------------------------------------------------------------------------
# Cadastro do aluno
# ---------------------------------------------------------------------------

def test_pagina_de_cadastro_mostra_o_formulario(cliente_anonimo):
    html = cliente_anonimo.get("/cadastro").get_data(as_text=True)

    for campo in ("apelido", "email", "senha", "codigo_turma", "consentimento"):
        assert f'name="{campo}"' in html


def test_cadastro_de_aluno_valido_redireciona_para_o_painel(app, turma):
    resposta = cadastrar_aluno(app.test_client(), turma["codigo"])

    assert resposta.status_code == 302
    assert caminho(resposta).endswith("/painel/")


def test_aluno_fica_logado_depois_do_cadastro(cliente_aluno):
    assert cliente_aluno.get("/lancamentos/").status_code == 200


def test_cadastro_aceita_codigo_da_turma_em_minusculas(app, turma):
    resposta = cadastrar_aluno(app.test_client(), turma["codigo"].lower())

    assert resposta.status_code == 302


@pytest.mark.usefixtures("turma")
def test_cadastro_com_codigo_inexistente_retorna_400(cliente_anonimo):
    resposta = cadastrar_aluno(cliente_anonimo, "ZZZZZZ")

    assert resposta.status_code == 400
    assert "Código de turma inválido." in resposta.get_data(as_text=True)


def test_cadastro_sem_consentimento_retorna_400(cliente_anonimo, turma):
    resposta = cadastrar_aluno(cliente_anonimo, turma["codigo"], consentimento="")

    assert resposta.status_code == 400
    assert "Você precisa confirmar a autorização para continuar." in resposta.get_data(as_text=True)


@pytest.mark.usefixtures("cliente_aluno")
def test_cadastro_com_email_ja_usado_retorna_400(app, turma):
    resposta = cadastrar_aluno(app.test_client(), turma["codigo"], email="GABRIEL@escola.br")

    assert resposta.status_code == 400
    assert "Este e-mail já está cadastrado." in resposta.get_data(as_text=True)


@pytest.mark.usefixtures("turma")
def test_cadastro_invalido_preserva_apelido_e_email(cliente_anonimo):
    html = cadastrar_aluno(cliente_anonimo, "ZZZZZZ").get_data(as_text=True)

    assert 'value="Gabriel"' in html
    assert 'value="gabriel@escola.br"' in html


@pytest.mark.usefixtures("turma")
def test_cadastro_invalido_nunca_devolve_a_senha_na_pagina(cliente_anonimo):
    html = cadastrar_aluno(cliente_anonimo, "ZZZZZZ").get_data(as_text=True)

    assert SENHA not in html


# ---------------------------------------------------------------------------
# Cadastro do professor
# ---------------------------------------------------------------------------

def test_cadastro_de_professor_valido_redireciona_para_turmas(cliente_anonimo):
    resposta = cadastrar_professor(cliente_anonimo)

    assert resposta.status_code == 302
    assert caminho(resposta).endswith("/professor/turmas")


def test_cadastro_de_professor_invalido_retorna_400(cliente_anonimo):
    resposta = cliente_anonimo.post("/cadastro/professor",
                                    data={"apelido": "Ana", "email": "ana", "senha": SENHA})

    assert resposta.status_code == 400


# ---------------------------------------------------------------------------
# Login e logout
# ---------------------------------------------------------------------------

@pytest.mark.usefixtures("cliente_aluno")
def test_login_de_aluno_redireciona_para_o_painel(app):
    resposta = entrar(app.test_client(), "gabriel@escola.br")

    assert resposta.status_code == 302
    assert caminho(resposta).endswith("/painel/")


@pytest.mark.usefixtures("cliente_professor")
def test_login_de_professor_redireciona_para_turmas(app):
    resposta = entrar(app.test_client(), "prof.ana@escola.br")

    assert caminho(resposta).endswith("/professor/turmas")


@pytest.mark.usefixtures("cliente_aluno")
def test_login_ignora_maiusculas_no_email(app):
    assert entrar(app.test_client(), "Gabriel@Escola.BR").status_code == 302


@pytest.mark.usefixtures("cliente_aluno")
def test_login_com_senha_errada_retorna_401(app):
    resposta = entrar(app.test_client(), "gabriel@escola.br", senha="senha-errada")

    assert resposta.status_code == 401
    assert "E-mail ou senha incorretos." in resposta.get_data(as_text=True)


def test_login_com_email_inexistente_da_a_mesma_mensagem(cliente_anonimo):
    resposta = entrar(cliente_anonimo, "ninguem@escola.br")

    assert resposta.status_code == 401
    assert "E-mail ou senha incorretos." in resposta.get_data(as_text=True)


def errar_a_senha(cliente, email, vezes):
    for _ in range(vezes):
        entrar(cliente, email, senha="senha-errada")


@pytest.mark.usefixtures("cliente_aluno")
def test_login_bloqueia_o_email_depois_de_5_senhas_erradas(app):
    cliente = app.test_client()
    errar_a_senha(cliente, "gabriel@escola.br", 5)

    resposta = entrar(cliente, "gabriel@escola.br")  # agora com a senha certa

    assert resposta.status_code == 429
    assert "Muitas tentativas para este e-mail" in resposta.get_data(as_text=True)
    assert cliente.get("/painel/").status_code == 302  # continua sem login


@pytest.mark.usefixtures("cliente_aluno")
def test_bloqueio_vale_para_o_email_em_outra_caixa(app):
    cliente = app.test_client()
    errar_a_senha(cliente, "gabriel@escola.br", 5)

    assert entrar(cliente, "GABRIEL@escola.br").status_code == 429


@pytest.mark.usefixtures("cliente_aluno")
def test_bloqueio_de_um_email_nao_afeta_outro(app, turma):
    cadastrar_aluno(app.test_client(), turma["codigo"], email="bia@escola.br", apelido="Bia")
    errar_a_senha(app.test_client(), "gabriel@escola.br", 5)

    assert entrar(app.test_client(), "bia@escola.br").status_code == 302


@pytest.mark.usefixtures("cliente_aluno")
def test_chutes_simultaneos_nao_furam_o_limite(monkeypatch, app):
    # 6 chutes chegam juntos: cada um dispara o próximo enquanto confere a senha (o hash
    # é lento), então nenhum terminou quando o 6º chega. O 6º, com a senha certa, não entra.
    original = auth_service.conferir_senha
    disparados = []
    sexto = {}

    def conferir_enquanto_chega_outro(senha_hash, senha):
        if len(disparados) < 5:
            disparados.append(True)
            if len(disparados) == 5:
                sexto["resposta"] = entrar(app.test_client(), "gabriel@escola.br")
            else:
                entrar(app.test_client(), "gabriel@escola.br", senha="senha-errada")
        return original(senha_hash, senha)

    monkeypatch.setattr(auth_service, "conferir_senha", conferir_enquanto_chega_outro)
    entrar(app.test_client(), "gabriel@escola.br", senha="senha-errada")

    assert sexto["resposta"].status_code == 429


@pytest.mark.usefixtures("cliente_aluno")
def test_login_certo_zera_as_falhas(app):
    cliente = app.test_client()
    errar_a_senha(cliente, "gabriel@escola.br", 4)
    entrar(cliente, "gabriel@escola.br")
    errar_a_senha(cliente, "gabriel@escola.br", 1)

    assert entrar(app.test_client(), "gabriel@escola.br").status_code == 302


@pytest.mark.usefixtures("cliente_aluno")
def test_login_com_hash_scrypt_antigo_entra_e_regrava_em_argon2id(app):
    # Conta de antes do Argon2id: o hash guardado é o scrypt padrão do Werkzeug.
    conn = conectar(app.config["DATABASE"])
    with conn:
        conn.execute("UPDATE usuarios SET senha_hash = ? WHERE email = ?",
                     (generate_password_hash(SENHA, method="scrypt"), "gabriel@escola.br"))

    resposta = entrar(app.test_client(), "gabriel@escola.br")

    assert resposta.status_code == 302
    usuario = UsuarioRepository(conn).buscar_por_email("gabriel@escola.br")
    conn.close()
    assert usuario["senha_hash"].startswith("$argon2id$")


def test_login_vazio_retorna_400(cliente_anonimo):
    assert cliente_anonimo.post("/login", data={"email": "", "senha": ""}).status_code == 400


def test_logout_redireciona_para_o_login(cliente_aluno):
    resposta = cliente_aluno.post("/logout")

    assert caminho(resposta).endswith("/login")


def test_depois_do_logout_a_lista_exige_login(cliente_aluno):
    cliente_aluno.post("/logout")

    assert caminho(cliente_aluno.get("/lancamentos/")).endswith("/login")


def test_logout_por_get_nao_e_permitido(cliente_aluno):
    assert cliente_aluno.get("/logout").status_code == 405


# ---------------------------------------------------------------------------
# Acesso por perfil (RNF04, HU5 "acesso indevido")
# ---------------------------------------------------------------------------

def test_visitante_sem_login_e_mandado_para_o_login(cliente_anonimo):
    resposta = cliente_anonimo.get("/lancamentos/")

    assert resposta.status_code == 302
    assert caminho(resposta).endswith("/login")


def test_visitante_sem_login_nao_ve_o_formulario_de_novo_lancamento(cliente_anonimo):
    assert cliente_anonimo.get("/lancamentos/novo").status_code == 302


def test_aluno_nao_acessa_o_painel_do_professor(cliente_aluno):
    assert cliente_aluno.get("/professor/turmas").status_code == 403


def test_aluno_nao_cria_turma(cliente_aluno):
    assert cliente_aluno.post("/professor/turmas", data={"nome": "Turma falsa"}).status_code == 403


def test_professor_nao_acessa_os_lancamentos(cliente_professor):
    assert cliente_professor.get("/lancamentos/").status_code == 403
