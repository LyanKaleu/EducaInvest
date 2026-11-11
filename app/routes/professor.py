"""Rotas do professor: criar turma, ver o código e o painel da turma (RF02, HU5)."""
from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)

from app.db import obter_conexao
from app.repositories.missao_repo import MissaoRepository
from app.repositories.turma_repo import TurmaRepository
from app.repositories.xp_repo import XpRepository
from app.routes.acesso import exigir_perfil
from app.services.auth_service import PERFIL_PROFESSOR
from app.services.erros import ErroValidacao
from app.services.lancamento_service import hoje_no_piaui
from app.services.turma_service import gerar_codigo_turma, painel_da_turma, validar_turma

bp = Blueprint("professor", __name__, url_prefix="/professor")


# Toda rota deste Blueprint exige login de professor (RNF04).
exigir_professor = bp.before_request(exigir_perfil(PERFIL_PROFESSOR))


def _repo() -> TurmaRepository:
    return TurmaRepository(obter_conexao())


def _render_turmas(erros=None, status=200):
    turmas = _repo().listar_do_professor(session["usuario_id"])
    html = render_template("professor/turmas.html", turmas=turmas,
                           form=request.form, erros=erros or {})
    return html, status


@bp.get("/turmas")
def turmas():
    return _render_turmas()


@bp.post("/turmas")
def criar_turma():
    professor_id = session["usuario_id"]
    try:
        dados = validar_turma(request.form)
    except ErroValidacao as erro:
        flash("Não foi possível criar a turma.", "erro")
        return _render_turmas(erro.erros, 400)

    if _repo().existe_nome(professor_id, dados["nome"]):
        flash("Não foi possível criar a turma.", "erro")
        return _render_turmas({"nome": "Você já tem uma turma com esse nome."}, 400)

    codigo = gerar_codigo_turma()
    while _repo().buscar_por_codigo(codigo):  # colisão é raríssima, mas possível
        codigo = gerar_codigo_turma()

    with obter_conexao():
        _repo().criar(professor_id, dados["nome"], codigo)
    flash(f"Turma criada! Código de acesso: {codigo}", "sucesso")
    return redirect(url_for(".turmas"))


@bp.get("/turmas/<int:turma_id>")
def turma(turma_id):
    # Turma de outro professor também dá 404: não revela que o id existe.
    registro = _repo().buscar_do_professor(session["usuario_id"], turma_id)
    if registro is None:
        abort(404)
    conn = obter_conexao()
    alunos = _repo().listar_alunos(turma_id)
    ids = [aluno["id"] for aluno in alunos]
    painel = painel_da_turma(
        alunos,
        XpRepository(conn).resumo_por_aluno(ids),
        MissaoRepository(conn).contar_por_aluno(ids),
        hoje_no_piaui(),
    )
    return render_template("professor/turma.html", turma=registro, painel=painel)
