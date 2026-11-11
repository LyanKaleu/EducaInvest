"""Testes de progresso, conclusão única e desbloqueio de missões (HU3). Só o service."""
from app.services import missao_service

PRIMEIRA = "REG_3_GASTOS"   # Registre 3 gastos (+30 XP)
SEGUNDA = "REG_7_LANCAMENTOS"  # Registre 7 lançamentos, entradas ou saídas (+50 XP); exige a primeira


def contagens(gastos=0, entradas=0):
    return {"SAIDA": gastos, "ENTRADA": entradas}


def por_codigo(situacao):
    return {missao["codigo"]: missao for missao in situacao}


def codigos(missoes):
    return [missao["codigo"] for missao in missoes]


# ---------------------------------------------------------------------------
# Situação mostrada na tela
# ---------------------------------------------------------------------------

def test_dois_gastos_mostram_2_de_3_na_primeira_missao():
    primeira = por_codigo(missao_service.situacao(contagens(gastos=2), set()))[PRIMEIRA]

    assert (primeira["atual"], primeira["alvo"], primeira["status"]) == (2, 3, "ATIVA")


def test_entradas_nao_contam_para_a_missao_de_gastos():
    primeira = por_codigo(missao_service.situacao(contagens(entradas=5), set()))[PRIMEIRA]

    assert primeira["atual"] == 0


def test_segunda_missao_fica_bloqueada_ate_concluir_a_primeira():
    segunda = por_codigo(missao_service.situacao(contagens(gastos=2), set()))[SEGUNDA]

    assert segunda["status"] == "BLOQUEADA"


def test_segunda_missao_conta_entradas_e_saidas_depois_de_desbloqueada():
    situacao = missao_service.situacao(contagens(gastos=3, entradas=2), {PRIMEIRA})
    segunda = por_codigo(situacao)[SEGUNDA]

    assert (segunda["atual"], segunda["alvo"], segunda["status"]) == (5, 7, "ATIVA")


def test_missao_concluida_aparece_como_concluida_mesmo_com_menos_registros():
    # O aluno excluiu um gasto depois de concluir: a conquista não some (RN-12).
    primeira = por_codigo(missao_service.situacao(contagens(gastos=1), {PRIMEIRA}))[PRIMEIRA]

    assert primeira["status"] == "CONCLUIDA"


def test_progresso_nao_passa_do_alvo():
    primeira = por_codigo(missao_service.situacao(contagens(gastos=9), set()))[PRIMEIRA]

    assert primeira["atual"] == 3


# ---------------------------------------------------------------------------
# O que concluir agora (RN-09, RN-10)
# ---------------------------------------------------------------------------

def test_nada_a_concluir_com_dois_gastos():
    assert missao_service.a_concluir(contagens(gastos=2), set()) == []


def test_terceiro_gasto_conclui_a_primeira_missao_com_30_xp():
    concluir = missao_service.a_concluir(contagens(gastos=3), set())

    assert codigos(concluir) == [PRIMEIRA]
    assert concluir[0]["xp"] == 30


def test_missao_ja_concluida_nao_e_concluida_de_novo():
    assert missao_service.a_concluir(contagens(gastos=4), {PRIMEIRA}) == []


def test_criterio_ja_cumprido_conclui_a_trilha_em_ordem():
    # Aluno que já tinha 7 gastos antes das missões existirem: conclui as duas, na ordem.
    concluir = missao_service.a_concluir(contagens(gastos=7), set())

    assert codigos(concluir) == [PRIMEIRA, SEGUNDA]


def test_segunda_missao_nao_conclui_sem_a_primeira():
    # 7 lançamentos, mas só 2 gastos: a primeira não fecha, então a segunda segue bloqueada.
    assert missao_service.a_concluir(contagens(gastos=2, entradas=5), set()) == []
