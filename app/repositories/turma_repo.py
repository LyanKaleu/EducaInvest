"""SQL de turmas e matrículas."""
import sqlite3

from app.repositories.conversao import linha_para_dict

SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS turmas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id   INTEGER NOT NULL REFERENCES usuarios (id),
    nome           TEXT    NOT NULL CHECK (length(trim(nome)) BETWEEN 1 AND 60),
    codigo_acesso  TEXT    NOT NULL UNIQUE
                   CHECK (length(codigo_acesso) BETWEEN 6 AND 8 AND codigo_acesso = upper(codigo_acesso)),
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (professor_id, nome)
);

-- "Turma 2" e "TURMA 2" contam como o mesmo nome para o professor
CREATE UNIQUE INDEX IF NOT EXISTS ux_turmas_professor_nome
    ON turmas (professor_id, nome COLLATE NOCASE);

-- aluno_id como chave: cada aluno pertence a uma única turma no MVP
CREATE TABLE IF NOT EXISTS matriculas (
    aluno_id   INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    turma_id   INTEGER NOT NULL REFERENCES turmas (id),
    entrou_em  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_matriculas_turma ON matriculas (turma_id);
"""


class TurmaRepository:
    """Turmas do professor e alunos matriculados. Não faz commit."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        conn.executescript(SQL_CRIAR_TABELA)

    def criar(self, professor_id, nome, codigo_acesso) -> dict:
        cursor = self.conn.execute(
            "INSERT INTO turmas (professor_id, nome, codigo_acesso) VALUES (?, ?, ?)",
            (professor_id, nome, codigo_acesso),
        )
        return self.buscar_do_professor(professor_id, cursor.lastrowid)

    def listar_do_professor(self, professor_id) -> list[dict]:
        linhas = self.conn.execute(
            "SELECT * FROM turmas WHERE professor_id = ? ORDER BY nome",
            (professor_id,),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar_do_professor(self, professor_id, turma_id) -> dict | None:
        linha = self.conn.execute(
            "SELECT * FROM turmas WHERE professor_id = ? AND id = ?",
            (professor_id, turma_id),
        ).fetchone()
        return linha_para_dict(linha)

    def buscar_por_codigo(self, codigo_acesso) -> dict | None:
        linha = self.conn.execute(
            "SELECT * FROM turmas WHERE codigo_acesso = ?", (codigo_acesso,)
        ).fetchone()
        return linha_para_dict(linha)

    def existe_nome(self, professor_id, nome) -> bool:
        linha = self.conn.execute(
            "SELECT 1 FROM turmas WHERE professor_id = ? AND nome = ? COLLATE NOCASE",
            (professor_id, nome),
        ).fetchone()
        return linha is not None

    def matricular(self, aluno_id, turma_id) -> None:
        self.conn.execute(
            "INSERT INTO matriculas (aluno_id, turma_id) VALUES (?, ?)", (aluno_id, turma_id)
        )

    def listar_alunos(self, turma_id) -> list[dict]:
        """Só id e apelido: a tela do professor nunca recebe e-mail (RNF02)."""
        linhas = self.conn.execute(
            """
            SELECT u.id, u.apelido
            FROM matriculas m JOIN usuarios u ON u.id = m.aluno_id
            WHERE m.turma_id = ?
            ORDER BY u.apelido
            """,
            (turma_id,),
        ).fetchall()
        return [dict(linha) for linha in linhas]
