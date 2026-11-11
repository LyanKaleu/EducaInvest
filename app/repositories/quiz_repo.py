"""SQL das respostas de quiz de cada aluno. O banco de perguntas fica em quiz_service.PERGUNTAS."""
import sqlite3

# A PK garante uma única resposta por pergunta (RN-16: a primeira vale), inclusive no
# clique duplo: o segundo INSERT cai no ON CONFLICT e não muda nada.
SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS quiz_respostas (
    aluno_id         INTEGER NOT NULL,
    pergunta_codigo  TEXT    NOT NULL CHECK (length(pergunta_codigo) > 0),
    alternativa      TEXT    NOT NULL CHECK (alternativa IN ('a', 'b', 'c', 'd')),
    correta          INTEGER NOT NULL CHECK (correta IN (0, 1)),
    respondida_em    TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (aluno_id, pergunta_codigo)
);
"""


class QuizRepository:
    """Respostas de quiz por aluno. NÃO faz commit: quem chama decide a transação."""

    def __init__(self, conn: sqlite3.Connection):
        """Cria o repositório sobre uma conexão já aberta."""
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        """Cria a tabela `quiz_respostas`, se ainda não existir."""
        conn.executescript(SQL_CRIAR_TABELA)

    def responder(self, aluno_id, pergunta_codigo, alternativa, correta: bool) -> bool:
        """Grava a resposta do aluno, se ele ainda não respondeu essa pergunta. Não faz commit.

        Returns:
            bool: True se gravou agora; False se já havia resposta (a primeira vale).
        """
        cursor = self.conn.execute(
            """
            INSERT INTO quiz_respostas (aluno_id, pergunta_codigo, alternativa, correta)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (aluno_id, pergunta_codigo) DO NOTHING
            """,
            (aluno_id, pergunta_codigo, alternativa, int(correta)),
        )
        return cursor.rowcount == 1

    def resposta(self, aluno_id, pergunta_codigo) -> dict | None:
        """Resposta do aluno a uma pergunta: {"alternativa", "correta"}, ou None se não respondeu."""
        linha = self.conn.execute(
            """
            SELECT alternativa, correta FROM quiz_respostas
            WHERE aluno_id = ? AND pergunta_codigo = ?
            """,
            (aluno_id, pergunta_codigo),
        ).fetchone()
        if linha is None:
            return None
        return {"alternativa": linha["alternativa"], "correta": bool(linha["correta"])}

    def acertos_por_pergunta(self, aluno_id) -> dict[str, bool]:
        """{código: acertou} de todas as perguntas que o aluno já respondeu."""
        linhas = self.conn.execute(
            "SELECT pergunta_codigo, correta FROM quiz_respostas WHERE aluno_id = ?",
            (aluno_id,),
        ).fetchall()
        return {linha["pergunta_codigo"]: bool(linha["correta"]) for linha in linhas}
