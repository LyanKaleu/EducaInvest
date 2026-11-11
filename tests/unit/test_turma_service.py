"""Testes das regras de turma (RF02, HU5): nome e código de acesso. Só o service."""
import random
from datetime import date

import pytest

from app.services import turma_service
from app.services.erros import ErroValidacao


def erros_turma(nome):
    with pytest.raises(ErroValidacao) as excinfo:
        turma_service.validar_turma({"nome": nome})
    return excinfo.value.erros


def test_turma_valida_devolve_nome_sem_espacos_nas_pontas():
    assert turma_service.validar_turma({"nome": "  2º A  "}) == {"nome": "2º A"}


@pytest.mark.parametrize("nome", ["", "   "])
def test_turma_sem_nome_e_recusada(nome):
    assert erros_turma(nome) == {"nome": "Dê um nome à turma."}


def test_nome_da_turma_com_60_caracteres_e_aceito():
    assert len(turma_service.validar_turma({"nome": "a" * 60})["nome"]) == 60


def test_nome_da_turma_com_61_caracteres_e_recusado():
    assert erros_turma("a" * 61) == {"nome": "O nome pode ter no máximo 60 caracteres."}


def test_codigo_da_turma_tem_6_caracteres():
    assert len(turma_service.gerar_codigo_turma()) == 6


def test_codigo_da_turma_usa_so_o_alfabeto_sem_caracteres_ambiguos():
    codigos = "".join(turma_service.gerar_codigo_turma() for _ in range(200))

    assert set(codigos) <= set(turma_service.ALFABETO_CODIGO)


def test_alfabeto_do_codigo_nao_tem_caracteres_que_se_confundem():
    # 0/O, 1/I/L se confundem ao copiar do quadro ou ditar em sala.
    assert not set("0O1IL") & set(turma_service.ALFABETO_CODIGO)


def test_codigo_da_turma_e_reproduzivel_com_gerador_fixo():
    primeiro = turma_service.gerar_codigo_turma(aleatorio=random.Random(42))
    segundo = turma_service.gerar_codigo_turma(aleatorio=random.Random(42))

    assert primeiro == segundo


# ---------------------------------------------------------------------------
# Painel da turma (HU5, RN-18): agregados e linha por aluno, sem valores em reais.
# ---------------------------------------------------------------------------

HOJE_PAINEL = date(2026, 11, 11)


def alunos(*apelidos):
    """Alunos da turma como `listar_alunos` devolve: id (1, 2, ...) e apelido."""
    return [{"id": i, "apelido": apelido} for i, apelido in enumerate(apelidos, start=1)]


def xp(pontos, ultimo_dia=HOJE_PAINEL):
    return {"xp": pontos, "ultimo_dia": ultimo_dia}


def painel(turma, resumo_xp=None, missoes=None):
    return turma_service.painel_da_turma(turma, resumo_xp or {}, missoes or {}, HOJE_PAINEL)


@pytest.mark.parametrize("turma, resumo_xp, esperado", [
    (alunos("Ana", "Beatriz", "Caio"), {1: xp(10), 2: xp(25)}, 12),  # 35 / 3 = 11,67
    (alunos("Ana", "Beatriz"), {1: xp(5)}, 3),                       # 5 / 2 = 2,5 sobe
])
def test_xp_medio_arredonda_para_o_inteiro_mais_proximo(turma, resumo_xp, esperado):
    assert painel(turma, resumo_xp)["xp_medio"] == esperado


def test_ativo_conta_ate_seis_dias_atras():
    turma = alunos("Ana", "Beatriz", "Caio")
    resumo_xp = {
        1: xp(10, date(2026, 11, 5)),  # hoje - 6: ainda dentro dos 7 dias
        2: xp(10, date(2026, 11, 4)),  # hoje - 7: fora
    }                                  # Caio nunca ganhou XP

    resultado = painel(turma, resumo_xp)

    assert resultado["ativos"] == 1
    assert [aluno["ativo"] for aluno in resultado["alunos"]] == [True, False, False]


def test_turma_vazia_nao_tem_media():
    resultado = painel([])

    assert resultado["total_alunos"] == 0
    assert resultado["xp_medio"] is None
    assert resultado["alunos"] == []


def test_linha_do_aluno_traz_nivel_xp_e_missoes():
    turma = alunos("Ana", "Beatriz")

    resultado = painel(turma, {1: xp(120)}, {1: 2})

    assert resultado["missoes_concluidas"] == 2
    ana, beatriz = resultado["alunos"]
    assert (ana["apelido"], ana["nivel"]["nome"], ana["xp"], ana["missoes"]) == ("Ana", "Aprendiz", 120, 2)
    assert (beatriz["nivel"]["nome"], beatriz["xp"], beatriz["missoes"]) == ("Iniciante", 0, 0)
