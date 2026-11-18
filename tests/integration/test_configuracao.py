"""Configuração segura do app: os 2 bloqueantes da revisão (SECRET_KEY e aluno de demonstração)."""
from pathlib import Path

import pytest

from app import create_app


def test_app_fora_de_teste_e_debug_sem_secret_key_nao_inicia(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"DATABASE": str(tmp_path / "x.db")})


def test_app_em_debug_inicia_sem_secret_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)

    assert create_app({"DEBUG": True, "DATABASE": str(tmp_path / "x.db")}).secret_key


def test_app_usa_a_secret_key_do_ambiente(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SECRET_KEY", "chave-do-ambiente")

    assert create_app({"DATABASE": str(tmp_path / "x.db")}).secret_key == "chave-do-ambiente"


def test_aluno_de_demonstracao_nao_libera_mais_o_acesso(tmp_path: Path) -> None:
    app = create_app({"TESTING": True, "SECRET_KEY": "t", "ALUNO_DEMO_ID": 1,
                      "DATABASE": str(tmp_path / "x.db")})

    resposta = app.test_client().get("/lancamentos/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")
