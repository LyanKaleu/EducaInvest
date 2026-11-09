"""Calcula o XP do lançamento com teto diário e o nível pelo XP acumulado (RN-11, RN-12).

A sequência de dias (streak, RN-13) fica para o próximo ciclo.
"""

# Valores de exemplo da spec (HU3). A confirmar pelo grupo.
XP_POR_LANCAMENTO = 10
TETO_DIARIO_LANCAMENTOS = 50  # só o XP de registros conta para o teto; missão fica fora

# (nível, nome, XP mínimo), do menor para o maior. Mesmo seed de docs/educainvest_schema.sql.
NIVEIS = (
    (1, "Iniciante", 0),
    (2, "Aprendiz", 100),
    (3, "Organizado", 300),
)


def xp_do_lancamento(ganho_hoje: int) -> int:
    """XP que um novo lançamento rende, respeitando o teto diário de registros.

    Args:
        ganho_hoje: XP que o aluno já ganhou hoje com registros (fuso do Piauí).

    Returns:
        int: `XP_POR_LANCAMENTO`, ou só o que falta para o teto, ou 0 se o teto
        já foi atingido. Nunca negativo.
    """
    return max(0, min(XP_POR_LANCAMENTO, TETO_DIARIO_LANCAMENTOS - ganho_hoje))


def nivel(xp_total: int) -> dict:
    """Nível correspondente ao XP acumulado.

    Args:
        xp_total: soma de todo o XP do aluno.

    Returns:
        dict: `nivel` (int), `nome` (str) e `falta` (XP que falta para o
        próximo nível, ou None se já está no último).
    """
    atual, proximo = NIVEIS[0], None
    for faixa in NIVEIS:
        if xp_total >= faixa[2]:
            atual = faixa
        else:
            proximo = faixa
            break
    return {
        "nivel": atual[0],
        "nome": atual[1],
        "falta": proximo[2] - xp_total if proximo else None,
    }
