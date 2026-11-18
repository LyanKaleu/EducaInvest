"""Proteções da auditoria de segurança: CSRF, headers, cookie e prazo da sessão
(achados 3 a 5).
"""

import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from itsdangerous import TimestampSigner

from app import create_app
from tests.conftest import SENHA, _criar_app

TEMPLATES = Path(__file__).resolve().parents[2] / "app" / "templates"


@pytest.fixture
def cliente_com_csrf(
    tmp_path: Path,
    cliente_professor: FlaskClient,  # noqa: ARG001
) -> FlaskClient:
    """App com CSRF ligado, no banco onde a Prof. Ana já está cadastrada."""
    # `cliente_professor` só cadastra a Prof. Ana antes.
    # Fixture não aceita @pytest.mark.usefixtures, daí o noqa do ARG001.
    return _criar_app(tmp_path, WTF_CSRF_ENABLED=True).test_client()


def token_da_pagina(cliente: FlaskClient, caminho: str) -> str:
    html = cliente.get(caminho).get_data(as_text=True)
    encontrado = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert encontrado, f"a página {caminho} deve ter o campo csrf_token"
    return encontrado.group(1)


def logado(cliente: FlaskClient) -> bool:
    return cliente.get("/professor/turmas").status_code == 200


# ---------------------------------------------------------------------------
# CSRF (achado 3)
# ---------------------------------------------------------------------------


def test_login_sem_token_csrf_nao_entra(cliente_com_csrf: FlaskClient) -> None:
    resposta = cliente_com_csrf.post(
        "/login", data={"email": "prof.ana@escola.br", "senha": SENHA}
    )

    assert resposta.status_code == 302
    assert not logado(cliente_com_csrf)


def test_login_com_token_de_outra_sessao_nao_entra(
    cliente_com_csrf: FlaskClient, tmp_path: Path
) -> None:
    outro = _criar_app(tmp_path, WTF_CSRF_ENABLED=True).test_client()
    token_alheio = token_da_pagina(outro, "/login")

    cliente_com_csrf.get("/login")
    cliente_com_csrf.post(
        "/login",
        data={
            "email": "prof.ana@escola.br",
            "senha": SENHA,
            "csrf_token": token_alheio,
        },
    )

    assert not logado(cliente_com_csrf)


def test_token_invalido_avisa_que_a_pagina_expirou(
    cliente_com_csrf: FlaskClient,
) -> None:
    resposta = cliente_com_csrf.post(
        "/login",
        follow_redirects=True,
        data={"email": "prof.ana@escola.br", "senha": SENHA},
    )

    assert (
        "A página expirou. Envie o formulário de novo."
        in resposta.get_data(as_text=True)
    )


def test_login_com_o_token_da_pagina_entra(
    cliente_com_csrf: FlaskClient,
) -> None:
    token = token_da_pagina(cliente_com_csrf, "/login")

    resposta = cliente_com_csrf.post(
        "/login",
        data={
            "email": "prof.ana@escola.br",
            "senha": SENHA,
            "csrf_token": token,
        },
    )

    assert resposta.status_code == 302
    assert logado(cliente_com_csrf)


def formularios_post() -> Iterator[tuple[str, str]]:
    """(arquivo, trecho) de cada <form method="post"> dos templates."""
    for arquivo in sorted(TEMPLATES.rglob("*.html")):
        texto = arquivo.read_text(encoding="utf-8")
        for form in re.findall(
            r"<form\b[^>]*>.*?</form>", texto, flags=re.DOTALL
        ):
            if re.search(
                r'method="post"', form.split(">", 1)[0], flags=re.IGNORECASE
            ):
                yield arquivo.relative_to(TEMPLATES).as_posix(), form


def test_os_templates_tem_formularios_post() -> None:
    # Guarda do meta-teste abaixo: se o regex parar de achar formulários, ele
    # passaria vazio.
    assert len(list(formularios_post())) >= 9


def test_todo_formulario_post_tem_csrf_token() -> None:
    sem_token = [
        arquivo
        for arquivo, form in formularios_post()
        if "csrf_token()" not in form
    ]

    assert sem_token == [], f"formulário POST sem csrf_token: {sem_token}"


# ---------------------------------------------------------------------------
# Cookie e headers de produção (achado 4)
# ---------------------------------------------------------------------------


def test_resposta_tem_headers_de_seguranca(
    cliente_anonimo: FlaskClient,
) -> None:
    headers = cliente_anonimo.get("/login").headers

    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert (
        headers["Content-Security-Policy"]
        == "default-src 'self'; frame-ancestors 'none'"
    )


def cookie_de_sessao(config: dict[str, object], tmp_path: Path) -> str:
    """Set-Cookie da sessão criada ao abrir o login (o token CSRF vai para a
    sessão).
    """
    app = create_app(
        {"SECRET_KEY": "chave", "DATABASE": str(tmp_path / "x.db"), **config}
    )
    resposta = app.test_client().get("/login")
    return next(
        v
        for v in resposta.headers.getlist("Set-Cookie")
        if v.startswith("session=")
    )


def test_cookie_de_sessao_so_viaja_por_https_fora_de_debug(
    tmp_path: Path,
) -> None:
    assert "; Secure" in cookie_de_sessao({}, tmp_path)


def test_cookie_de_sessao_funciona_por_http_em_debug(tmp_path: Path) -> None:
    # O servidor de desenvolvimento é http://127.0.0.1: com Secure, o login não
    # funcionaria.
    assert "; Secure" not in cookie_de_sessao({"DEBUG": True}, tmp_path)


# ---------------------------------------------------------------------------
# Prazo da sessão (achado 5)
# ---------------------------------------------------------------------------


def adiantar_relogio_da_sessao(
    monkeypatch: pytest.MonkeyPatch, horas: int
) -> None:
    """Relógio do cookie assinado (itsdangerous) `horas` à frente: a fronteira
    de tempo.
    """
    agora = TimestampSigner.get_timestamp(None)
    monkeypatch.setattr(
        TimestampSigner, "get_timestamp", lambda _self: agora + horas * 3600
    )


def test_sessao_com_11_horas_continua_valendo(
    monkeypatch: pytest.MonkeyPatch, cliente_professor: FlaskClient
) -> None:
    adiantar_relogio_da_sessao(monkeypatch, 11)

    assert cliente_professor.get("/professor/turmas").status_code == 200


def test_sessao_com_mais_de_12_horas_volta_para_o_login(
    monkeypatch: pytest.MonkeyPatch, cliente_professor: FlaskClient
) -> None:
    adiantar_relogio_da_sessao(monkeypatch, 13)

    resposta = cliente_professor.get("/professor/turmas")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")
