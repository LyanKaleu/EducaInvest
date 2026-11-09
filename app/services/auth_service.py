"""Valida cadastro e login, faz hash de senha e controla o acesso por perfil (RNF04)."""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.services.erros import ErroValidacao
from app.services.formulario import texto_do_campo

PERFIL_ALUNO = "ALUNO"
PERFIL_PROFESSOR = "PROFESSOR"

APELIDO_MIN, APELIDO_MAX = 2, 40
SENHA_MIN, SENHA_MAX = 8, 128
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CODIGO_RE = re.compile(r"[A-Z0-9]{6,8}")

# Algoritmo do hash de senha (o padrão do Werkzeug). Os testes trocam por um
# mais rápido; em produção fica sempre o scrypt, lento de propósito.
METODO_HASH = "scrypt"


def validar_cadastro_aluno(dados) -> dict:
    erros = {}
    resultado = _validar_conta(dados, erros)

    codigo = texto_do_campo(dados, "codigo_turma").upper()
    if not codigo:
        erros["codigo_turma"] = "Informe o código da turma."
    elif not CODIGO_RE.fullmatch(codigo):
        erros["codigo_turma"] = "Código de turma inválido."

    if dados.get("consentimento") != "sim":
        erros["consentimento"] = "Você precisa confirmar a autorização para continuar."

    if erros:
        raise ErroValidacao(erros)
    return {**resultado, "codigo_turma": codigo}


def validar_cadastro_professor(dados) -> dict:
    erros = {}
    resultado = _validar_conta(dados, erros)
    if erros:
        raise ErroValidacao(erros)
    return resultado


def validar_login(dados) -> dict:
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
    return generate_password_hash(senha, method=METODO_HASH)


def senha_confere(hash_senha: str, senha: str) -> bool:
    return check_password_hash(hash_senha, senha)


def _validar_conta(dados, erros) -> dict:
    """Campos comuns a aluno e professor: apelido, e-mail e senha."""
    apelido = texto_do_campo(dados, "apelido")
    email = texto_do_campo(dados, "email").lower()
    senha = dados.get("senha") or ""  # senha não é aparada: espaços fazem parte dela

    if not APELIDO_MIN <= len(apelido) <= APELIDO_MAX:
        erros["apelido"] = f"Informe um apelido de {APELIDO_MIN} a {APELIDO_MAX} caracteres."
    if not EMAIL_RE.fullmatch(email):
        erros["email"] = "Informe um e-mail válido."
    if len(senha) < SENHA_MIN:
        erros["senha"] = f"A senha precisa ter pelo menos {SENHA_MIN} caracteres."
    elif len(senha) > SENHA_MAX:
        erros["senha"] = f"A senha pode ter no máximo {SENHA_MAX} caracteres."

    return {"apelido": apelido, "email": email, "senha": senha}
