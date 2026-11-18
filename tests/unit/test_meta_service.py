"""Testes das regras de metas e aportes (HU2)."""
import uuid
from collections.abc import Callable

import pytest

from app.services.erros import ErroValidacao
from app.services.meta_service import (
    conferir_limite_do_aporte,
    mais_perto_de_concluir,
    progresso,
    resumo,
    validar_aporte,
    validar_meta,
)
from tests.conftest import HOJE  # 2026-11-04


def form_meta(**alteracoes: str) -> dict[str, str]:
    return {"nome": "Fone", "alvo": "200,00", "prazo": "",
            "chave_idempotencia": str(uuid.uuid4()), **alteracoes}


def erros_de(funcao: Callable[..., object], *args: object, **kwargs: object) -> dict[str, str]:
    with pytest.raises(ErroValidacao) as excecao:
        funcao(*args, **kwargs)
    return excecao.value.erros


# ---------------------------------------------------------------------------
# validar_meta
# ---------------------------------------------------------------------------

def test_nome_com_mais_de_60_caracteres_e_recusado() -> None:
    erros = erros_de(validar_meta, form_meta(nome="a" * 61), hoje=HOJE)

    assert erros == {"nome": "O nome pode ter no máximo 60 caracteres."}


def test_meta_valida_sai_normalizada_e_sem_prazo_vira_none() -> None:
    chave = str(uuid.uuid4())

    dados = validar_meta(form_meta(nome="  Fone  ", alvo="1.234,50", chave_idempotencia=chave), hoje=HOJE)

    assert dados == {"nome": "Fone", "valor_alvo_centavos": 123450, "prazo": None,
                     "chave_idempotencia": chave}


def test_prazo_de_hoje_e_aceito() -> None:
    assert validar_meta(form_meta(prazo="04/11/2026"), hoje=HOJE)["prazo"] == "2026-11-04"


def test_prazo_de_ontem_e_recusado() -> None:
    erros = erros_de(validar_meta, form_meta(prazo="2026-11-03"), hoje=HOJE)

    assert erros == {"prazo": "O prazo não pode ser no passado."}


def test_meta_mostra_todos_os_erros_de_uma_vez() -> None:
    erros = erros_de(validar_meta, {"nome": "", "alvo": "-5", "prazo": "31/02/2027"}, hoje=HOJE)

    assert set(erros) == {"nome", "alvo", "prazo", "chave_idempotencia"}


# ---------------------------------------------------------------------------
# validar_aporte
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("valor", ["", "0", "0,00", "-10"])
def test_aporte_vazio_zero_ou_negativo_e_recusado(valor: str) -> None:
    erros = erros_de(validar_aporte, {"valor": valor, "chave_idempotencia": str(uuid.uuid4())})

    assert set(erros) == {"valor"}


def test_aporte_valido_vira_centavos() -> None:
    chave = str(uuid.uuid4())

    assert validar_aporte({"valor": "50,00", "chave_idempotencia": chave}) == {
        "valor_centavos": 5000, "chave_idempotencia": chave,
    }


# ---------------------------------------------------------------------------
# conferir_limite_do_aporte: o aporte não passa do que falta
# ---------------------------------------------------------------------------

def test_aporte_acima_do_que_falta_e_recusado_com_o_valor_restante() -> None:
    erros = erros_de(conferir_limite_do_aporte, 3001, alvo_centavos=20000, guardado_centavos=17000)

    assert erros == {"valor": "Faltam só R$ 30,00 para concluir esta meta. Guarde até esse valor."}


def test_aporte_igual_ao_que_falta_e_aceito() -> None:
    # Completar o alvo exato é o caminho para concluir a meta.
    assert conferir_limite_do_aporte(3000, alvo_centavos=20000, guardado_centavos=17000) is None


# ---------------------------------------------------------------------------
# progresso (RN-08)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("guardado", "percentual", "concluida"), [
    (0, 0, False),
    (10000, 50, False),
    (19999, 99, False),   # R$ 199,99 de R$ 200,00 não aparece como 100%
    (20000, 100, True),
    (23000, 100, True),   # acima do alvo para em 100%
])
def test_progresso_de_meta_de_200_reais(guardado: int, percentual: int, concluida: bool) -> None:
    assert progresso(20000, guardado) == {"percentual": percentual, "concluida": concluida}


# ---------------------------------------------------------------------------
# mais_perto_de_concluir (card da tela inicial)
# ---------------------------------------------------------------------------

def meta(id_: int, alvo: int, guardado: int) -> dict[str, int]:
    return {"id": id_, "valor_alvo_centavos": alvo, "guardado_centavos": guardado}


def test_destaca_a_meta_em_andamento_com_maior_percentual_e_ignora_concluidas() -> None:
    metas = [meta(3, 10000, 10000), meta(2, 80000, 12000), meta(1, 20000, 10000)]

    assert mais_perto_de_concluir(metas)["id"] == 1  # 50% vence 15%; a de 100% já foi


def test_no_empate_destaca_a_meta_mais_antiga() -> None:
    metas = [meta(2, 20000, 10000), meta(1, 40000, 20000)]  # as duas em 50%; id menor é mais antiga

    assert mais_perto_de_concluir(metas)["id"] == 1


def test_sem_meta_em_andamento_nao_destaca_nenhuma() -> None:
    assert mais_perto_de_concluir([]) is None
    assert mais_perto_de_concluir([meta(1, 10000, 10000)]) is None


# ---------------------------------------------------------------------------
# resumo (topo da tela de metas)
# ---------------------------------------------------------------------------

def test_resumo_soma_o_guardado_e_conta_metas_em_andamento_e_concluidas() -> None:
    metas = [meta(1, 20000, 12000), meta(2, 8000, 8000), meta(3, 50000, 0)]

    assert resumo(metas) == {"guardado": 20000, "em_andamento": 2, "concluidas": 1}


def test_meta_que_passou_do_alvo_conta_como_concluida() -> None:
    assert resumo([meta(1, 5000, 6000)]) == {"guardado": 6000, "em_andamento": 0, "concluidas": 1}


def test_resumo_sem_metas_e_zerado() -> None:
    assert resumo([]) == {"guardado": 0, "em_andamento": 0, "concluidas": 0}
