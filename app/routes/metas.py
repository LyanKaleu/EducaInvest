"""Rotas para criar metas e registrar aportes (HU2, RF04)."""
import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.db import obter_conexao
from app.filtros import reais
from app.repositories.meta_repo import MetaRepository
from app.routes.acesso import exigir_perfil
from app.services import meta_service
from app.services.auth_service import PERFIL_ALUNO
from app.services.erros import ErroValidacao

bp = Blueprint("metas", __name__, url_prefix="/metas")

MSG_ERRO_FORM = "Não foi possível salvar. Confira os campos destacados."
MSG_ERRO_APORTE = "O aporte não foi registrado. Confira o valor."

# Toda rota deste Blueprint exige login de aluno (RNF04).
exigir_aluno = bp.before_request(exigir_perfil(PERFIL_ALUNO))


def _aluno_id() -> int:
    """Id do aluno logado (garantido pelo exigir_aluno)."""
    return session["usuario_id"]


def _repo() -> MetaRepository:
    # A mesma conexão da requisição: `with obter_conexao():` controla a transação.
    return MetaRepository(obter_conexao())


def _buscar_ou_404(meta_id: int) -> dict:
    # Meta de outro aluno também dá 404: não revela que o id existe.
    meta = _repo().buscar(_aluno_id(), meta_id)
    if meta is None:
        abort(404)
    return meta


def _com_progresso(meta: dict) -> dict:
    return {**meta, **meta_service.progresso(meta["valor_alvo_centavos"], meta["guardado_centavos"])}


# ---------------------------------------------------------------------------
# Listar
# ---------------------------------------------------------------------------

def _render_lista(aporte_com_erro=None, status=200):
    """Lista de metas. `aporte_com_erro` traz `meta_id`, `erros` e `form` do aporte recusado."""
    metas = [_com_progresso(meta) for meta in _repo().listar(_aluno_id())]
    html = render_template("aluno/metas.html", metas=metas, nova_chave=_nova_chave,
                           aporte_com_erro=aporte_com_erro or {})
    return html, status


@bp.get("/")
def listar():
    return _render_lista()


def _nova_chave() -> str:
    # Uma chave por formulário de aporte, gerada a cada exibição da lista (N2).
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Criar
# ---------------------------------------------------------------------------

def _render_form(form, erros=None, status=200):
    return render_template("aluno/meta_form.html", form=form, erros=erros or {}), status


@bp.get("/nova")
def nova():
    # A chave evita duplicar a meta se o envio for repetido (N2).
    return _render_form({"chave_idempotencia": str(uuid.uuid4())})


@bp.post("/nova")
def criar():
    try:
        dados = meta_service.validar_meta(request.form)
    except ErroValidacao as erro:
        flash(MSG_ERRO_FORM, "erro")
        return _render_form(request.form, erro.erros, status=400)

    with obter_conexao():
        _repo().criar(_aluno_id(), **dados)
    flash("Meta criada!", "sucesso")
    return redirect(url_for(".listar"))


# ---------------------------------------------------------------------------
# Aportar
# ---------------------------------------------------------------------------

@bp.post("/<int:meta_id>/aportes")
def aportar(meta_id):
    meta = _com_progresso(_buscar_ou_404(meta_id))
    if meta["concluida"]:  # meta cheia fecha: não aceita mais aportes
        flash("Essa meta já foi concluída.", "erro")
        return _render_lista(status=400)
    try:
        dados = meta_service.validar_aporte(request.form)
    except ErroValidacao as erro:
        flash(MSG_ERRO_APORTE, "erro")
        return _render_lista({"meta_id": meta_id, "erros": erro.erros, "form": request.form}, 400)

    with obter_conexao():
        _repo().aportar(_aluno_id(), meta_id, **dados)
    flash(f"Aporte de {reais(dados['valor_centavos'])} guardado!", "sucesso")
    if _com_progresso(_repo().buscar(_aluno_id(), meta_id))["concluida"]:
        flash(f"Parabéns, você concluiu a meta {meta['nome']}!", "sucesso")
    return redirect(url_for(".listar"))
