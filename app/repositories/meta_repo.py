"""SQL de metas e aportes: único lugar com SQL destas entidades."""
import sqlite3

from app.repositories.conversao import linha_para_dict

# "Concluída" não fica em coluna: é calculada (guardado >= alvo), como o total de XP.
# O aporte é um valor separado e não entra no saldo dos lançamentos (decisão do grupo).
SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS metas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id            INTEGER NOT NULL,
    nome                TEXT    NOT NULL CHECK (length(trim(nome)) BETWEEN 1 AND 60),
    valor_alvo_centavos INTEGER NOT NULL
                        CHECK (typeof(valor_alvo_centavos) = 'integer' AND valor_alvo_centavos > 0),
    prazo               TEXT    CHECK (prazo IS NULL OR date(prazo) IS prazo),  -- 'AAAA-MM-DD'
    chave_idempotencia  TEXT    NOT NULL,  -- gerada no formulário; evita duplicar no reenvio
    criada_em           TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (aluno_id, chave_idempotencia)
);
CREATE INDEX IF NOT EXISTS ix_metas_aluno ON metas (aluno_id);

CREATE TABLE IF NOT EXISTS aportes_meta (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    meta_id             INTEGER NOT NULL REFERENCES metas (id),
    valor_centavos      INTEGER NOT NULL
                        CHECK (typeof(valor_centavos) = 'integer' AND valor_centavos > 0),
    chave_idempotencia  TEXT    NOT NULL,
    criado_em           TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (meta_id, chave_idempotencia)
);
"""

# Meta com o total já guardado nos aportes.
SQL_METAS_COM_GUARDADO = """
SELECT m.*, COALESCE(SUM(a.valor_centavos), 0) AS guardado_centavos
FROM metas m
LEFT JOIN aportes_meta a ON a.meta_id = m.id
WHERE m.aluno_id = ? {filtro}
GROUP BY m.id
ORDER BY m.id DESC
"""


class MetaRepository:
    """Metas e aportes. Toda operação é restrita ao aluno dono da meta.

    O repositório NÃO faz commit: quem chama decide a transação com `with conn:`.
    """

    def __init__(self, conn: sqlite3.Connection):
        """Cria o repositório sobre uma conexão já aberta (com `row_factory = sqlite3.Row`)."""
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        """Cria as tabelas `metas` e `aportes_meta`, se ainda não existirem."""
        conn.executescript(SQL_CRIAR_TABELA)

    def criar(self, aluno_id, nome, valor_alvo_centavos, prazo, chave_idempotencia) -> dict:
        """Insere uma meta, ou devolve a já existente se a chave se repetir. Não faz commit.

        Args:
            aluno_id: id do aluno dono da meta.
            nome: nome da meta (1 a 60 caracteres).
            valor_alvo_centavos: valor-alvo inteiro maior que zero, em centavos.
            prazo: "AAAA-MM-DD" ou None.
            chave_idempotencia: identificador único do envio, por aluno.

        Returns:
            dict: a meta gravada (nova ou a que já existia), com todas as colunas da tabela.

        Raises:
            sqlite3.IntegrityError: se algum valor violar as regras da tabela.
        """
        self.conn.execute(
            """
            INSERT INTO metas (aluno_id, nome, valor_alvo_centavos, prazo, chave_idempotencia)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (aluno_id, chave_idempotencia) DO NOTHING
            """,
            (aluno_id, nome, valor_alvo_centavos, prazo, chave_idempotencia),
        )
        linha = self.conn.execute(
            "SELECT * FROM metas WHERE aluno_id = ? AND chave_idempotencia = ?",
            (aluno_id, chave_idempotencia),
        ).fetchone()
        return linha_para_dict(linha)

    def listar(self, aluno_id) -> list[dict]:
        """Metas do aluno, da mais recente para a mais antiga, com `guardado_centavos`.

        Returns:
            list[dict]: as colunas de `metas` mais `guardado_centavos` (soma dos aportes, 0 sem aportes).
        """
        linhas = self.conn.execute(SQL_METAS_COM_GUARDADO.format(filtro=""), (aluno_id,)).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar(self, aluno_id, meta_id) -> dict | None:
        """Uma meta do aluno com `guardado_centavos`, ou None se não existir ou for de outro aluno."""
        linha = self.conn.execute(
            SQL_METAS_COM_GUARDADO.format(filtro="AND m.id = ?"), (aluno_id, meta_id)
        ).fetchone()
        return linha_para_dict(linha)

    def aportar(self, aluno_id, meta_id, valor_centavos, chave_idempotencia) -> bool:
        """Registra um aporte numa meta do aluno. Não faz commit.

        O INSERT só acontece se a meta for do aluno; o reenvio da mesma
        `chave_idempotencia` não grava de novo.

        Returns:
            bool: True se gravou agora; False se a chave já tinha sido usada
            ou a meta não é do aluno.

        Raises:
            sqlite3.IntegrityError: se o valor violar as regras da tabela.
        """
        cursor = self.conn.execute(
            """
            INSERT INTO aportes_meta (meta_id, valor_centavos, chave_idempotencia)
            SELECT id, ?, ? FROM metas WHERE id = ? AND aluno_id = ?
            ON CONFLICT (meta_id, chave_idempotencia) DO NOTHING
            """,
            (valor_centavos, chave_idempotencia, meta_id, aluno_id),
        )
        return cursor.rowcount == 1
