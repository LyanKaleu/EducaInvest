"""Fluxo HTTP do professor: criar turma, ver o código e a lista de alunos (RF02, HU5)."""

import re

import pytest
from flask import Flask
from flask.testing import FlaskClient

from tests.conftest import cadastrar_aluno, cadastrar_professor, criar_turma


def test_criar_turma_valida_redireciona_para_turmas(
    cliente_professor: FlaskClient,
) -> None:
    resposta = criar_turma(cliente_professor)

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/professor/turmas")


def test_turma_criada_aparece_com_codigo_de_8_caracteres(
    turma: dict[str, int | str],
) -> None:
    # A fixture `turma` lê o código e o link da turma na página de turmas.
    assert len(turma["codigo"]) == 8


def test_turma_sem_nome_retorna_400(cliente_professor: FlaskClient) -> None:
    resposta = criar_turma(cliente_professor, nome="")

    assert resposta.status_code == 400
    assert "Dê um nome à turma." in resposta.get_data(as_text=True)


@pytest.mark.usefixtures("turma")
def test_turma_com_nome_repetido_do_mesmo_professor_retorna_400(
    cliente_professor: FlaskClient,
) -> None:
    resposta = criar_turma(cliente_professor, nome="2º A")

    assert resposta.status_code == 400
    assert "Você já tem uma turma com esse nome." in resposta.get_data(
        as_text=True
    )


@pytest.mark.usefixtures("turma")
def test_turma_com_mesmo_nome_em_outra_caixa_retorna_400(
    cliente_professor: FlaskClient,
) -> None:
    resposta = criar_turma(cliente_professor, nome="2º a")

    assert resposta.status_code == 400
    assert "Você já tem uma turma com esse nome." in resposta.get_data(
        as_text=True
    )


@pytest.mark.usefixtures("turma")
def test_professores_diferentes_podem_usar_o_mesmo_nome_de_turma(
    app: Flask,
) -> None:
    outro = app.test_client()
    cadastrar_professor(outro, email="prof.bia@escola.br", apelido="Prof. Bia")

    assert criar_turma(outro, nome="2º A").status_code == 302


def test_turmas_diferentes_recebem_codigos_diferentes(
    cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    criar_turma(cliente_professor, nome="3º B")
    html = cliente_professor.get("/professor/turmas").get_data(as_text=True)

    assert html.count('<code class="codigo-turma">') == 2
    assert (
        html.count(f'<code class="codigo-turma">{turma["codigo"]}</code>') == 1
    )


def test_turma_vazia_avisa_que_nao_ha_alunos(
    cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    html = cliente_professor.get(f"/professor/turmas/{turma['id']}").get_data(
        as_text=True
    )

    assert "Nenhum aluno ainda." in html


@pytest.mark.usefixtures("cliente_aluno")
def test_aluno_cadastrado_com_o_codigo_aparece_na_turma(
    cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    html = cliente_professor.get(f"/professor/turmas/{turma['id']}").get_data(
        as_text=True
    )

    assert "Gabriel" in html


@pytest.mark.usefixtures("cliente_aluno")
def test_lista_da_turma_nao_mostra_email_do_aluno(
    cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    html = cliente_professor.get(f"/professor/turmas/{turma['id']}").get_data(
        as_text=True
    )

    assert "gabriel@escola.br" not in html


def test_turma_inexistente_retorna_404(cliente_professor: FlaskClient) -> None:
    assert cliente_professor.get("/professor/turmas/9999").status_code == 404


def test_turma_de_outro_professor_retorna_404(
    app: Flask, turma: dict[str, int | str]
) -> None:
    outro = app.test_client()
    cadastrar_professor(outro, email="prof.bia@escola.br", apelido="Prof. Bia")

    assert outro.get(f"/professor/turmas/{turma['id']}").status_code == 404


def test_aluno_de_outra_turma_nao_aparece(
    app: Flask, cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    criar_turma(cliente_professor, nome="3º B")
    html = cliente_professor.get("/professor/turmas").get_data(as_text=True)
    todos = re.findall(
        r'<code class="codigo-turma">([A-Z0-9]{6,8})</code>', html
    )
    codigo_3b = next(codigo for codigo in todos if codigo != turma["codigo"])
    cadastrar_aluno(
        app.test_client(), codigo_3b, email="bia@escola.br", apelido="Beatriz"
    )

    html_turma = cliente_professor.get(
        f"/professor/turmas/{turma['id']}"
    ).get_data(as_text=True)
    assert "Beatriz" not in html_turma


@pytest.mark.usefixtures("cliente_aluno")
def test_lista_de_turmas_mostra_quantos_alunos_cada_uma_tem(
    app: Flask, cliente_professor: FlaskClient, turma: dict[str, int | str]
) -> None:
    criar_turma(cliente_professor, "3º B")  # sem alunos
    cadastrar_aluno(
        app.test_client(),
        turma["codigo"],
        email="bruno@escola.br",
        apelido="Bruno",
    )

    html = cliente_professor.get("/professor/turmas").get_data(as_text=True)

    assert re.search(r"2º A</strong>\s*<span[^>]*>2 alunos</span>", html)
    assert re.search(r"3º B</strong>\s*<span[^>]*>0 alunos</span>", html)
