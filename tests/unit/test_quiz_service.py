"""Testes de correção de quiz e XP não repetido (HU4). Só o service."""
import pytest

from app.services import quiz_service
from app.services.erros import ErroValidacao

# Pergunta escrita à mão: os testes não dependem do texto do catálogo, que o grupo vai revisar.
PERGUNTA = {
    "codigo": "TESTE_1",
    "tema": "JUROS",
    "enunciado": "Qual rende mais em 12 meses?",
    "alternativas": {"a": "Juros simples", "b": "Juros compostos", "c": "Tanto faz", "d": "Nenhum"},
    "correta": "b",
    "explicacao": "Nos compostos, o juro de cada mês também rende.",
}


# ---------------------------------------------------------------------------
# Correção
# ---------------------------------------------------------------------------

def test_alternativa_certa_e_acerto():
    assert quiz_service.corrigir(PERGUNTA, "b") is True


def test_alternativa_errada_e_erro():
    assert quiz_service.corrigir(PERGUNTA, "a") is False


@pytest.mark.parametrize("escolha", [None, "", "   "])
def test_enviar_sem_escolher_pede_uma_alternativa(escolha):
    with pytest.raises(ErroValidacao) as erro:
        quiz_service.corrigir(PERGUNTA, escolha)

    assert erro.value.erros == {"alternativa": "Escolha uma alternativa."}


@pytest.mark.parametrize("escolha", ["e", "B", "correta"])
def test_alternativa_que_nao_e_da_pergunta_e_recusada(escolha):
    with pytest.raises(ErroValidacao) as erro:
        quiz_service.corrigir(PERGUNTA, escolha)

    assert erro.value.erros == {"alternativa": "Escolha uma das alternativas da pergunta."}


# ---------------------------------------------------------------------------
# XP do acerto: 10 por acerto, no máximo 40 por dia somando o quiz
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("ganho_hoje", "esperado"), [(0, 10), (30, 10), (35, 5), (40, 0), (55, 0)])
def test_xp_do_acerto_respeita_o_teto_diario(ganho_hoje, esperado):
    assert quiz_service.xp_do_acerto(ganho_hoje) == esperado


# ---------------------------------------------------------------------------
# Catálogo: protege as edições do grupo no texto das perguntas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pergunta", quiz_service.PERGUNTAS, ids=lambda p: p["codigo"])
def test_cada_pergunta_tem_4_alternativas_e_a_correta_entre_elas(pergunta):
    assert list(pergunta["alternativas"]) == ["a", "b", "c", "d"]
    assert all(texto.strip() for texto in pergunta["alternativas"].values())
    assert len(set(pergunta["alternativas"].values())) == 4, "alternativas repetidas"
    assert pergunta["correta"] in pergunta["alternativas"]
    assert pergunta["tema"] in quiz_service.TEMAS
    assert pergunta["enunciado"].strip() and pergunta["explicacao"].strip()


def test_banco_tem_3_perguntas_por_tema_e_codigos_unicos():
    codigos = [pergunta["codigo"] for pergunta in quiz_service.PERGUNTAS]
    por_tema = {tema: 0 for tema in quiz_service.TEMAS}
    for pergunta in quiz_service.PERGUNTAS:
        por_tema[pergunta["tema"]] += 1

    assert len(codigos) == len(set(codigos)) == 12
    assert por_tema == {"JUROS": 3, "CREDITO": 3, "ORCAMENTO": 3, "INFLACAO": 3}


def test_a_alternativa_certa_nao_e_sempre_a_mesma_letra():
    # Se a certa fosse sempre "b", o aluno acertaria sem ler.
    assert len({pergunta["correta"] for pergunta in quiz_service.PERGUNTAS}) == 4


def test_situacao_marca_nova_acertou_e_errou_pelas_respostas_do_aluno():
    respostas = {"JUROS_1": True, "CREDITO_2": False}

    status = {item["codigo"]: item["status"] for item in quiz_service.situacao(respostas)}

    assert status["JUROS_1"] == "ACERTOU"
    assert status["CREDITO_2"] == "ERROU"
    assert status["INFLACAO_3"] == "NOVA"
    assert len(status) == 12


def test_buscar_devolve_a_pergunta_pelo_codigo_ou_none():
    primeira = quiz_service.PERGUNTAS[0]

    assert quiz_service.buscar(primeira["codigo"]) == primeira
    assert quiz_service.buscar("NAO_EXISTE") is None
