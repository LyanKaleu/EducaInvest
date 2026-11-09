"""Meta-teste de acesso (RNF04): toda rota nova nasce protegida, sem depender de alguém lembrar.

Percorre o mapa de rotas do app em vez de listar URLs à mão: rota criada amanhã
entra na verificação sozinha. Rota pública só passa se estiver em ROTAS_PUBLICAS.
"""
import pytest
from flask import url_for

from app import create_app
from tests.conftest import entrar

# Rotas que qualquer visitante pode abrir. Entrar aqui é decisão explícita, nunca esquecimento.
ROTAS_PUBLICAS = {
    "static",
    "auth.cadastro", "auth.cadastrar_aluno",
    "auth.cadastro_professor", "auth.cadastrar_professor",
    "auth.login", "auth.entrar",
}

# Rotas para qualquer usuário logado, sem perfil específico.
ROTAS_DE_QUALQUER_PERFIL = {"inicio", "auth.sair"}


def _requisicoes(app, ignorar):
    """Lista (método, url) de cada rota fora de `ignorar`, com 1 em todo parâmetro da URL."""
    requisicoes = []
    with app.test_request_context():
        for regra in app.url_map.iter_rules():
            if regra.endpoint in ignorar:
                continue
            url = url_for(regra.endpoint, **{parametro: 1 for parametro in regra.arguments})
            for metodo in sorted(regra.methods - {"HEAD", "OPTIONS"}):
                requisicoes.append((metodo, url))
    return requisicoes


def _abrir(cliente, metodo, url):
    """Faz a requisição e devolve (status, Location). Exceção no handler vira status "erro"."""
    try:
        resposta = cliente.open(url, method=metodo)
    except Exception as erro:  # rota sem proteção costuma quebrar ao ler a sessão vazia
        return f"erro {type(erro).__name__}", ""
    return resposta.status_code, resposta.headers.get("Location", "")


def rotas_abertas_a_visitante(app):
    """Rotas não públicas que um visitante sem login consegue usar (devia ir para /login)."""
    cliente = app.test_client()
    abertas = []
    for metodo, url in _requisicoes(app, ignorar=ROTAS_PUBLICAS):
        status, destino = _abrir(cliente, metodo, url)
        if not (status == 302 and destino.endswith("/login")):
            abertas.append(f"{metodo} {url} -> {status}")
    return abertas


def rotas_sem_perfil_definido(cliente_aluno, cliente_professor, app):
    """Rotas restritas em que aluno e professor não são separados (403 para exatamente um)."""
    misturadas = []
    ignorar = ROTAS_PUBLICAS | ROTAS_DE_QUALQUER_PERFIL
    for metodo, url in _requisicoes(app, ignorar=ignorar):
        recusou_aluno = _abrir(cliente_aluno, metodo, url)[0] == 403
        recusou_professor = _abrir(cliente_professor, metodo, url)[0] == 403
        if recusou_aluno == recusou_professor:
            misturadas.append(f"{metodo} {url}")
    return misturadas


def test_toda_rota_nao_publica_manda_visitante_para_o_login(app):
    assert rotas_abertas_a_visitante(app) == []


def test_toda_rota_restrita_aceita_um_perfil_e_recusa_o_outro(app, cliente_aluno, cliente_professor):
    assert rotas_sem_perfil_definido(cliente_aluno, cliente_professor, app) == []


def test_meta_teste_acusa_rota_nova_esquecida_sem_protecao(app):
    # Prova de que o meta-teste morde: uma rota sem verificação precisa aparecer.
    app.add_url_rule("/rota-esquecida", "rota_esquecida", lambda: "dados")

    assert "GET /rota-esquecida -> 200" in rotas_abertas_a_visitante(app)


@pytest.mark.usefixtures("cliente_aluno", "cliente_professor")  # só para cadastrar os dois
def test_meta_teste_acusa_rota_que_qualquer_perfil_abre(app):
    # Os fixtures já fizeram requisições no `app`, que não aceita mais rotas novas.
    # Um segundo app no MESMO banco reaproveita o aluno e o professor cadastrados.
    outro_app = create_app({**app.config})
    outro_app.add_url_rule("/so-com-login", "so_com_login", lambda: "dados")
    aluno, professor = outro_app.test_client(), outro_app.test_client()
    entrar(aluno, "gabriel@escola.br")
    entrar(professor, "prof.ana@escola.br")

    assert "GET /so-com-login" in rotas_sem_perfil_definido(aluno, professor, outro_app)
