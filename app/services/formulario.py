"""Leitura e conversão de campos de formulário (texto, valor em reais, data, chave), compartilhadas pelos services.

Os conversores recebem o texto já sem espaços nas pontas e devolvem o valor
normalizado, ou levantam ValueError com a mensagem que o aluno vai ler.
"""
import re
import uuid
from datetime import date
from decimal import Decimal

VALOR_MAXIMO_CENTAVOS = 10_000_000  # R$ 100.000,00: barra erros de digitação. A confirmar.


def texto_do_campo(dados, nome: str) -> str:
    """Lê um campo de texto e remove os espaços das pontas.

    Args:
        dados: objeto com `.get(nome)`, por exemplo `request.form` ou um dict.
        nome: nome do campo.

    Returns:
        str: o texto sem espaços nas pontas, ou "" se o campo faltar ou for None.
    """
    valor = dados.get(nome)
    return "" if valor is None else str(valor).strip()


def converter_valor(texto: str) -> int:
    """Converte um valor em reais digitado ("25,50", "1.234,56", "25.50") em centavos.

    Raises:
        ValueError: se estiver vazio, mal formatado, for zero ou negativo, ou
            passar de `VALOR_MAXIMO_CENTAVOS`.
    """
    if not texto:
        raise ValueError("Informe o valor.")
    limpo = texto.replace("R$", "").replace(" ", "").replace(" ", "")
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


def ler_data(texto: str) -> date:
    """Converte "AAAA-MM-DD" (input type=date) ou "dd/mm/aaaa" em `date`.

    Raises:
        ValueError: se o formato for outro ou a data não existir.
    """
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texto):      # 2026-11-04 (input type=date)
        ano, mes, dia = m.groups()
    elif m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto):  # 04/11/2026
        dia, mes, ano = m.groups()
    else:
        raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")
    try:
        return date(int(ano), int(mes), int(dia))
    except ValueError:
        raise ValueError("Essa data não existe.") from None


def converter_chave(texto: str) -> str:
    """Valida a chave de idempotência do envio (UUID) e a devolve normalizada.

    Raises:
        ValueError: se não for um UUID.
    """
    try:
        return str(uuid.UUID(texto))
    except ValueError:
        raise ValueError(
            "Não foi possível identificar este envio. Recarregue a página e tente de novo."
        ) from None
