"""Garantias do banco nos aportes de meta, sem passar pela rota (auditoria, achado 7)."""
import pytest

from app.db import conectar
from app.repositories.meta_repo import MetaRepository

ALUNO = 1


@pytest.fixture
def repo():
    conn = conectar(":memory:")
    yield MetaRepository(conn)
    conn.close()


@pytest.fixture
def meta_de_100_reais(repo):
    return repo.criar(ALUNO, "Fone", 10000, None, "chave-meta")["id"]


def test_banco_recusa_aporte_que_passa_do_alvo(repo, meta_de_100_reais):
    # Dois aportes simultâneos passam pela checagem da rota com o mesmo "guardado";
    # o segundo chega aqui quando só faltam R$ 30,00.
    repo.aportar(ALUNO, meta_de_100_reais, 7000, "chave-1")

    assert repo.aportar(ALUNO, meta_de_100_reais, 5000, "chave-2") is False
    assert repo.buscar(ALUNO, meta_de_100_reais)["guardado_centavos"] == 7000


def test_banco_aceita_aporte_que_completa_o_alvo_exato(repo, meta_de_100_reais):
    repo.aportar(ALUNO, meta_de_100_reais, 7000, "chave-1")

    assert repo.aportar(ALUNO, meta_de_100_reais, 3000, "chave-2") is True
    assert repo.buscar(ALUNO, meta_de_100_reais)["guardado_centavos"] == 10000


def test_banco_recusa_aporte_em_meta_ja_concluida(repo, meta_de_100_reais):
    repo.aportar(ALUNO, meta_de_100_reais, 10000, "chave-1")

    assert repo.aportar(ALUNO, meta_de_100_reais, 1, "chave-2") is False
