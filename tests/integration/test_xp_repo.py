"""Garantias do banco no XP e nas missões concluídas (INVARIANTES N6), sem passar pela rota."""
import sqlite3
from datetime import date

import pytest

from app.db import conectar
from app.repositories.missao_repo import MissaoRepository
from app.repositories.xp_repo import XpRepository

DIA = "2026-11-04"


@pytest.fixture
def conn():
    conexao = conectar(":memory:")
    yield conexao
    conexao.close()


@pytest.fixture
def repo(conn):
    return XpRepository(conn)


def test_mesma_origem_pontua_uma_vez_so(repo):
    assert repo.creditar(aluno_id=1, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref=DIA)
    assert not repo.creditar(aluno_id=1, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref=DIA)

    assert repo.total(1) == 30


def test_mesma_origem_pontua_para_alunos_diferentes(repo):
    repo.creditar(aluno_id=1, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref=DIA)
    repo.creditar(aluno_id=2, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref=DIA)

    assert (repo.total(1), repo.total(2)) == (30, 30)


def test_pontos_no_dia_somam_so_a_origem_e_o_dia_pedidos(repo):
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="1", pontos=10, dia_ref=DIA)
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="2", pontos=10, dia_ref=DIA)
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="3", pontos=10, dia_ref="2026-11-03")
    repo.creditar(aluno_id=1, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref=DIA)

    assert repo.pontos_no_dia(1, "LANCAMENTO", DIA) == 20


def test_banco_recusa_pontos_zero_ou_negativos(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="1", pontos=-10, dia_ref=DIA)


def test_banco_recusa_apagar_xp(repo, conn):
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="1", pontos=10, dia_ref=DIA)

    with pytest.raises(sqlite3.IntegrityError, match="XP nunca diminui"):
        conn.execute("DELETE FROM xp_eventos")


def test_banco_recusa_alterar_xp(repo, conn):
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="1", pontos=10, dia_ref=DIA)

    with pytest.raises(sqlite3.IntegrityError, match="XP nunca diminui"):
        conn.execute("UPDATE xp_eventos SET pontos = 1")


def test_missao_conclui_uma_vez_so_por_aluno(conn):
    # Garantia própria da PK de missoes_concluidas, sem depender do service nem do XP.
    repo = MissaoRepository(conn)

    assert repo.concluir(aluno_id=1, missao_codigo="REG_3_GASTOS")
    assert not repo.concluir(aluno_id=1, missao_codigo="REG_3_GASTOS")
    assert repo.concluir(aluno_id=2, missao_codigo="REG_3_GASTOS")
    assert repo.concluidas(1) == {"REG_3_GASTOS"}


def test_dias_ativos_sao_distintos_e_so_do_aluno(repo):
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="1", pontos=10, dia_ref="2026-11-09")
    repo.creditar(aluno_id=1, origem="LANCAMENTO", origem_id="2", pontos=10, dia_ref="2026-11-10")
    repo.creditar(aluno_id=1, origem="MISSAO", origem_id="REG_3_GASTOS", pontos=30, dia_ref="2026-11-10")
    repo.creditar(aluno_id=2, origem="LANCAMENTO", origem_id="3", pontos=10, dia_ref="2026-11-08")

    assert repo.dias_ativos(1) == {date(2026, 11, 9), date(2026, 11, 10)}
