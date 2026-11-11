"""SQL de usuários (alunos e professores)."""
import sqlite3

from app.repositories.conversao import linha_para_dict

SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    perfil            TEXT    NOT NULL CHECK (perfil IN ('ALUNO', 'PROFESSOR')),
    apelido           TEXT    NOT NULL CHECK (length(trim(apelido)) BETWEEN 2 AND 40),
    email             TEXT    NOT NULL UNIQUE COLLATE NOCASE CHECK (instr(email, '@') > 1),
    senha_hash        TEXT    NOT NULL,
    consentimento_em  TEXT,   -- quando o aluno marcou a autorização (RN-05)
    criado_em         TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


class UsuarioRepository:
    """Leitura e gravação de usuários. Não faz commit."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        conn.executescript(SQL_CRIAR_TABELA)

    def criar(self, perfil, apelido, email, senha_hash, consentimento_em=None) -> dict:
        cursor = self.conn.execute(
            """
            INSERT INTO usuarios (perfil, apelido, email, senha_hash, consentimento_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (perfil, apelido, email, senha_hash, consentimento_em),
        )
        return self.buscar_por_id(cursor.lastrowid)

    def buscar_por_id(self, usuario_id) -> dict | None:
        linha = self.conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return linha_para_dict(linha)

    def buscar_por_email(self, email) -> dict | None:
        linha = self.conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        return linha_para_dict(linha)
