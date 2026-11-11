"""Painel da turma do professor: XP médio, missões, frequência e linha por aluno (HU5, RN-18)."""
import re
import uuid

from tests.conftest import cadastrar_aluno, criar_turma


def registrar_gasto(cliente, valor="25,00"):
    """Cria um gasto pela rota, como o navegador envia. Rende 10 XP."""
    form = {"tipo": "saida", "categoria": "Alimentação", "valor": valor, "data": "2026-11-01",
            "descricao": "", "chave_idempotencia": str(uuid.uuid4())}
    resposta = cliente.post("/lancamentos/novo", data=form)
    assert resposta.status_code == 302, "o gasto deve ser salvo"


def painel_da_turma(cliente_professor, turma):
    resposta = cliente_professor.get(f"/professor/turmas/{turma['id']}")
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def valor(html, id_):
    """Texto do elemento com `id_` na tela, sem espaços nas pontas."""
    encontrado = re.search(rf'id="{id_}"[^>]*>([^<]*)<', html)
    assert encontrado, f"a tela deve ter o elemento #{id_}"
    return encontrado.group(1).strip()


def test_painel_mostra_xp_medio_missoes_e_ativos(cliente_professor, turma, cliente_aluno,
                                                 cliente_outro_aluno):
    # Gabriel: 3 gastos x 10 XP + 30 XP da missão "Primeiros passos" = 60 XP.
    # Beatriz não registra nada: 0 XP. Média (60 + 0) / 2 = 30.
    for _ in range(3):
        registrar_gasto(cliente_aluno)

    html = painel_da_turma(cliente_professor, turma)

    assert valor(html, "total-alunos") == "2"
    assert valor(html, "xp-medio") == "30 XP"
    assert valor(html, "missoes-concluidas") == "1"
    assert valor(html, "ativos-semana") == "1 de 2"


def test_painel_nao_mostra_valores_em_reais(cliente_professor, turma, cliente_aluno):
    registrar_gasto(cliente_aluno, valor="37,90")

    html = painel_da_turma(cliente_professor, turma)

    assert "R$" not in html
    assert "37,90" not in html


def test_aluno_de_outra_turma_nao_entra_na_media(app, cliente_professor, turma, cliente_aluno):
    criar_turma(cliente_professor, nome="3º B")
    html_turmas = cliente_professor.get("/professor/turmas").get_data(as_text=True)
    codigos = re.findall(r'<code class="codigo-turma">([A-Z0-9]{6})</code>', html_turmas)
    codigo_3b = next(codigo for codigo in codigos if codigo != turma["codigo"])
    de_outra_turma = app.test_client()
    assert cadastrar_aluno(de_outra_turma, codigo_3b, email="caio@escola.br",
                           apelido="Caio").status_code == 302
    registrar_gasto(de_outra_turma)

    html = painel_da_turma(cliente_professor, turma)

    assert valor(html, "total-alunos") == "1"
    assert valor(html, "xp-medio") == "0 XP"
    assert valor(html, "ativos-semana") == "0 de 1"
    # O XP do Caio existe, só que na turma dele.
    turma_3b_id = max(int(i) for i in re.findall(r'href="/professor/turmas/(\d+)"', html_turmas))
    assert valor(painel_da_turma(cliente_professor, {"id": turma_3b_id}), "xp-medio") == "10 XP"


def test_tabela_mostra_cada_aluno_sem_email(cliente_professor, turma, cliente_aluno):
    for _ in range(3):
        registrar_gasto(cliente_aluno)

    html = painel_da_turma(cliente_professor, turma)

    linha = re.search(r"<tr>\s*<th scope=\"row\">Gabriel</th>(.*?)</tr>", html, re.S)
    assert linha, "a tabela deve ter a linha do Gabriel"
    celulas = [c.strip() for c in re.findall(r"<td[^>]*>([^<]*)</td>", linha.group(1))]
    assert celulas == ["Iniciante", "60", "1", "Sim"]
    assert "gabriel@escola.br" not in html


def test_tabela_fica_em_ordem_de_apelido_sem_diferenciar_maiusculas(app, cliente_professor, turma,
                                                                    cliente_aluno):
    # Ordem binária poria "Gabriel" antes de "bruno"; a tabela não é ranking, é alfabética.
    resposta = cadastrar_aluno(app.test_client(), turma["codigo"], email="bruno@escola.br",
                               apelido="bruno")
    assert resposta.status_code == 302

    html = painel_da_turma(cliente_professor, turma)

    assert re.findall(r'<th scope="row">([^<]*)</th>', html) == ["bruno", "Gabriel"]
