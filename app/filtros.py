"""Filtros Jinja usados em todas as telas: dinheiro e data no formato brasileiro."""


def reais(centavos: int) -> str:
    """Formata centavos como dinheiro: 123456 -> 'R$ 1.234,56'; -1050 -> '-R$ 10,50'."""
    # divmod de negativo arredonda para baixo (-1050 -> -11 e 50): formata o módulo e põe o sinal.
    inteiro, resto = divmod(abs(centavos), 100)
    sinal = "-" if centavos < 0 else ""
    return f"{sinal}R$ {inteiro:,}".replace(",", ".") + f",{resto:02d}"


def data_br(data_iso: str) -> str:
    """Formata uma data ISO no padrão brasileiro: '2026-11-04' -> '04/11/2026'."""
    ano, mes, dia = data_iso.split("-")
    return f"{dia}/{mes}/{ano}"


def registrar_filtros(app) -> None:
    """Disponibiliza `reais` e `data_br` em todos os templates do app."""
    app.add_template_filter(reais, "reais")
    app.add_template_filter(data_br, "data_br")
