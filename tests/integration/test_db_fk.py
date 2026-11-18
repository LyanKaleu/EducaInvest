"""O banco impõe as foreign keys declaradas: a conexão liga PRAGMA
foreign_keys.

Sem o PRAGMA, o SQLite aceita filho órfão (o REFERENCES vira decoração) e o
ON DELETE CASCADE de `matriculas` não dispara. Este teste falha se a linha do
PRAGMA sumir de app.db.conectar (prova de revert).
"""

import sqlite3

import pytest

from app.db import conectar


def test_conexao_recusa_turma_com_professor_inexistente() -> None:
    # professor_id 999 não existe em usuarios; os demais campos passam nos
    # CHECK. Com a FK imposta, o INSERT do filho órfão levanta IntegrityError.
    conn = conectar(":memory:")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO turmas (professor_id, nome, codigo_acesso) "
                "VALUES (999, 'Turma X', 'AAAAAA')"
            )
    finally:
        conn.close()
