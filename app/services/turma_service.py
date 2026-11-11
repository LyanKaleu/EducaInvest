"""Gera código único de turma e valida o nome da turma (RF02)."""
import secrets
from datetime import date, timedelta

from app.services.erros import ErroValidacao
from app.services.formulario import texto_do_campo
from app.services.xp_service import nivel

# Sem 0/O e 1/I/L, que se confundem ao copiar do quadro ou ditar em sala.
ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 6
NOME_MAX = 60

# Frequência no painel do professor: aluno ativo é quem ganhou XP (a mesma regra
# de "dia ativo" da sequência, RN-15) nos últimos 7 dias, contando hoje.
# A spec deixa "dia ativo" em aberto. A confirmar pelo grupo.
JANELA_FREQUENCIA_DIAS = 7


def validar_turma(dados) -> dict:
    nome = texto_do_campo(dados, "nome")
    if not nome:
        raise ErroValidacao({"nome": "Dê um nome à turma."})
    if len(nome) > NOME_MAX:
        raise ErroValidacao({"nome": f"O nome pode ter no máximo {NOME_MAX} caracteres."})
    return {"nome": nome}


def painel_da_turma(alunos: list[dict], resumo_xp: dict, missoes: dict, hoje: date) -> dict:
    """Progresso da turma para o professor, sem nenhum valor em reais (HU5, RN-18).

    Args:
        alunos: alunos da turma, cada um com `id` e `apelido`.
        resumo_xp: `{aluno_id: {"xp": int, "ultimo_dia": date}}` de quem já ganhou XP.
        missoes: `{aluno_id: int}` com as missões concluídas de cada aluno.
        hoje: dia de hoje no fuso do Piauí.

    Returns:
        dict: `total_alunos`; `xp_medio`, o XP médio da turma arredondado para
        o inteiro mais próximo (,5 sobe), ou None se a turma está vazia;
        `missoes_concluidas`, a soma da turma; `ativos`, quantos alunos
        ganharam XP nos últimos `JANELA_FREQUENCIA_DIAS` dias contando hoje;
        e `alunos`, uma linha por aluno com `apelido`, `xp`, `nivel`
        (de `xp_service.nivel`), `missoes` e `ativo`, na ordem recebida.
    """
    primeiro_dia_da_janela = hoje - timedelta(days=JANELA_FREQUENCIA_DIAS - 1)
    linhas = []
    for aluno in alunos:
        resumo = resumo_xp.get(aluno["id"], {"xp": 0, "ultimo_dia": None})
        ativo = resumo["ultimo_dia"] is not None and resumo["ultimo_dia"] >= primeiro_dia_da_janela
        linhas.append({
            "apelido": aluno["apelido"],
            "xp": resumo["xp"],
            "nivel": nivel(resumo["xp"]),
            "missoes": missoes.get(aluno["id"], 0),
            "ativo": ativo,
        })

    total = len(linhas)
    soma_xp = sum(linha["xp"] for linha in linhas)
    return {
        "total_alunos": total,
        "xp_medio": (soma_xp * 2 + total) // (total * 2) if total else None,
        "missoes_concluidas": sum(linha["missoes"] for linha in linhas),
        "ativos": sum(linha["ativo"] for linha in linhas),
        "alunos": linhas,
    }


def gerar_codigo_turma(aleatorio=None) -> str:
    aleatorio = aleatorio or secrets.SystemRandom()
    return "".join(aleatorio.choice(ALFABETO_CODIGO) for _ in range(TAMANHO_CODIGO))
