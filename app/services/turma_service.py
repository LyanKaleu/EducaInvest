"""Gera código único de turma e valida o nome da turma (RF02)."""
import secrets

from app.services.erros import ErroValidacao
from app.services.formulario import texto_do_campo

# Sem 0/O e 1/I/L, que se confundem ao copiar do quadro ou ditar em sala.
ALFABETO_CODIGO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 6
NOME_MAX = 60


def validar_turma(dados) -> dict:
    nome = texto_do_campo(dados, "nome")
    if not nome:
        raise ErroValidacao({"nome": "Dê um nome à turma."})
    if len(nome) > NOME_MAX:
        raise ErroValidacao({"nome": f"O nome pode ter no máximo {NOME_MAX} caracteres."})
    return {"nome": nome}


def gerar_codigo_turma(aleatorio=None) -> str:
    aleatorio = aleatorio or secrets.SystemRandom()
    return "".join(aleatorio.choice(ALFABETO_CODIGO) for _ in range(TAMANHO_CODIGO))
