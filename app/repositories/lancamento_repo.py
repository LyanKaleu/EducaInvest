"""SQL de lançamentos (entradas e gastos): único lugar com SQL desta entidade."""
import sqlite3

from app.repositories.conversao import linha_para_dict

# Colunas que podem ser alteradas em atualizar(). Nomes de coluna não podem ir
# como parâmetro "?", então só aceitamos nomes desta lista fixa.
CAMPOS_EDITAVEIS = ("tipo", "categoria", "valor_centavos", "data_lancamento", "descricao")

SQL_CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS lancamentos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id           INTEGER NOT NULL,
    tipo               TEXT    NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    categoria          TEXT    NOT NULL CHECK (length(trim(categoria)) > 0),
    valor_centavos     INTEGER NOT NULL
                       CHECK (typeof(valor_centavos) = 'integer' AND valor_centavos > 0),
    data_lancamento    TEXT    NOT NULL
                       CHECK (date(data_lancamento) IS data_lancamento),  -- 'AAAA-MM-DD' válida
    descricao          TEXT    CHECK (descricao IS NULL OR length(descricao) <= 140),
    chave_idempotencia TEXT    NOT NULL,  -- gerada no formulário; evita duplicar no reenvio
    criado_em          TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (aluno_id, chave_idempotencia)
);
CREATE INDEX IF NOT EXISTS ix_lancamentos_aluno_data
    ON lancamentos (aluno_id, data_lancamento DESC);
