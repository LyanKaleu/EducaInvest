"""Escolha do perfil no cadastro e identificação de quem está logado (RF01, usabilidade).

Padrão de mercado (Google Classroom, Khan Academy, Upwork): o tipo de usuário é
escolhido no cadastro, o login é um só, e depois de entrar a tela mostra o perfil.
"""
import re

from tests.conftest import cadastrar_aluno, entrar


def opcao(html, texto):
    """A tag <a> da opção de perfil com o `texto` dado, ou None."""
    encontrado = re.search(rf'<a [^>]*>\s*{texto}\s*</a>', html)
    return encontrado.group(0) if encontrado else None


# ---------------------------------------------------------------------------
# Cadastro: escolha clara entre aluno e professor
# ---------------------------------------------------------------------------

def test_cadastro_de_aluno_oferece_as_duas_opcoes_com_aluno_marcado(cliente_anonimo):
    html = cliente_anonimo.get("/cadastro").get_data(as_text=True)

    aluno, professor = opcao(html, "Sou aluno"), opcao(html, "Sou professor")
    assert aluno and 'href="/cadastro"' in aluno and 'aria-current="page"' in aluno
    assert professor and 'href="/cadastro/professor"' in professor
    assert 'aria-current="page"' not in professor


def test_cadastro_de_professor_marca_a_opcao_professor(cliente_anonimo):
    html = cliente_anonimo.get("/cadastro/professor").get_data(as_text=True)

    assert 'aria-current="page"' in opcao(html, "Sou professor")
    assert 'aria-current="page"' not in opcao(html, "Sou aluno")


# ---------------------------------------------------------------------------
# Login: um só para todos
# ---------------------------------------------------------------------------

def test_login_avisa_que_alunos_e_professores_entram_pelo_mesmo_lugar(cliente_anonimo):
    html = cliente_anonimo.get("/login").get_data(as_text=True)

    assert "Alunos e professores entram por aqui" in html


# ---------------------------------------------------------------------------
# Topo: quem está logado e com qual perfil
# ---------------------------------------------------------------------------

def test_topo_mostra_apelido_e_perfil_do_aluno(cliente_aluno):
    html = cliente_aluno.get("/lancamentos/").get_data(as_text=True)

    assert '<span class="identificacao">Gabriel · Aluno</span>' in html


def test_topo_mostra_apelido_e_perfil_do_professor(cliente_professor):
    html = cliente_professor.get("/professor/turmas").get_data(as_text=True)

    assert '<span class="identificacao">Prof. Ana · Professor</span>' in html


def test_topo_identifica_quem_entrou_pelo_login(app, cliente_aluno):
    cliente = app.test_client()
    entrar(cliente, "gabriel@escola.br")

    html = cliente.get("/lancamentos/").get_data(as_text=True)

    assert '<span class="identificacao">Gabriel · Aluno</span>' in html


def test_visitante_nao_ve_identificacao(cliente_anonimo):
    html = cliente_anonimo.get("/login").get_data(as_text=True)

    assert 'class="identificacao"' not in html


def test_apelido_no_topo_nao_executa_html(app, turma):
    cliente = app.test_client()
    cadastrar_aluno(cliente, turma["codigo"], email="x@escola.br", apelido="<b>Zé</b>")

    html = cliente.get("/lancamentos/").get_data(as_text=True)

    assert "<b>Zé</b>" not in html
    assert '<span class="identificacao">&lt;b&gt;Zé&lt;/b&gt; · Aluno</span>' in html


def test_sessao_antiga_sem_apelido_mostra_so_o_perfil(cliente_aluno):
    # Quem entrou antes desta versão não tem apelido na sessão: nada de "None · Aluno".
    with cliente_aluno.session_transaction() as sessao:
        sessao.pop("apelido")

    html = cliente_aluno.get("/lancamentos/").get_data(as_text=True)

    assert '<span class="identificacao">Aluno</span>' in html
    assert "None" not in html
