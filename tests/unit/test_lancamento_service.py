"""Testes das regras de lançamento (HU1, RN-07): só o validador, sem Flask nem banco."""
import pytest

from app.services.erros import ErroValidacao
from app.services.lancamento_service import validar_lancamento
from tests.conftest import HOJE


def validar(form, **alteracoes):
    return validar_lancamento({**form, **alteracoes}, hoje=HOJE)


def erros_de(form, **alteracoes):
    with pytest.raises(ErroValidacao) as excinfo:
        validar(form, **alteracoes)
    return excinfo.value.erros


# ---------------------------------------------------------------------------
# Caminho feliz
# ---------------------------------------------------------------------------

def test_gasto_valido_devolve_dados_normalizados(form_valido):
    dados = validar(form_valido)

    assert dados == {
        "tipo": "SAIDA",
        "categoria": "Alimentação",
        "valor_centavos": 2500,
        "data_lancamento": "2026-11-01",
        "descricao": "lanche",
        "chave_idempotencia": form_valido["chave_idempotencia"],
    }


def test_entrada_valida_devolve_tipo_entrada(form_valido):
    dados = validar(form_valido, tipo="entrada", categoria="Mesada")

    assert (dados["tipo"], dados["categoria"]) == ("ENTRADA", "Mesada")


# ---------------------------------------------------------------------------
# Entradas válidas em formatos diferentes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("valor, centavos", [
    ("25", 2500),
    ("25,5", 2550),
    ("25,50", 2550),
    ("25.50", 2550),          # o que o input type=number envia
    ("1.234,56", 123456),
    ("1.234", 123400),
    ("R$ 1.234,00", 123400),
    ("  10  ", 1000),
])
def test_valor_aceita_formatos_brasileiros(form_valido, valor, centavos):
    assert validar(form_valido, valor=valor)["valor_centavos"] == centavos


@pytest.mark.parametrize("tipo", ["saida", "saída", "SAIDA", "Saída"])
def test_tipo_aceita_variacoes_de_escrita(form_valido, tipo):
    assert validar(form_valido, tipo=tipo)["tipo"] == "SAIDA"


def test_categoria_ignora_maiusculas_e_devolve_nome_oficial(form_valido):
    assert validar(form_valido, categoria="ALIMENTAÇÃO")["categoria"] == "Alimentação"


@pytest.mark.parametrize("data", ["2026-11-01", "01/11/2026", "1/11/2026"])
def test_data_aceita_formato_iso_e_brasileiro(form_valido, data):
    assert validar(form_valido, data=data)["data_lancamento"] == "2026-11-01"


def test_data_vazia_usa_o_dia_de_hoje(form_valido):
    assert validar(form_valido, data="")["data_lancamento"] == HOJE.isoformat()


def test_descricao_vazia_vira_none(form_valido):
    assert validar(form_valido, descricao="   ")["descricao"] is None


def test_descricao_tem_espacos_das_pontas_removidos(form_valido):
    assert validar(form_valido, descricao="  lanche  ")["descricao"] == "lanche"


def test_descricao_ausente_do_formulario_vira_none(form_valido):
    form_valido.pop("descricao")
    assert validar(form_valido)["descricao"] is None


def test_chave_em_maiusculas_e_normalizada(form_valido):
    chave = form_valido["chave_idempotencia"]
    assert validar(form_valido, chave_idempotencia=chave.upper())["chave_idempotencia"] == chave


# ---------------------------------------------------------------------------
# Bordas
# ---------------------------------------------------------------------------

def test_descricao_com_140_caracteres_e_aceita(form_valido):
    assert len(validar(form_valido, descricao="a" * 140)["descricao"]) == 140


def test_descricao_com_141_caracteres_e_recusada(form_valido):
    assert "descricao" in erros_de(form_valido, descricao="a" * 141)


def test_valor_minimo_de_um_centavo_e_aceito(form_valido):
    assert validar(form_valido, valor="0,01")["valor_centavos"] == 1


def test_valor_de_100_mil_reais_e_aceito(form_valido):
    assert validar(form_valido, valor="100.000,00")["valor_centavos"] == 10_000_000


def test_valor_acima_de_100_mil_reais_e_recusado(form_valido):
    assert "valor" in erros_de(form_valido, valor="100.000,01")


def test_data_de_hoje_e_aceita(form_valido):
    assert validar(form_valido, data=HOJE.isoformat())["data_lancamento"] == "2026-11-04"


def test_data_de_amanha_e_recusada(form_valido):
    assert erros_de(form_valido, data="2026-11-05") == {"data": "A data não pode ser no futuro."}


@pytest.mark.parametrize("data", ["31/02/2026", "2026-02-29", "2026-13-01", "00/11/2026"])
def test_data_inexistente_e_recusada(form_valido, data):
    assert erros_de(form_valido, data=data) == {"data": "Essa data não existe."}


def test_29_de_fevereiro_de_ano_bissexto_e_aceito(form_valido):
    assert validar(form_valido, data="29/02/2024")["data_lancamento"] == "2024-02-29"


@pytest.mark.parametrize("data", ["2026/11/01", "01-11-2026", "ontem", "2026-11-01T10:00"])
def test_data_em_formato_desconhecido_e_recusada(form_valido, data):
    assert "data" in erros_de(form_valido, data=data)


# ---------------------------------------------------------------------------
# Entradas inválidas: cada erro aparece só no campo certo (HU1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("valor", ["", "0", "0,00", "-5", "abc", "25,555", "1,2,3"])
def test_valor_invalido_gera_erro_apenas_no_valor(form_valido, valor):
    assert list(erros_de(form_valido, valor=valor)) == ["valor"]


def test_valor_vazio_pede_para_informar(form_valido):
    assert erros_de(form_valido, valor="")["valor"] == "Informe o valor."


def test_valor_negativo_explica_que_precisa_ser_maior_que_zero(form_valido):
    assert erros_de(form_valido, valor="-5")["valor"] == "O valor precisa ser maior que zero."


@pytest.mark.parametrize("tipo", ["", "gasto", "x"])
def test_tipo_invalido_e_recusado(form_valido, tipo):
    assert "tipo" in erros_de(form_valido, tipo=tipo)


def test_sem_categoria_pede_para_escolher(form_valido):
    assert erros_de(form_valido, categoria="") == {"categoria": "Escolha uma categoria."}


def test_categoria_fora_da_lista_e_recusada(form_valido):
    assert erros_de(form_valido, categoria="Viagem") == {"categoria": "Escolha uma categoria da lista."}


def test_categoria_de_entrada_em_um_gasto_e_recusada(form_valido):
    erros = erros_de(form_valido, categoria="Mesada")
    assert erros == {"categoria": "Essa categoria não combina com o tipo escolhido."}


@pytest.mark.parametrize("chave", ["", "123", "nao-e-uuid"])
def test_chave_de_idempotencia_invalida_e_recusada(form_valido, chave):
    assert "chave_idempotencia" in erros_de(form_valido, chave_idempotencia=chave)


def test_varios_erros_sao_devolvidos_de_uma_vez(form_valido):
    assert set(erros_de(form_valido, valor="", categoria="", data="2999-01-01")) == {
        "valor", "categoria", "data",
    }


def test_mensagem_da_excecao_junta_todas_as_mensagens(form_valido):
    with pytest.raises(ErroValidacao) as excinfo:
        validar(form_valido, valor="", categoria="")
    assert "Informe o valor." in str(excinfo.value)
    assert "Escolha uma categoria." in str(excinfo.value)
