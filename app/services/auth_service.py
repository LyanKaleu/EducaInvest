"""Valida cadastro e login, faz hash de senha e controla o acesso por perfil (RNF04)."""

import re
from collections.abc import Mapping
from typing import override

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.base import HasherProtocol
from werkzeug.security import check_password_hash

from app.services.erros import ErroValidacao
from app.services.formulario import texto_do_campo

PERFIL_ALUNO = "ALUNO"
PERFIL_PROFESSOR = "PROFESSOR"

APELIDO_MIN, APELIDO_MAX = 2, 40
SENHA_MIN, SENHA_MAX = 8, 128
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CODIGO_RE = re.compile(r"[A-Z0-9]{6,8}")


class HasherLegadoWerkzeug(HasherProtocol):
    """Confere os hashes antigos do Werkzeug (scrypt), de antes do Argon2id. Nunca gera hash.

    Pega tudo o que não é Argon2: formato desconhecido cai no check_password_hash, que
    responde False em vez de derrubar o login.
    """

    # Os nomes dos parâmetros (inclusive `hash`) vêm do HasherProtocol do pwdlib.
    @classmethod
    @override
    def identify(cls, hash: str | bytes) -> bool:
        return not Argon2Hasher.identify(hash)

    @override
    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
        raise NotImplementedError("hash novo é sempre Argon2id")

    @override
    def verify(self, password: str | bytes, hash: str | bytes) -> bool:
        return check_password_hash(hash, password)

    @override
    def check_needs_rehash(self, hash: str | bytes) -> bool:
        return True


# Hash de senha: Argon2id com os parâmetros padrão do argon2-cffi (t=3, 64 MiB, p=4),
# lento de propósito. O legado só confere, e o login regrava o hash em Argon2id.
# Os testes trocam por um Argon2id barato (tests/conftest.py).
SENHAS = PasswordHash((Argon2Hasher(), HasherLegadoWerkzeug()))


def validar_cadastro_aluno(dados: Mapping[str, str]) -> dict:
    """Valida o cadastro do aluno e devolve os dados normalizados."""
    erros = {}
    resultado = _validar_conta(dados, erros)

    codigo = texto_do_campo(dados, "codigo_turma").upper()
    if not codigo:
        erros["codigo_turma"] = "Informe o código da turma."
    elif not CODIGO_RE.fullmatch(codigo):
        erros["codigo_turma"] = "Código de turma inválido."

    if dados.get("consentimento") != "sim":
        erros["consentimento"] = (
            "Você precisa confirmar a autorização para continuar."
        )

    if erros:
        raise ErroValidacao(erros)
    return {**resultado, "codigo_turma": codigo}


def validar_cadastro_professor(dados: Mapping[str, str]) -> dict:
    """Valida o cadastro do professor e devolve os dados normalizados."""
    erros = {}
    resultado = _validar_conta(dados, erros)
    if erros:
        raise ErroValidacao(erros)
    return resultado


def validar_login(dados: Mapping[str, str]) -> dict:
    """Valida o formulário de login e devolve e-mail e senha."""
    email = texto_do_campo(dados, "email").lower()
    senha = dados.get("senha") or ""
    erros = {}
    if not email:
        erros["email"] = "Informe seu e-mail."
    if not senha:
        erros["senha"] = "Informe sua senha."
    if erros:
        raise ErroValidacao(erros)
    return {"email": email, "senha": senha}


def gerar_hash_senha(senha: str) -> str:
    """Gera o hash Argon2id da senha."""
    return SENHAS.hash(senha)


def conferir_senha(hash_senha: str, senha: str) -> tuple[bool, str | None]:
    """(a senha confere?, hash novo para gravar ou None).

    O hash novo só vem quando a senha confere e o hash guardado está num formato antigo
    ou com parâmetros desatualizados. Uma verificação só: o Argon2 é lento de propósito.
    """
    return SENHAS.verify_and_update(senha, hash_senha)


def _validar_conta(dados: Mapping[str, str], erros: dict[str, str]) -> dict:
    """Campos comuns a aluno e professor: apelido, e-mail e senha."""
    apelido = texto_do_campo(dados, "apelido")
    email = texto_do_campo(dados, "email").lower()
    senha = (
        dados.get("senha") or ""
    )  # senha não é aparada: espaços fazem parte dela

    if not APELIDO_MIN <= len(apelido) <= APELIDO_MAX:
        erros["apelido"] = (
            f"Informe um apelido de {APELIDO_MIN} a {APELIDO_MAX} caracteres."
        )
    if not EMAIL_RE.fullmatch(email):
        erros["email"] = "Informe um e-mail válido."
    if len(senha) < SENHA_MIN:
        erros["senha"] = (
            f"A senha precisa ter pelo menos {SENHA_MIN} caracteres."
        )
    elif len(senha) > SENHA_MAX:
        erros["senha"] = f"A senha pode ter no máximo {SENHA_MAX} caracteres."

    return {"apelido": apelido, "email": email, "senha": senha}
