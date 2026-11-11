"""Fixtures compartilhadas: app de teste, banco SQLite temporário e cliente HTTP."""
import re
import uuid
from datetime import date

import pytest

from app import create_app
from app.services import auth_service

# Data fixa para os testes do validador não dependerem do dia em que rodam.
HOJE = date(2026, 11, 4)


@pytest.fixture(autouse=True)
def hash_de_senha_rapido(monkeypatch):
    """Troca o scrypt (lento de propósito) por PBKDF2 com 1 iteração, só nos testes."""
    monkeypatch.setattr(auth_service, "METODO_HASH", "pbkdf2:sha256:1")


@pytest.fixture
def form_valido():
    """Formulário de um gasto válido, como o navegador envia."""
    return {
        "tipo": "saida",
        "categoria": "Alimentação",
        "valor": "25,00",
        "data": "2026-11-01",
        "descricao": "lanche",
        "chave_idempotencia": str(uuid.uuid4()),
    }


def _criar_app(tmp_path, **config):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "chave-de-teste",
        "DATABASE": str(tmp_path / "teste.db"),
        **config,
    })


@pytest.fixture
def app(tmp_path):
    """App de teste com banco novo em uma pasta temporária a cada teste."""
    return _criar_app(tmp_path)


@pytest.fixture
def cliente(cliente_aluno):
    """Cliente padrão dos testes de lançamentos: um aluno logado."""
    return cliente_aluno


@pytest.fixture
def cliente_outro_aluno(app, turma, cliente_aluno):
    """Segundo aluno, na mesma turma e no MESMO banco do primeiro."""
    outro = app.test_client()
    cadastrar_aluno(outro, turma["codigo"], email="beatriz@escola.br", apelido="Beatriz")
    return outro


@pytest.fixture
def cliente_sem_login(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Login + turma (RF01, RF02): professor, turma e aluno criados pelas rotas HTTP.
# ---------------------------------------------------------------------------

SENHA = "senha-segura-123"


def cadastrar_professor(cliente, email="prof.ana@escola.br", apelido="Prof. Ana"):
    return cliente.post("/cadastro/professor",
                        data={"apelido": apelido, "email": email, "senha": SENHA})


def criar_turma(cliente_professor, nome="2º A"):
    return cliente_professor.post("/professor/turmas", data={"nome": nome})


def cadastrar_aluno(cliente, codigo, email="gabriel@escola.br", apelido="Gabriel", **extra):
    dados = {"apelido": apelido, "email": email, "senha": SENHA,
             "codigo_turma": codigo, "consentimento": "sim", **extra}
    return cliente.post("/cadastro", data=dados)


def entrar(cliente, email, senha=SENHA):
    return cliente.post("/login", data={"email": email, "senha": senha})


@pytest.fixture
def cliente_anonimo(app):
    return app.test_client()


@pytest.fixture
def cliente_professor(app):
    cliente = app.test_client()
    cadastrar_professor(cliente)
    return cliente


@pytest.fixture
def turma(cliente_professor):
    """Cria a turma "2º A" e devolve {"id": ..., "codigo": ...} lidos da página de turmas."""
    criar_turma(cliente_professor)
    html = cliente_professor.get("/professor/turmas").get_data(as_text=True)
    codigo = re.search(r'<code class="codigo-turma">([A-Z0-9]{6})</code>', html)
    turma_id = re.search(r'href="/professor/turmas/(\d+)"', html)
    assert codigo and turma_id, "a página de turmas deve mostrar o código e o link da turma"
    return {"id": int(turma_id.group(1)), "codigo": codigo.group(1)}


@pytest.fixture
def cliente_aluno(app, turma):
    cliente = app.test_client()
    cadastrar_aluno(cliente, turma["codigo"])
    return cliente


@pytest.fixture
def lancamento_existente(cliente, form_valido):
    """Gasto de R$ 25,00 do aluno logado, criado pela rota. Devolve {"id": ...}."""
    cliente.post("/lancamentos/novo", data=form_valido)
    html = cliente.get("/lancamentos/").get_data(as_text=True)
    encontrado = re.search(r'href="/lancamentos/(\d+)/editar"', html)
    assert encontrado, "o lançamento criado deve aparecer na lista"
    return {"id": int(encontrado.group(1))}
