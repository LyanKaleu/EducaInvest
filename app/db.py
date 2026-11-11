"""Conexão com o SQLite: abre o banco, cria as tabelas e entrega uma conexão por requisição."""
import sqlite3

from flask import current_app, g

from app.repositories.lancamento_repo import LancamentoRepository
from app.repositories.meta_repo import MetaRepository
from app.repositories.missao_repo import MissaoRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.turma_repo import TurmaRepository
from app.repositories.usuario_repo import UsuarioRepository
from app.repositories.xp_repo import XpRepository


def conectar(caminho: str) -> sqlite3.Connection:
    """Abre (ou cria) o banco em `caminho` e cria as tabelas que faltarem.

    Use ":memory:" nos testes para um banco temporário em memória.
    """
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row  # linhas acessíveis por nome: linha["valor_centavos"]
    UsuarioRepository.criar_tabela(conn)
    TurmaRepository.criar_tabela(conn)
    LancamentoRepository.criar_tabela(conn)
    XpRepository.criar_tabela(conn)
    MissaoRepository.criar_tabela(conn)
    MetaRepository.criar_tabela(conn)
    QuizRepository.criar_tabela(conn)
    return conn


def obter_conexao() -> sqlite3.Connection:
    """Conexão da requisição atual: abre na primeira chamada e reaproveita nas seguintes."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def fechar_conexao(_erro=None) -> None:
    """Fecha a conexão ao fim da requisição. O que não teve commit é descartado."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app) -> None:
    """Liga o fechamento automático da conexão ao ciclo de cada requisição."""
    app.teardown_appcontext(fechar_conexao)
