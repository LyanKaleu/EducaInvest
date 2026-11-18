"""Testes de teto diário e nível (HU3, RN-11 e RN-12). Só o service."""

from datetime import date

import pytest

from app.services import xp_service

# ---------------------------------------------------------------------------
# XP do lançamento com teto diário (RN-11): 10 por registro, até 50 por dia
# ---------------------------------------------------------------------------


def test_lancamento_abaixo_do_teto_vale_10_xp() -> None:
    assert xp_service.xp_do_lancamento(ganho_hoje=0) == 10


def test_lancamento_com_teto_atingido_nao_vale_xp() -> None:
    assert xp_service.xp_do_lancamento(ganho_hoje=50) == 0


def test_lancamento_perto_do_teto_vale_so_o_que_falta() -> None:
    assert xp_service.xp_do_lancamento(ganho_hoje=45) == 5


def test_lancamento_nunca_vale_xp_negativo() -> None:
    # Se o teto baixar um dia, quem já passou dele não perde nem "deve" XP
    # (RN-12).
    assert xp_service.xp_do_lancamento(ganho_hoje=80) == 0


# ---------------------------------------------------------------------------
# Nível calculado pelo XP acumulado (RN-12)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("xp_total", "esperado"),
    [
        (0, (1, "Iniciante")),
        (99, (1, "Iniciante")),
        (100, (2, "Aprendiz")),
        (299, (2, "Aprendiz")),
        (300, (3, "Organizado")),
        (5000, (3, "Organizado")),
    ],
)
def test_nivel_pelo_xp_acumulado(
    xp_total: int, esperado: tuple[int, str]
) -> None:
    nivel = xp_service.nivel(xp_total)

    assert (nivel["nivel"], nivel["nome"]) == esperado


def test_nivel_informa_quanto_falta_para_o_proximo() -> None:
    assert xp_service.nivel(40)["falta"] == 60


def test_ultimo_nivel_nao_tem_proximo() -> None:
    assert xp_service.nivel(300)["falta"] is None


# ---------------------------------------------------------------------------
# Sequência de dias (RN-13): dias seguidos com XP; hoje em aberto não zera
# ---------------------------------------------------------------------------

HOJE = date(2026, 11, 10)


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (set(), 0),  # nunca teve atividade
        ({10}, 1),  # só hoje
        ({8, 9, 10}, 3),  # três seguidos até hoje
        ({8, 9}, 2),  # hoje ainda não acabou: não zera
        ({7, 8}, 0),  # 09 em branco zera
        ({6, 8, 9, 10}, 3),  # lacuna antiga não conta
    ],
)
def test_sequencia_conta_dias_seguidos_ate_hoje(
    dias: set[int], esperado: int
) -> None:
    dias_ativos = {date(2026, 11, dia) for dia in dias}

    assert xp_service.sequencia(dias_ativos, HOJE) == esperado


# ---------------------------------------------------------------------------
# Os últimos 7 dias da sequência (tela inicial): do mais antigo até hoje
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        (set(), [False] * 7),  # nunca teve atividade
        (
            {10},
            [False, False, False, False, False, False, True],
        ),  # hoje é o último
        (
            {4},
            [True, False, False, False, False, False, False],
        ),  # 04 é o primeiro da janela
        ({3, 11}, [False] * 7),  # antes da janela e depois de hoje não contam
        ({5, 8, 9}, [False, True, False, False, True, True, False]),
    ],
)
def test_ultimos_dias_marca_cada_dia_da_janela_ate_hoje(
    dias: set[int], esperado: list[bool]
) -> None:
    dias_ativos = {date(2026, 11, dia) for dia in dias}

    assert xp_service.ultimos_dias(dias_ativos, HOJE) == esperado


# ---------------------------------------------------------------------------
# Progresso dentro do nível (barra do cartão de nível)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("xp_total", "esperado"),
    [
        (0, 0),  # começo do Iniciante (0 a 100)
        (70, 70),  # 70 de 100
        (100, 0),  # acabou de virar Aprendiz (100 a 300)
        (250, 75),  # 150 de 200
        (299, 99),  # arredonda para baixo: só 100 no nível seguinte
        (300, 100),  # Organizado é o último: barra cheia
        (900, 100),
    ],
)
def test_percentual_mostra_o_progresso_dentro_do_nivel(
    xp_total: int, esperado: int
) -> None:
    assert xp_service.nivel(xp_total)["percentual"] == esperado
