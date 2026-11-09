"""Leitura de campos de formulário, compartilhada pelos services."""


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
