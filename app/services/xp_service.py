"""Calcula o XP do lançamento com teto diário, o nível e a sequência de dias (RN-11 a RN-13)."""
from datetime import date, timedelta

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
        dict: `nivel` (int), `nome` (str), `falta` (XP que falta para o
        próximo nível, ou None se já está no último) e `percentual` (int de
        0 a 100: quanto do nível atual já foi feito, arredondado para baixo;
        100 no último nível).
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
        "percentual": (xp_total - atual[2]) * 100 // (proximo[2] - atual[2]) if proximo else 100,
    }


def sequencia(dias_ativos: set[date], hoje: date) -> int:
    """Dias seguidos com atividade até hoje (streak, RN-13).

    Hoje ainda não acabou: se o aluno não teve atividade hoje, a sequência
    conta a partir de ontem. Um dia inteiro em branco zera.

    Args:
        dias_ativos: dias (fuso do Piauí) em que o aluno ganhou XP.
        hoje: dia de hoje no fuso do Piauí.

    Returns:
        int: quantidade de dias seguidos; 0 se ontem e hoje estão em branco.
    """
    dia = hoje if hoje in dias_ativos else hoje - timedelta(days=1)
    total = 0
    while dia in dias_ativos:
        total += 1
        dia -= timedelta(days=1)
    return total


def ultimos_dias(dias_ativos: set[date], hoje: date, quantidade: int = 7) -> list[bool]:
    """Se o aluno ganhou XP em cada um dos últimos dias, do mais antigo até hoje.

    Alimenta as marcas da sequência na tela inicial.

    Args:
        dias_ativos: dias (fuso do Piauí) em que o aluno ganhou XP.
        hoje: dia de hoje no fuso do Piauí; é o último da lista.
        quantidade: tamanho da janela, contando hoje.

    Returns:
        list[bool]: `quantidade` itens; True no dia em que houve XP.
    """
    return [hoje - timedelta(days=atras) in dias_ativos for atras in range(quantidade - 1, -1, -1)]
