"""Rotas para abrir um quiz, responder e ver a explicação (HU4, RF06)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.db import obter_conexao
from app.repositories.quiz_repo import QuizRepository
from app.repositories.xp_repo import XpRepository
from app.routes.acesso import exigir_perfil
from app.services import quiz_service
from app.services.auth_service import PERFIL_ALUNO
from app.services.erros import ErroValidacao
from app.services.lancamento_service import hoje_no_piaui

bp = Blueprint("quiz", __name__, url_prefix="/quiz")

MSG_ERRO_FORM = "A resposta não foi enviada. Marque uma alternativa."

# Toda rota deste Blueprint exige login de aluno (RNF04).
exigir_aluno = bp.before_request(exigir_perfil(PERFIL_ALUNO))


def _aluno_id() -> int:
    """Id do aluno logado (garantido pelo exigir_aluno)."""
    return session["usuario_id"]


def _pergunta_ou_404(codigo: str) -> dict:
    pergunta = quiz_service.buscar(codigo)
    if pergunta is None:
        abort(404)
    return pergunta


def _xp_do_quiz_hoje(conn) -> int:
    return XpRepository(conn).pontos_no_dia(_aluno_id(), "QUIZ", hoje_no_piaui().isoformat())


def _render_pergunta(pergunta, erros=None, status=200):
    conn = obter_conexao()
    repo = QuizRepository(conn)
    resposta = repo.resposta(_aluno_id(), pergunta["codigo"])
    # Depois de responder, o atalho leva à próxima pergunta ainda não respondida.
    novas = [item for item in quiz_service.situacao(repo.acertos_por_pergunta(_aluno_id()))
             if item["status"] == "NOVA"]
    html = render_template("aluno/quiz_pergunta.html", pergunta=pergunta, resposta=resposta,
                           erros=erros or {}, xp_hoje=_xp_do_quiz_hoje(conn),
                           teto=quiz_service.TETO_DIARIO_QUIZ,
                           tema_nome=quiz_service.TEMAS[pergunta["tema"]],
                           proxima=novas[0] if novas else None)
    return html, status


@bp.get("/")
def listar():
    conn = obter_conexao()
    perguntas = quiz_service.situacao(QuizRepository(conn).acertos_por_pergunta(_aluno_id()))
    return render_template("aluno/quiz.html", perguntas=perguntas, temas=quiz_service.TEMAS,
                           xp_hoje=_xp_do_quiz_hoje(conn), teto=quiz_service.TETO_DIARIO_QUIZ,
                           xp_por_acerto=quiz_service.XP_POR_ACERTO)


@bp.get("/<codigo>")
def ver(codigo):
    return _render_pergunta(_pergunta_ou_404(codigo))


@bp.post("/<codigo>")
def responder(codigo):
    pergunta = _pergunta_ou_404(codigo)
    if QuizRepository(obter_conexao()).resposta(_aluno_id(), codigo) is not None:
        # Já respondida (reenvio, clique duplo, nova tentativa): a primeira resposta vale (RN-16).
        return redirect(url_for(".ver", codigo=codigo))
    # A mesma letra que o service valida é a que vai para o banco (" c" vira "c").
    escolha = (request.form.get("alternativa") or "").strip()
    try:
        acertou = quiz_service.corrigir(pergunta, escolha)
    except ErroValidacao as erro:
        flash(MSG_ERRO_FORM, "erro")
        return _render_pergunta(pergunta, erro.erros, status=400)

    conn = obter_conexao()
    hoje = hoje_no_piaui().isoformat()
    xp_ganho = 0
    # Resposta e XP gravados juntos ou nenhum dos dois (INVARIANTES N6).
    with conn:
        gravou = QuizRepository(conn).responder(_aluno_id(), codigo, escolha, acertou)
        # Só paga quem gravou agora: num envio simultâneo, o segundo não grava nem pontua.
        if gravou and acertou:
            xp_repo = XpRepository(conn)
            xp_ganho = quiz_service.xp_do_acerto(xp_repo.pontos_no_dia(_aluno_id(), "QUIZ", hoje))
            if xp_ganho:  # teto atingido: a resposta vale, mas sem XP
                xp_repo.creditar(_aluno_id(), "QUIZ", codigo, xp_ganho, hoje)

    if xp_ganho:
        flash(f"+{xp_ganho} XP no quiz!", "sucesso")
    elif acertou:
        flash(f"Você já ganhou os {quiz_service.TETO_DIARIO_QUIZ} XP do quiz hoje. "
              "Este acerto vale como aprendizado.", "sucesso")
    return redirect(url_for(".ver", codigo=codigo))
