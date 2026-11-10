"""Tela inicial do aluno: saldo, XP, nível, sequência e missão em andamento (HU1 saldo, HU3 RN-13)."""
import re
import uuid


def registrar(cliente, tipo, categoria, valor):
    """Cria um lançamento pela rota, como o navegador envia."""
    form = {"tipo": tipo, "categoria": categoria, "valor": valor, "data": "2026-11-01",
            "descricao": "", "chave_idempotencia": str(uuid.uuid4())}
    cliente.post("/lancamentos/novo", data=form)


def painel(cliente):
    resposta = cliente.get("/painel/")
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def valor(html, id_):
    """Texto do elemento com `id_` na tela (ex.: o saldo), sem espaços nas pontas."""
    encontrado = re.search(rf'id="{id_}"[^>]*>([^<]*)<', html)
    assert encontrado, f"a tela deve ter o elemento #{id_}"
    return encontrado.group(1).strip()


def test_painel_mostra_saldo_xp_sequencia_e_missao(cliente_aluno):
    registrar(cliente_aluno, "entrada", "Mesada", "50,00")
    registrar(cliente_aluno, "saida", "Alimentação", "25,00")

    html = painel(cliente_aluno)

    assert valor(html, "saldo") == "R$ 25,00"
    assert valor(html, "xp-total") == "20 XP"
    assert valor(html, "sequencia") == "1 dia"
    assert valor(html, "missao-progresso") == "Primeiros passos: 1 de 3"


def test_saldo_nao_inclui_lancamentos_de_outro_aluno(cliente_aluno, cliente_outro_aluno):
    registrar(cliente_outro_aluno, "entrada", "Mesada", "80,00")
    registrar(cliente_aluno, "saida", "Lazer", "10,50")

    assert valor(painel(cliente_aluno), "saldo") == "-R$ 10,50"


def test_aluno_novo_ve_painel_zerado(cliente_aluno):
    html = painel(cliente_aluno)

    assert valor(html, "saldo") == "R$ 0,00"
    assert valor(html, "xp-total") == "0 XP"
    assert valor(html, "sequencia") == "0 dias"
    assert valor(html, "missao-progresso") == "Primeiros passos: 0 de 3"


def test_inicio_do_aluno_abre_o_painel(cliente_aluno):
    resposta = cliente_aluno.get("/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/painel/")
