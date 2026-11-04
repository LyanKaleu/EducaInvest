"""Valida lançamentos (RN-07), calcula saldo e dispara a verificação de missões."""
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.services.erros import ErroValidacao
from app.services.formulario import texto_do_campo

# O Piauí fica em UTC-3 o ano todo (sem horário de verão). Usamos o deslocamento
# fixo porque, no Windows, zoneinfo("America/Fortaleza") exige instalar o pacote tzdata.
FUSO_PIAUI = timezone(timedelta(hours=-3), "America/Fortaleza")

TIPOS = {"entrada": "ENTRADA", "saida": "SAIDA", "saída": "SAIDA"}

# Lista fixa (mesma do seed em docs/educainvest_schema.sql). A confirmar pelo grupo.
CATEGORIAS = {
    "ENTRADA": ("Mesada", "Trabalho/bico", "Benefício", "Outras entradas"),
    "SAIDA": ("Alimentação", "Transporte", "Lazer", "Compras", "Estudos", "Outras saídas"),
}

DESCRICAO_MAX = 140
VALOR_MAXIMO_CENTAVOS = 10_000_000  # R$ 100.000,00: barra erros de digitação. A confirmar.


def hoje_no_piaui() -> date:
    """Devolve a data de hoje no fuso do Piauí (UTC-3).

    Returns:
        date: o dia atual em America/Fortaleza, usado como "hoje" nas regras
        de data (RN-07, RN-13).
    """
    return datetime.now(FUSO_PIAUI).date()


def validar_lancamento(dados, hoje: date | None = None) -> dict:
    """Valida o formulário de lançamento e devolve os dados normalizados.

    Confere todos os campos antes de responder, para a tela mostrar todos os
    erros de uma vez, cada um junto ao seu campo (HU1).

    Args:
        dados: objeto com `.get(nome)`, por exemplo `request.form` ou um dict,
            com os campos `tipo`, `categoria`, `valor`, `data`, `descricao` e
            `chave_idempotencia`, todos como texto.
        hoje: data considerada "hoje" para recusar datas futuras e preencher
            a data vazia. Se for None, usa `hoje_no_piaui()`. Os testes passam
            uma data fixa.

    Returns:
        dict: com as chaves `tipo` ("ENTRADA" ou "SAIDA"), `categoria` (nome
        oficial da lista), `valor_centavos` (int), `data_lancamento`
        ("AAAA-MM-DD"), `descricao` (str ou None) e `chave_idempotencia`
        (UUID em texto). Os nomes batem com os parâmetros de
        `LancamentoRepository.criar`.

    Raises:
        ErroValidacao: se algum campo for inválido. O atributo `erros` mapeia
            o nome do campo do formulário para a mensagem em português.
    """
    hoje = hoje or hoje_no_piaui()
    erros: dict[str, str] = {}

    def campo(nome, conversor, *args):
        try:
            return conversor(texto_do_campo(dados, nome), *args)
        except ValueError as erro:
            erros[nome] = str(erro)
            return None

    tipo = campo("tipo", _converter_tipo)
    categoria = campo("categoria", _converter_categoria, tipo)
    valor_centavos = campo("valor", _converter_valor)
    data_lancamento = campo("data", _converter_data, hoje)
    descricao = campo("descricao", _converter_descricao)
    chave = campo("chave_idempotencia", _converter_chave)

    if erros:
        raise ErroValidacao(erros)

    return {
        "tipo": tipo,
        "categoria": categoria,
        "valor_centavos": valor_centavos,
        "data_lancamento": data_lancamento.isoformat(),
        "descricao": descricao,
        "chave_idempotencia": chave,
    }


# ---------------------------------------------------------------------------
# Conversores: recebem o texto já sem espaços nas pontas e devolvem o valor
# normalizado, ou levantam ValueError com a mensagem que o aluno vai ler.
# ---------------------------------------------------------------------------


def _converter_tipo(texto):
    tipo = TIPOS.get(texto.casefold())
    if tipo is None:
        raise ValueError("Escolha se é uma entrada ou um gasto.")
    return tipo


def _converter_categoria(texto, tipo):
    if not texto:
        raise ValueError("Escolha uma categoria.")
    if tipo is None:  # o erro do tipo já foi informado; não dá para checar a categoria
        return None
    for nome in CATEGORIAS[tipo]:
        if nome.casefold() == texto.casefold():
            return nome
    outro_tipo = "SAIDA" if tipo == "ENTRADA" else "ENTRADA"
    if any(nome.casefold() == texto.casefold() for nome in CATEGORIAS[outro_tipo]):
        raise ValueError("Essa categoria não combina com o tipo escolhido.")
    raise ValueError("Escolha uma categoria da lista.")


def _converter_valor(texto):
    if not texto:
        raise ValueError("Informe o valor.")
    limpo = texto.replace("R$", "").replace(" ", "").replace(" ", "")
    if limpo.startswith("-"):
        raise ValueError("O valor precisa ser maior que zero.")

    if re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{1,2}|\d+,\d{1,2}", limpo):
        numero = limpo.replace(".", "").replace(",", ".")  # 1.234,56 -> 1234.56
    elif re.fullmatch(r"\d+(\.\d{1,2})?", limpo):
        numero = limpo                                        # 25 ou 25.50 (input type=number)
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", limpo):
        numero = limpo.replace(".", "")                       # 1.234 -> 1234
    else:
        raise ValueError("Valor inválido. Use só números, por exemplo 25,50.")

    centavos = int(Decimal(numero) * 100)
    if centavos <= 0:
        raise ValueError("O valor precisa ser maior que zero.")
    if centavos > VALOR_MAXIMO_CENTAVOS:
        raise ValueError("O valor máximo é R$ 100.000,00.")
    return centavos


def _converter_data(texto, hoje):
    if not texto:
        return hoje  # RNF03: menos toques; sem data, vale o dia de hoje
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texto):      # 2026-11-04 (input type=date)
        ano, mes, dia = m.groups()
    elif m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto):  # 04/11/2026
        dia, mes, ano = m.groups()
    else:
        raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")
    try:
        data = date(int(ano), int(mes), int(dia))
    except ValueError:
        raise ValueError("Essa data não existe.") from None
    if data > hoje:
        raise ValueError("A data não pode ser no futuro.")
    return data


def _converter_descricao(texto):
    if len(texto) > DESCRICAO_MAX:
        raise ValueError(f"A descrição pode ter no máximo {DESCRICAO_MAX} caracteres.")
    return texto or None


def _converter_chave(texto):
    try:
        return str(uuid.UUID(texto))
    except ValueError:
        raise ValueError(
            "Não foi possível identificar este envio. Recarregue a página e tente de novo."
        ) from None
