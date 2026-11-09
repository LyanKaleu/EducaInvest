"""Testes de teto diário e nível (HU3, RN-11 e RN-12). Só o service."""
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
