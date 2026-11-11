"""Rota das missões, conquistas, XP e nível do aluno, e o progresso gerado por cada registro (HU3)."""
import sqlite3

from flask import Blueprint, flash, render_template, session

from app.db import obter_conexao
from app.repositories.lancamento_repo import LancamentoRepository
from app.repositories.missao_repo import MissaoRepository
from app.repositories.xp_repo import XpRepository
from app.routes.acesso import exigir_perfil
from app.services import missao_service, xp_service
from app.services.auth_service import PERFIL_ALUNO
from app.services.lancamento_service import hoje_no_piaui

bp = Blueprint("missoes", __name__, url_prefix="/missoes")

# Toda rota deste Blueprint exige login de aluno (RNF04).
exigir_aluno = bp.before_request(exigir_perfil(PERFIL_ALUNO))


@bp.get("/")
def listar():
    conn = obter_conexao()
    aluno_id = session["usuario_id"]
    contagens = LancamentoRepository(conn).contar_por_tipo(aluno_id)
    concluidas = MissaoRepository(conn).concluidas(aluno_id)
    xp_total = XpRepository(conn).total(aluno_id)
    return render_template(
        "aluno/missoes.html",
        missoes=missao_service.situacao(contagens, concluidas),
        xp_total=xp_total,
        nivel=xp_service.nivel(xp_total),
    )


# ---------------------------------------------------------------------------
# Progresso: chamado pelas rotas de lançamento, DENTRO da transação delas
# ---------------------------------------------------------------------------

def registrar_progresso(conn: sqlite3.Connection, aluno_id: int, lancamento_id=None) -> dict:
    """Credita o XP do lançamento, conclui as missões cumpridas e detecta a subida de nível.

    Não faz commit: chame dentro do mesmo `with conn:` que gravou o lançamento,
    para que lançamento e XP sejam gravados juntos ou nenhum dos dois (HU3).

    Args:
        conn: conexão da requisição, com a transação aberta.
        aluno_id: id do aluno logado.
        lancamento_id: id do lançamento recém-criado, que rende XP de registro.
            None na edição, que só reavalia as missões.

    Returns:
        dict: `xp_lancamento` (XP creditado pelo registro), `teto_atingido` (bool),
        `conquistas` (missões concluídas agora) e `novo_nivel` (dict de
        `xp_service.nivel`, ou None se o nível não mudou).
    """
    xp_repo = XpRepository(conn)
    missao_repo = MissaoRepository(conn)
    hoje = hoje_no_piaui().isoformat()
    nivel_antes = xp_service.nivel(xp_repo.total(aluno_id))["nivel"]

    xp_lancamento, teto_atingido = 0, False
    if lancamento_id is not None:
        pontos = xp_service.xp_do_lancamento(xp_repo.pontos_no_dia(aluno_id, "LANCAMENTO", hoje))
        teto_atingido = pontos == 0
        # Reenvio da mesma chave devolve o mesmo lançamento: o UNIQUE barra o 2º crédito.
        if pontos and xp_repo.creditar(aluno_id, "LANCAMENTO", lancamento_id, pontos, hoje):
            xp_lancamento = pontos

    contagens = LancamentoRepository(conn).contar_por_tipo(aluno_id)
    conquistas = []
    for missao in missao_service.a_concluir(contagens, missao_repo.concluidas(aluno_id)):
        if missao_repo.concluir(aluno_id, missao["codigo"]):
            xp_repo.creditar(aluno_id, "MISSAO", missao["codigo"], missao["xp"], hoje)
            conquistas.append(missao)

    nivel_depois = xp_service.nivel(xp_repo.total(aluno_id))
    return {
        "xp_lancamento": xp_lancamento,
        "teto_atingido": teto_atingido,
        "conquistas": conquistas,
        "novo_nivel": nivel_depois if nivel_depois["nivel"] > nivel_antes else None,
    }


def avisar_conquistas(progresso: dict) -> None:
    """Mostra (flash) as conquistas e a subida de nível do `registrar_progresso`."""
    for missao in progresso["conquistas"]:
        flash(f"Conquista desbloqueada: {missao['titulo']}! +{missao['xp']} XP", "sucesso")
    if progresso["novo_nivel"]:
        nivel = progresso["novo_nivel"]
        flash(f"Você subiu para o nível {nivel['nivel']} ({nivel['nome']})!", "sucesso")