"""


def _escapar_like(texto):
    """Faz '%' e '_' digitados pelo usuário serem procurados literalmente no LIKE."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class LancamentoRepository:
    """CRUD de lançamentos. Toda operação é restrita ao aluno dono do registro.

    O repositório NÃO faz commit: quem chama decide a transação com `with conn:`.
    Assim, no futuro, o lançamento e o XP podem ser gravados juntos (spec, HU3).
    """

    def __init__(self, conn: sqlite3.Connection):
        """Cria o repositório sobre uma conexão já aberta.

        Args:
            conn: conexão SQLite com `row_factory = sqlite3.Row` (como a que
                `app.db.conectar` devolve).
        """
        self.conn = conn

    @staticmethod
    def criar_tabela(conn: sqlite3.Connection) -> None:
        """Cria a tabela `lancamentos` e seu índice, se ainda não existirem.

        Args:
            conn: conexão SQLite onde a tabela será criada.

        Raises:
            sqlite3.Error: se o SQLite não conseguir executar o script.
        """
        conn.executescript(SQL_CRIAR_TABELA)

    def criar(self, aluno_id, tipo, categoria, valor_centavos, data_lancamento,
              chave_idempotencia, descricao=None) -> dict:
        """Insere um lançamento, ou devolve o já existente se a chave se repetir.

        Se o mesmo aluno enviar de novo a mesma `chave_idempotencia` (por
        exemplo, num reenvio depois de uma falha de rede), nada é inserido e
        o registro original é devolvido. Não faz commit.

        Args:
            aluno_id: id do aluno dono do lançamento.
            tipo: "ENTRADA" ou "SAIDA".
            categoria: nome da categoria (não pode ser vazio).
            valor_centavos: valor inteiro maior que zero, em centavos.
            data_lancamento: data no formato "AAAA-MM-DD".
            chave_idempotencia: identificador único do envio, por aluno.
            descricao: texto opcional de até 140 caracteres.

        Returns:
            dict: o lançamento gravado (novo ou o que já existia), com todas
            as colunas da tabela.

        Raises:
            sqlite3.IntegrityError: se algum valor violar as regras da tabela
                (tipo, valor, data, categoria ou descrição inválidos).
        """
        self.conn.execute(
            """
            INSERT INTO lancamentos
                (aluno_id, tipo, categoria, valor_centavos, data_lancamento,
                 descricao, chave_idempotencia)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (aluno_id, chave_idempotencia) DO NOTHING
            """,
            (aluno_id, tipo, categoria, valor_centavos, data_lancamento,
             descricao, chave_idempotencia),
        )
        linha = self.conn.execute(
            "SELECT * FROM lancamentos WHERE aluno_id = ? AND chave_idempotencia = ?",
            (aluno_id, chave_idempotencia),
        ).fetchone()
        return linha_para_dict(linha)

    def listar(self, aluno_id, busca=None) -> list[dict]:
        """Lista os lançamentos de um aluno, do mais recente para o mais antigo.

        Args:
            aluno_id: id do aluno.
            busca: texto opcional procurado na descrição ou na categoria.
                `%` e `_` digitados são procurados literalmente.

        Returns:
            list[dict]: os lançamentos encontrados (lista vazia se não houver
            nenhum), ordenados por data e depois por id, ambos decrescentes.
        """
        # Sem busca, o padrão vira '%%', que casa com qualquer categoria (sempre preenchida).
        padrao = "%" + _escapar_like((busca or "").strip()) + "%"
        linhas = self.conn.execute(
            r"""
            SELECT * FROM lancamentos
            WHERE aluno_id = ?
              AND (descricao LIKE ? ESCAPE '\' OR categoria LIKE ? ESCAPE '\')
            ORDER BY data_lancamento DESC, id DESC
            """,
            (aluno_id, padrao, padrao),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar(self, aluno_id, lancamento_id) -> dict | None:
        """Busca um lançamento pelo id, só entre os do aluno informado.

        Args:
            aluno_id: id do aluno dono do lançamento.
            lancamento_id: id do lançamento.

        Returns:
            dict | None: o lançamento, ou None se ele não existir ou for de
            outro aluno.
        """
        linha = self.conn.execute(
            "SELECT * FROM lancamentos WHERE aluno_id = ? AND id = ?",
            (aluno_id, lancamento_id),
        ).fetchone()
        return linha_para_dict(linha)

    def atualizar(self, aluno_id, lancamento_id, campos: dict) -> bool:
        """Altera colunas de um lançamento do aluno. Não faz commit.

        Args:
            aluno_id: id do aluno dono do lançamento.
            lancamento_id: id do lançamento.
            campos: {coluna: novo_valor}, só com colunas de `CAMPOS_EDITAVEIS`
                (tipo, categoria, valor_centavos, data_lancamento, descricao).

        Returns:
            bool: True se o lançamento foi alterado; False se ele não existe
            ou é de outro aluno.

        Raises:
            ValueError: se `campos` estiver vazio ou tiver uma coluna fora de
                `CAMPOS_EDITAVEIS`.
            sqlite3.IntegrityError: se um novo valor violar as regras da tabela.
        """
        desconhecidos = set(campos) - set(CAMPOS_EDITAVEIS)
        if desconhecidos:
            raise ValueError(f"Campos não editáveis: {sorted(desconhecidos)}")
        if not campos:
            raise ValueError("Informe ao menos um campo para atualizar.")
        # Os nomes vêm da lista fixa acima; os valores vão sempre por "?".
        atribuicoes = ", ".join(f"{nome} = ?" for nome in campos)
        cursor = self.conn.execute(
            f"UPDATE lancamentos SET {atribuicoes} WHERE aluno_id = ? AND id = ?",
            (*campos.values(), aluno_id, lancamento_id),
        )
        return cursor.rowcount == 1

    def excluir(self, aluno_id, lancamento_id) -> bool:
        """Apaga um lançamento do aluno. Não faz commit.

        Args:
            aluno_id: id do aluno dono do lançamento.
            lancamento_id: id do lançamento.

        Returns:
            bool: True se o lançamento foi apagado; False se ele não existe
            ou é de outro aluno.
        """
        cursor = self.conn.execute(
            "DELETE FROM lancamentos WHERE aluno_id = ? AND id = ?",
            (aluno_id, lancamento_id),
        )
        return cursor.rowcount == 1
