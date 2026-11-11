"""SQL das missões concluídas por cada aluno. O catálogo fica em missao_service.MISSOES."""
import sqlite3

# A PK impede concluir (e pontuar) a mesma missão duas vezes (RN-10).
SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS missoes_concluidas (
    aluno_id       INTEGER NOT NULL,
    missao_codigo  TEXT    NOT NULL CHECK (length(missao_codigo) > 0),
    concluida_em   TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (aluno_id, missao_codigo)
);
"""


class MissaoRepository:
    """Conclusões de missão por aluno. NÃO faz commit: quem chama decide a transação."""

    def __init__(self, conn: sqlite3.Connection):
        """Cria o repositório sobre uma conexão já aberta."""
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        """Cria a tabela `missoes_concluidas`, se ainda não existir."""
        conn.executescript(SQL_CRIAR_TABELA)

    def concluir(self, aluno_id, missao_codigo) -> bool:
        """Marca a missão como concluída pelo aluno. Não faz commit.

        Returns:
            bool: True se concluiu agora; False se já estava concluída.
        """
        cursor = self.conn.execute(
            """
            INSERT INTO missoes_concluidas (aluno_id, missao_codigo) VALUES (?, ?)
            ON CONFLICT (aluno_id, missao_codigo) DO NOTHING
            """,
            (aluno_id, missao_codigo),
        )
        return cursor.rowcount == 1

    def contar_por_aluno(self, aluno_ids) -> dict[int, int]:
        """Quantas missões cada aluno concluiu, para o painel da turma (HU5).

        Returns:
            dict: `{aluno_id: int}`, só de quem concluiu alguma; `{}` se
            `aluno_ids` vier vazio.
        """
        aluno_ids = list(aluno_ids)
        if not aluno_ids:
            return {}
        marcadores = ", ".join("?" * len(aluno_ids))
        linhas = self.conn.execute(
            f"""
            SELECT aluno_id, COUNT(*) AS total FROM missoes_concluidas
            WHERE aluno_id IN ({marcadores}) GROUP BY aluno_id
            """,
            aluno_ids,
        ).fetchall()
        return {linha["aluno_id"]: linha["total"] for linha in linhas}

    def concluidas(self, aluno_id) -> set[str]:
        """Códigos das missões que o aluno já concluiu."""
        linhas = self.conn.execute(
            "SELECT missao_codigo FROM missoes_concluidas WHERE aluno_id = ?",
            (aluno_id,),
        ).fetchall()
        return {linha["missao_codigo"] for linha in linhas}
