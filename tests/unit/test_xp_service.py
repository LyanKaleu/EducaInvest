"""Testes de teto diário e nível (HU3, RN-11 e RN-12). Só o service."""
from datetime import date

import pytest

from app.services import xp_service

# ---------------------------------------------------------------------------
# XP do lançamento com teto diário (RN-11): 10 por registro, até 50 por dia
# ---------------------------------------------------------------------------


def test_lancamento_abaixo_do_teto_vale_10_xp():
    assert xp_service.xp_do_lancamento(ganho_hoje=0) == 10


def test_lancamento_com_teto_atingido_nao_vale_xp():
    assert xp_service.xp_do_lancamento(ganho_hoje=50) == 0


def test_lancamento_perto_do_teto_vale_so_o_que_falta():
    assert xp_service.xp_do_lancamento(ganho_hoje=45) == 5


def test_lancamento_nunca_vale_xp_negativo():
    # Se o teto baixar um dia, quem já passou dele não perde nem "deve" XP (RN-12).
    assert xp_service.xp_do_lancamento(ganho_hoje=80) == 0


# ---------------------------------------------------------------------------
# Nível calculado pelo XP acumulado (RN-12)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("xp_total", "esperado"), [
    (0, (1, "Iniciante")),
    (99, (1, "Iniciante")),
    (100, (2, "Aprendiz")),
    (299, (2, "Aprendiz")),
    (300, (3, "Organizado")),
    (5000, (3, "Organizado")),
])
def test_nivel_pelo_xp_acumulado(xp_total, esperado):
    nivel = xp_service.nivel(xp_total)

    assert (nivel["nivel"], nivel["nome"]) == esperado


def test_nivel_informa_quanto_falta_para_o_proximo():
    assert xp_service.nivel(40)["falta"] == 60


def test_ultimo_nivel_nao_tem_proximo():
    assert xp_service.nivel(300)["falta"] is None


# ---------------------------------------------------------------------------
# Sequência de dias (RN-13): dias seguidos com XP; hoje em aberto não zera
# ---------------------------------------------------------------------------

HOJE = date(2026, 11, 10)


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (set(), 0),                                                  # nunca teve atividade
        ({10}, 1),                                                   # só hoje
        ({8, 9, 10}, 3),                                             # três seguidos até hoje
        ({8, 9}, 2),                                                 # hoje ainda não acabou: não zera
        ({7, 8}, 0),                                                 # 09 em branco zera
        ({6, 8, 9, 10}, 3),                                          # lacuna antiga não conta
    ],
)
def test_sequencia_conta_dias_seguidos_ate_hoje(dias, esperado):
    dias_ativos = {date(2026, 11, dia) for dia in dias}

    assert xp_service.sequencia(dias_ativos, HOJE) == esperado
