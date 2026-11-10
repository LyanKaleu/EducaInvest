"""Rota da tela inicial do aluno: saldo, XP, nível, sequência de dias e missão em andamento."""
from flask import Blueprint, render_template, session

from app.db import obter_conexao
from app.repositories.lancamento_repo import LancamentoRepository
from app.repositories.missao_repo import MissaoRepository
from app.repositories.xp_repo import XpRepository
from app.routes.acesso import exigir_perfil
from app.services import lancamento_service, missao_service, xp_service
from app.services.auth_service import PERFIL_ALUNO
from app.services.lancamento_service import hoje_no_piaui

bp = Blueprint("painel", __name__, url_prefix="/painel")

# Toda rota deste Blueprint exige login de aluno (RNF04).
exigir_aluno = bp.before_request(exigir_perfil(PERFIL_ALUNO))


@bp.get("/")
def ver():
    conn = obter_conexao()
    aluno_id = session["usuario_id"]
    lancamentos = LancamentoRepository(conn)
    xp_repo = XpRepository(conn)

    somas = lancamentos.somar_por_tipo(aluno_id)
    xp_total = xp_repo.total(aluno_id)
    dias_ativos = xp_repo.dias_ativos(aluno_id)
    hoje = hoje_no_piaui()
    missoes = missao_service.situacao(
        lancamentos.contar_por_tipo(aluno_id), MissaoRepository(conn).concluidas(aluno_id)
    )
    return render_template(
        "aluno/painel.html",
        saldo=lancamento_service.saldo(somas),
        entradas=somas["ENTRADA"],
        gastos=somas["SAIDA"],
        xp_total=xp_total,
        nivel=xp_service.nivel(xp_total),
        sequencia=xp_service.sequencia(dias_ativos, hoje),
        ativo_hoje=hoje in dias_ativos,
        # A próxima missão a cumprir; None quando a trilha foi concluída.
        missao=next((m for m in missoes if m["status"] == "ATIVA"), None),
    )
