"""Testes das regras de turma (RF02, HU5): nome e código de acesso. Só o service."""
import random

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
