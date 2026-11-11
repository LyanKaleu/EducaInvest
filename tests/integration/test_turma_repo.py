"""Garantias do banco na tabela de turmas, sem passar pela rota."""
import sqlite3

import pytest

from app.db import conectar
from app.repositories.turma_repo import TurmaRepository


@pytest.fixture
def repo():
    conn = conectar(":memory:")
    yield TurmaRepository(conn)
    conn.close()


def test_banco_recusa_turma_do_mesmo_professor_com_nome_em_outra_caixa(repo):
    # Mesmo que a checagem da rota falhe (corrida, clique duplo), o banco barra.
    repo.criar(professor_id=1, nome="Turma 2", codigo_acesso="AAAAAA")

    with pytest.raises(sqlite3.IntegrityError):
        repo.criar(professor_id=1, nome="TURMA 2", codigo_acesso="BBBBBB")


def test_banco_aceita_mesmo_nome_para_professores_diferentes(repo):
    repo.criar(professor_id=1, nome="Turma 2", codigo_acesso="AAAAAA")

    assert repo.criar(professor_id=2, nome="turma 2", codigo_acesso="BBBBBB")
