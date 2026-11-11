"""SQL do livro-razão de XP: único lugar com SQL desta entidade (INVARIANTES N6)."""
import sqlite3
from datetime import date

# Livro-razão: o XP só entra por INSERT, e cada origem pontua uma vez por aluno.
# Total e nível são calculados, nunca guardados em coluna.
SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS xp_eventos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id   INTEGER NOT NULL,
    pontos     INTEGER NOT NULL CHECK (typeof(pontos) = 'integer' AND pontos > 0),
    origem     TEXT    NOT NULL CHECK (origem IN ('LANCAMENTO', 'MISSAO', 'QUIZ')),
    origem_id  TEXT    NOT NULL CHECK (length(origem_id) > 0),  -- id do lançamento, código da missão...
    dia_ref    TEXT    NOT NULL CHECK (date(dia_ref) IS dia_ref),  -- dia no fuso do Piauí (teto diário)
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (aluno_id, origem, origem_id)
);
CREATE INDEX IF NOT EXISTS ix_xp_eventos_aluno_dia ON xp_eventos (aluno_id, dia_ref);

-- O XP nunca diminui (RN-12): o próprio banco recusa alterar ou apagar um evento.
CREATE TRIGGER IF NOT EXISTS tr_xp_eventos_sem_update BEFORE UPDATE ON xp_eventos
BEGIN
    SELECT RAISE(ABORT, 'XP nunca diminui: xp_eventos só aceita INSERT');
END;
CREATE TRIGGER IF NOT EXISTS tr_xp_eventos_sem_delete BEFORE DELETE ON xp_eventos
BEGIN
    SELECT RAISE(ABORT, 'XP nunca diminui: xp_eventos só aceita INSERT');
END;
"""


class XpRepository:
    """Crédito e consulta de XP de cada aluno.

    O repositório NÃO faz commit: o crédito vai na mesma transação da ação que
    o gerou (spec, HU3 "falha parcial").
    """

    def __init__(self, conn: sqlite3.Connection):
        """Cria o repositório sobre uma conexão já aberta."""
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        """Cria a tabela `xp_eventos`, seu índice e os gatilhos, se ainda não existirem."""
        conn.executescript(SQL_CRIAR_TABELA)

    def creditar(self, aluno_id, origem, origem_id, pontos, dia_ref) -> bool:
        """Registra XP para o aluno, se essa origem ainda não pontuou. Não faz commit.

        Args:
            aluno_id: id do aluno.
            origem: "LANCAMENTO", "MISSAO" ou "QUIZ".
            origem_id: identificador da origem (id do lançamento, código da missão).
            pontos: XP inteiro maior que zero.
            dia_ref: dia do crédito no fuso do Piauí, "AAAA-MM-DD".

        Returns:
            bool: True se creditou; False se essa origem já tinha pontuado.

        Raises:
            sqlite3.IntegrityError: se algum valor violar as regras da tabela.
        """
        cursor = self.conn.execute(
            """
            INSERT INTO xp_eventos (aluno_id, origem, origem_id, pontos, dia_ref)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (aluno_id, origem, origem_id) DO NOTHING
            """,
            (aluno_id, origem, str(origem_id), pontos, dia_ref),
        )
        return cursor.rowcount == 1

    def pontos_no_dia(self, aluno_id, origem, dia_ref) -> int:
        """Soma do XP que o aluno ganhou com `origem` no dia `dia_ref` (para o teto diário)."""
        linha = self.conn.execute(
            """
            SELECT COALESCE(SUM(pontos), 0) FROM xp_eventos
            WHERE aluno_id = ? AND origem = ? AND dia_ref = ?
            """,
            (aluno_id, origem, dia_ref),
        ).fetchone()
        return linha[0]

    def total(self, aluno_id) -> int:
        """Soma de todo o XP do aluno (0 se ele ainda não ganhou nada)."""
        linha = self.conn.execute(
            "SELECT COALESCE(SUM(pontos), 0) FROM xp_eventos WHERE aluno_id = ?",
            (aluno_id,),
        ).fetchone()
        return linha[0]

    def resumo_por_aluno(self, aluno_ids) -> dict[int, dict]:
        """XP total e último dia com XP de cada aluno, para o painel da turma (HU5).

        Args:
            aluno_ids: ids dos alunos (ex.: os da turma).

        Returns:
            dict: `{aluno_id: {"xp": int, "ultimo_dia": date}}`, só de quem já
            ganhou XP; `{}` se `aluno_ids` vier vazio.
        """
        aluno_ids = list(aluno_ids)
        if not aluno_ids:
            return {}
        marcadores = ", ".join("?" * len(aluno_ids))
        linhas = self.conn.execute(
            f"""
            SELECT aluno_id, SUM(pontos) AS xp, MAX(dia_ref) AS ultimo_dia
            FROM xp_eventos WHERE aluno_id IN ({marcadores})
            GROUP BY aluno_id
            """,
            aluno_ids,
        ).fetchall()
        return {
            linha["aluno_id"]: {"xp": linha["xp"], "ultimo_dia": date.fromisoformat(linha["ultimo_dia"])}
            for linha in linhas
        }

    def dias_ativos(self, aluno_id) -> set[date]:
        """Dias (fuso do Piauí) em que o aluno ganhou algum XP, sem repetição (RN-13)."""
        linhas = self.conn.execute(
            "SELECT DISTINCT dia_ref FROM xp_eventos WHERE aluno_id = ?",
            (aluno_id,),
        ).fetchall()
        return {date.fromisoformat(linha[0]) for linha in linhas}
