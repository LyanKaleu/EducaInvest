"""Garantias do banco na tabela de turmas, sem passar pela rota."""
import sqlite3
from collections.abc import Iterator

import pytest

from app.db import conectar
from app.repositories.turma_repo import TurmaRepository
from app.repositories.usuario_repo import UsuarioRepository


@pytest.fixture
def repo() -> Iterator[TurmaRepository]:
    conn = conectar(":memory:")
    # Com as FKs ligadas (app.db), turmas.professor_id precisa de um usuário real.
    # Dois professores pelo AUTOINCREMENT viram os ids 1 e 2 usados abaixo.
    usuarios = UsuarioRepository(conn)
    usuarios.criar("PROFESSOR", "Prof 1", "prof1@escola.br", "x")
    usuarios.criar("PROFESSOR", "Prof 2", "prof2@escola.br", "x")
    yield TurmaRepository(conn)
    conn.close()


def test_banco_recusa_turma_do_mesmo_professor_com_nome_em_outra_caixa(repo: TurmaRepository) -> None:
    # Mesmo que a checagem da rota falhe (corrida, clique duplo), o banco barra.
    repo.criar(professor_id=1, nome="Turma 2", codigo_acesso="AAAAAA")

    with pytest.raises(sqlite3.IntegrityError):
        repo.criar(professor_id=1, nome="TURMA 2", codigo_acesso="BBBBBB")


def test_banco_aceita_mesmo_nome_para_professores_diferentes(repo: TurmaRepository) -> None:
    repo.criar(professor_id=1, nome="Turma 2", codigo_acesso="AAAAAA")

    assert repo.criar(professor_id=2, nome="turma 2", codigo_acesso="BBBBBB")
