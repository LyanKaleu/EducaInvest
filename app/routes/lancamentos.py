"""Rotas para registrar e listar entradas e gastos (HU1, RF03)."""
import uuid

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, session, url_for,
)

from app.db import obter_conexao
from app.filtros import data_br, reais  # noqa: F401 (mantém os nomes importáveis daqui)
from app.repositories.lancamento_repo import LancamentoRepository
from app.routes.acesso import exigir_perfil
from app.services.auth_service import PERFIL_ALUNO
from app.services.erros import ErroValidacao
from app.services.lancamento_service import CATEGORIAS, hoje_no_piaui, validar_lancamento

bp = Blueprint("lancamentos", __name__, url_prefix="/lancamentos")

MSG_ERRO_FORM = "Não foi possível salvar. Confira os campos destacados."


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

# Toda rota deste Blueprint exige login de aluno (RNF04).
exigir_aluno = bp.before_request(exigir_perfil(PERFIL_ALUNO))


def _aluno_id() -> int:
    """Id do aluno logado (garantido pelo exigir_aluno)."""
    return session["usuario_id"]


def _repo() -> LancamentoRepository:
    # obter_conexao() devolve sempre a MESMA conexão durante a requisição,
    # então `with obter_conexao():` controla a transação do repositório.
    return LancamentoRepository(obter_conexao())


def _buscar_ou_404(lancamento_id: int) -> dict:
    # Lançamento de outro aluno também dá 404: não revela que o id existe.
    lancamento = _repo().buscar(_aluno_id(), lancamento_id)
    if lancamento is None:
        abort(404)
    return lancamento


def _centavos_para_campo(centavos: int) -> str:
    """2550 -> '25,50' (formato que o aluno digita no formulário)."""
    return f"{centavos // 100},{centavos % 100:02d}"


def _form_do_registro(lancamento: dict) -> dict:
    """Converte um registro do banco nos valores que o formulário de edição mostra."""
    return {
        "tipo": lancamento["tipo"].lower(),
        "categoria": lancamento["categoria"],
        "valor": _centavos_para_campo(lancamento["valor_centavos"]),
        "data": lancamento["data_lancamento"],
        "descricao": lancamento["descricao"] or "",
    }


def _render_form(form, erros=None, lancamento=None, status=200):
    """Formulário de criar (lancamento=None) ou editar, já preenchido com `form`."""
    html = render_template(
        "aluno/lancamento_form.html",
        form=form,
        erros=erros or {},
        lancamento=lancamento,
        categorias=CATEGORIAS,
    )
    return html, status


# ---------------------------------------------------------------------------
# Listar
# ---------------------------------------------------------------------------

@bp.get("/")
def listar():
    busca = request.args.get("busca", "").strip()
    lancamentos = _repo().listar(_aluno_id(), busca or None)
    return render_template("aluno/lancamentos.html", lancamentos=lancamentos, busca=busca)


# ---------------------------------------------------------------------------
# Criar
# ---------------------------------------------------------------------------

@bp.get("/novo")
def novo():
    form = {
        "tipo": "saida",  # gasto é o caso mais comum (HU1)
        "data": hoje_no_piaui().isoformat(),
        "chave_idempotencia": str(uuid.uuid4()),  # evita duplicar se o envio for repetido
    }
    return _render_form(form)


@bp.post("/novo")
def criar():
    try:
        dados = validar_lancamento(request.form)
    except ErroValidacao as erro:
        flash(MSG_ERRO_FORM, "erro")
        return _render_form(request.form, erro.erros, status=400)

    with obter_conexao():
        _repo().criar(_aluno_id(), **dados)
    flash("Lançamento salvo!", "sucesso")
    return redirect(url_for(".listar"))


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

@bp.get("/<int:lancamento_id>/editar")
def editar(lancamento_id):
    lancamento = _buscar_ou_404(lancamento_id)
    return _render_form(_form_do_registro(lancamento), lancamento=lancamento)


@bp.post("/<int:lancamento_id>/editar")
def atualizar(lancamento_id):
    lancamento = _buscar_ou_404(lancamento_id)
    # Na edição a chave de idempotência é a do registro original e não muda.
    dados_form = {**request.form.to_dict(), "chave_idempotencia": lancamento["chave_idempotencia"]}
    try:
        dados = validar_lancamento(dados_form)
    except ErroValidacao as erro:
        flash(MSG_ERRO_FORM, "erro")
        return _render_form(request.form, erro.erros, lancamento=lancamento, status=400)

    dados.pop("chave_idempotencia")
    with obter_conexao():
        _repo().atualizar(_aluno_id(), lancamento_id, dados)
    flash("Lançamento atualizado!", "sucesso")
    return redirect(url_for(".listar"))


# ---------------------------------------------------------------------------
# Excluir: GET mostra a confirmação; só o POST apaga.
# ---------------------------------------------------------------------------

@bp.get("/<int:lancamento_id>/excluir")
def confirmar_exclusao(lancamento_id):
    lancamento = _buscar_ou_404(lancamento_id)
    return render_template("aluno/lancamento_excluir.html", lancamento=lancamento)


@bp.post("/<int:lancamento_id>/excluir")
def excluir(lancamento_id):
    with obter_conexao():
        apagou = _repo().excluir(_aluno_id(), lancamento_id)
    if not apagou:
        abort(404)
    flash("Lançamento excluído.", "sucesso")
    return redirect(url_for(".listar"))
