"""Avalia o critério de cada missão, conclui uma única vez e desbloqueia a próxima (RN-09, RN-10).

O progresso é calculado a partir da contagem atual de lançamentos; só a conclusão
é gravada (pela rota, no repositório). Assim "2 de 3" nunca fica dessincronizado.
"""

# Trilha fixa, na ordem em que as missões são liberadas. Mesmo seed de
# docs/educainvest_schema.sql. Títulos e XP a confirmar pelo grupo.
# `tipo`: tipo de lançamento contado ("SAIDA"/"ENTRADA"), ou None para contar todos.
MISSOES = (
    {
        "codigo": "REG_3_GASTOS",
        "titulo": "Primeiros passos",
        "descricao": "Registre 3 gastos.",
        "tipo": "SAIDA",
        "alvo": 3,
        "xp": 30,
        "requisito": None,
    },
    {
        "codigo": "REG_7_LANCAMENTOS",
        "titulo": "Hábito em construção",
        "descricao": "Registre 7 lançamentos (entradas ou gastos).",
        "tipo": None,
        "alvo": 7,
        "xp": 50,
        "requisito": "REG_3_GASTOS",
    },
)


def _contagem(missao: dict, contagens: dict) -> int:
    if missao["tipo"] is None:
        return sum(contagens.values())
    return contagens.get(missao["tipo"], 0)


def situacao(contagens: dict, concluidas: set) -> list[dict]:
    """Estado de cada missão da trilha, para a tela.

    Args:
        contagens: {"ENTRADA": n, "SAIDA": m}, lançamentos atuais do aluno.
        concluidas: códigos das missões que o aluno já concluiu.

    Returns:
        list[dict]: cada missão de `MISSOES` com `atual` (limitado ao `alvo`) e
        `status`: "CONCLUIDA", "ATIVA" ou "BLOQUEADA" (requisito pendente).
        Missão concluída continua concluída mesmo que o aluno exclua registros.
    """
    resultado = []
    for missao in MISSOES:
        if missao["codigo"] in concluidas:
            status, atual = "CONCLUIDA", missao["alvo"]
        else:
            requisito_pendente = missao["requisito"] and missao["requisito"] not in concluidas
            status = "BLOQUEADA" if requisito_pendente else "ATIVA"
            atual = min(_contagem(missao, contagens), missao["alvo"])
        resultado.append({**missao, "atual": atual, "status": status})
    return resultado


def a_concluir(contagens: dict, concluidas: set) -> list[dict]:
    """Missões que o aluno acabou de cumprir e ainda não foram concluídas.

    Percorre a trilha em ordem: concluir uma libera a seguinte no mesmo passo,
    então quem já tinha registros suficientes conclui a trilha inteira de uma vez.

    Args:
        contagens: {"ENTRADA": n, "SAIDA": m}, lançamentos atuais do aluno.
        concluidas: códigos das missões que o aluno já concluiu.

    Returns:
        list[dict]: as missões a concluir agora, na ordem da trilha (vazia se nenhuma).
    """
    feitas = set(concluidas)
    novas = []
    for missao in MISSOES:
        if missao["codigo"] in feitas:
            continue
        if missao["requisito"] and missao["requisito"] not in feitas:
            continue
        if _contagem(missao, contagens) >= missao["alvo"]:
            novas.append(dict(missao))
            feitas.add(missao["codigo"])
    return novas
