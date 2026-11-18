"""Testes das rotas de metas e aportes (HU2) com banco SQLite temporário (tmp_path)."""
import re
import sqlite3
import uuid

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app.repositories.meta_repo import MetaRepository


def criar_meta(
    cliente: FlaskClient,
    nome: str = "Fone",
    alvo: str = "200,00",
    prazo: str = "",
    chave: str | None = None,
) -> TestResponse:
    return cliente.post("/metas/nova", data={
        "nome": nome, "alvo": alvo, "prazo": prazo,
        "chave_idempotencia": chave or str(uuid.uuid4()),
    })


def lista(cliente: FlaskClient) -> str:
    return cliente.get("/metas/").get_data(as_text=True)


def aportar(
    cliente: FlaskClient, meta_id: int, valor: str, chave: str | None = None
) -> TestResponse:
    return cliente.post(f"/metas/{meta_id}/aportes", data={
        "valor": valor, "chave_idempotencia": chave or str(uuid.uuid4()),
    })


@pytest.fixture
def meta_fone(cliente: FlaskClient) -> int:
    """Meta "Fone" de R$ 200,00 do aluno logado, criada pela rota. Devolve o id."""
    criar_meta(cliente, "Fone", "200,00")
    encontrado = re.search(r'data-meta-id="(\d+)"', lista(cliente))
    assert encontrado, "a meta criada deve aparecer na lista"
    return int(encontrado.group(1))


# ---------------------------------------------------------------------------
# Criar meta
# ---------------------------------------------------------------------------

def test_meta_criada_aparece_com_0_por_cento(cliente: FlaskClient) -> None:
    resposta = criar_meta(cliente, "Fone", "200,00")

    assert resposta.status_code == 302
    html = lista(cliente)
    assert "Fone" in html
    assert "R$ 0,00 de R$ 200,00 · 0%" in html


def test_meta_sem_nome_e_com_alvo_zero_retorna_400_e_nao_cria(cliente: FlaskClient) -> None:
    resposta = criar_meta(cliente, nome="", alvo="0", prazo="2026-12-20")

    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert "Dê um nome para a meta." in html
    assert "O valor precisa ser maior que zero." in html
    assert 'value="2026-12-20"' in html  # o que foi digitado continua lá
    assert "Você ainda não tem metas" in lista(cliente)


def test_meta_com_prazo_no_passado_retorna_400_e_nao_cria(cliente: FlaskClient) -> None:
    resposta = criar_meta(cliente, prazo="2020-01-01")

    assert resposta.status_code == 400
    assert "O prazo não pode ser no passado." in resposta.get_data(as_text=True)
    assert "Você ainda não tem metas" in lista(cliente)


# ---------------------------------------------------------------------------
# Aportes
# ---------------------------------------------------------------------------

def test_aporte_leva_a_meta_a_50_por_cento(cliente: FlaskClient, meta_fone: int) -> None:
    aportar(cliente, meta_fone, "50,00")

    resposta = aportar(cliente, meta_fone, "50,00")

    assert resposta.status_code == 302
    assert "R$ 100,00 de R$ 200,00 · 50%" in lista(cliente)


def test_meta_em_andamento_tem_formulario_de_aporte(cliente: FlaskClient, meta_fone: int) -> None:
    assert f'action="/metas/{meta_fone}/aportes"' in lista(cliente)


def test_aporte_que_completa_o_alvo_conclui_a_meta(cliente: FlaskClient, meta_fone: int) -> None:
    aportar(cliente, meta_fone, "190,00")

    resposta = aportar(cliente, meta_fone, "10,00")

    assert resposta.status_code == 302
    html = lista(cliente)
    assert "R$ 200,00 de R$ 200,00 · 100%" in html
    assert "Concluída" in html
    assert f'action="/metas/{meta_fone}/aportes"' not in html


def test_aporte_que_completa_a_meta_parabeniza_o_aluno(cliente: FlaskClient, meta_fone: int) -> None:
    resposta = cliente.post(f"/metas/{meta_fone}/aportes", follow_redirects=True,
                            data={"valor": "200,00", "chave_idempotencia": str(uuid.uuid4())})

    assert "Parabéns, você concluiu a meta Fone!" in resposta.get_data(as_text=True)


def test_meta_concluida_recusa_novo_aporte(cliente: FlaskClient, meta_fone: int) -> None:
    aportar(cliente, meta_fone, "200,00")

    resposta = aportar(cliente, meta_fone, "10,00")

    assert resposta.status_code == 400
    assert "Essa meta já foi concluída." in resposta.get_data(as_text=True)
    assert "R$ 200,00 de R$ 200,00 · 100%" in lista(cliente)


def test_aporte_acima_do_que_falta_retorna_400_e_a_meta_nao_conclui(cliente: FlaskClient, meta_fone: int) -> None:
    # Sem resgate nem exclusão de aporte, um dígito a mais fecharia a meta para sempre.
    aportar(cliente, meta_fone, "170,00")
    chave = str(uuid.uuid4())

    resposta = aportar(cliente, meta_fone, "100.000,00", chave=chave)

    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert (f'<p class="erro-campo" id="erro-valor-{meta_fone}">'
            "Faltam só R$ 30,00 para concluir esta meta. Guarde até esse valor.</p>") in html
    # O digitado volta no formulário, com a mesma chave: nada foi gravado.
    assert 'value="100.000,00"' in html
    assert f'value="{chave}"' in html
    assert "R$ 170,00 de R$ 200,00 · 85%" in lista(cliente)


@pytest.mark.parametrize("valor", ["0", "-10,00"])
def test_aporte_zero_ou_negativo_retorna_400_e_o_progresso_nao_muda(cliente: FlaskClient, meta_fone: int, valor: str) -> None:
    aportar(cliente, meta_fone, "50,00")

    resposta = aportar(cliente, meta_fone, valor)

    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert f'<p class="erro-campo" id="erro-valor-{meta_fone}">O valor precisa ser maior que zero.</p>' in html
    assert "R$ 50,00 de R$ 200,00 · 25%" in lista(cliente)


# ---------------------------------------------------------------------------
# Acesso (N1): meta de outro aluno é invisível e responde 404
# ---------------------------------------------------------------------------

def test_aporte_em_meta_de_outro_aluno_retorna_404_e_nao_muda_nada(cliente: FlaskClient, meta_fone: int, cliente_outro_aluno: FlaskClient) -> None:
    resposta = aportar(cliente_outro_aluno, meta_fone, "50,00")

    assert resposta.status_code == 404
    assert "R$ 0,00 de R$ 200,00 · 0%" in lista(cliente)


@pytest.mark.usefixtures("meta_fone")
def test_lista_nao_mostra_metas_de_outro_aluno(cliente_outro_aluno: FlaskClient) -> None:
    assert "Você ainda não tem metas" in lista(cliente_outro_aluno)


def test_aporte_em_meta_inexistente_retorna_404(cliente: FlaskClient) -> None:
    assert aportar(cliente, 999, "50,00").status_code == 404


# ---------------------------------------------------------------------------
# Reenvio (N2): o mesmo envio grava uma vez só
# ---------------------------------------------------------------------------

def test_reenvio_da_meta_com_a_mesma_chave_nao_duplica(cliente: FlaskClient) -> None:
    chave = str(uuid.uuid4())
    criar_meta(cliente, "Fone", "200,00", chave=chave)

    resposta = criar_meta(cliente, "Fone", "200,00", chave=chave)

    assert resposta.status_code == 302
    assert lista(cliente).count("data-meta-id=") == 1


def test_reenvio_do_aporte_com_a_mesma_chave_nao_duplica(cliente: FlaskClient, meta_fone: int) -> None:
    chave = str(uuid.uuid4())
    aportar(cliente, meta_fone, "50,00", chave=chave)

    resposta = aportar(cliente, meta_fone, "50,00", chave=chave)

    assert resposta.status_code == 302
    assert "R$ 50,00 de R$ 200,00 · 25%" in lista(cliente)


def test_reenvio_do_aporte_que_concluiu_a_meta_responde_como_sucesso(cliente: FlaskClient, meta_fone: int) -> None:
    # Clique duplo no aporte que completa o alvo: o 2º envio não pode virar "meta já concluída".
    aportar(cliente, meta_fone, "190,00")
    chave = str(uuid.uuid4())
    aportar(cliente, meta_fone, "10,00", chave=chave)

    resposta = aportar(cliente, meta_fone, "10,00", chave=chave)

    assert resposta.status_code == 302
    assert "R$ 200,00 de R$ 200,00 · 100%" in lista(cliente)


def test_reenvio_do_aporte_com_a_chave_em_maiusculas_responde_como_sucesso(cliente: FlaskClient, meta_fone: int) -> None:
    # A chave é gravada normalizada (minúsculas): o reenvio precisa ser reconhecido em outra grafia.
    aportar(cliente, meta_fone, "190,00")
    chave = str(uuid.uuid4()).upper()
    aportar(cliente, meta_fone, "10,00", chave=chave)

    resposta = aportar(cliente, meta_fone, "10,00", chave=chave)

    assert resposta.status_code == 302
    assert "R$ 200,00 de R$ 200,00 · 100%" in lista(cliente)


# ---------------------------------------------------------------------------
# Corrida: outro aporte é gravado entre a conferência da rota e o INSERT (auditoria, achado 7)
# ---------------------------------------------------------------------------

def aporte_concorrente_depois_da_conferencia(monkeypatch: pytest.MonkeyPatch, app: Flask, meta_id: int, centavos: int, chave: str) -> None:
    """Na 1ª conferência de reenvio, outra requisição grava e commita um aporte nesta meta.

    Simula a corrida real: a rota já leu o "guardado" e conferiu o limite, mas o
    INSERT dela ainda não rodou. O outro aporte entra por outra conexão, como
    entraria por outro processo.
    """
    original = MetaRepository.aporte_registrado
    disparou = []

    def conferir_e_deixar_outro_passar(self: MetaRepository, *args: object) -> bool:
        resultado = original(self, *args)
        if not disparou:
            disparou.append(True)
            outra = sqlite3.connect(app.config["DATABASE"])
            with outra:
                outra.execute("INSERT INTO aportes_meta (meta_id, valor_centavos, chave_idempotencia)"
                              " VALUES (?, ?, ?)", (meta_id, centavos, chave))
            outra.close()
        return resultado

    monkeypatch.setattr(MetaRepository, "aporte_registrado", conferir_e_deixar_outro_passar)


def test_aporte_que_perde_a_corrida_e_passaria_do_alvo_retorna_400(monkeypatch: pytest.MonkeyPatch, app: Flask, cliente: FlaskClient, meta_fone: int) -> None:
    aporte_concorrente_depois_da_conferencia(monkeypatch, app, meta_fone, 15000, "outro-envio")

    resposta = aportar(cliente, meta_fone, "100,00")

    assert resposta.status_code == 400
    assert "Faltam só R$ 50,00 para concluir esta meta." in resposta.get_data(as_text=True)
    monkeypatch.undo()
    assert "R$ 150,00 de R$ 200,00 · 75%" in lista(cliente)


def test_clique_duplo_simultaneo_no_aporte_responde_como_sucesso(monkeypatch: pytest.MonkeyPatch, app: Flask, cliente: FlaskClient, meta_fone: int) -> None:
    chave = str(uuid.uuid4())
    aporte_concorrente_depois_da_conferencia(monkeypatch, app, meta_fone, 10000, chave)

    resposta = aportar(cliente, meta_fone, "100,00", chave=chave)

    assert resposta.status_code == 302
    monkeypatch.undo()
    assert "R$ 100,00 de R$ 200,00 · 50%" in lista(cliente)


# ---------------------------------------------------------------------------
# Resumo no topo e metas concluídas separadas
# ---------------------------------------------------------------------------

def ultima_meta_criada(cliente: FlaskClient) -> int:
    return max(int(i) for i in re.findall(r'data-meta-id="(\d+)"', lista(cliente)))


def secao(html: str, id_: str) -> str:
    """Conteúdo da <section> com `id_`, ou '' se a tela não tem essa seção."""
    encontrado = re.search(rf'<section[^>]*id="{id_}".*?</section>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else ""


def test_lista_mostra_o_total_guardado_em_todas_as_metas(cliente: FlaskClient) -> None:
    criar_meta(cliente, "Fone", "200,00")
    aportar(cliente, ultima_meta_criada(cliente), "50,00")
    criar_meta(cliente, "Show", "80,00")
    aportar(cliente, ultima_meta_criada(cliente), "30,00")

    assert re.search(r'id="guardado-total"[^>]*>R\$ 80,00<', lista(cliente))


def test_meta_concluida_fica_separada_das_em_andamento(cliente: FlaskClient) -> None:
    criar_meta(cliente, "Show", "80,00")
    show = ultima_meta_criada(cliente)
    aportar(cliente, show, "80,00")
    criar_meta(cliente, "Fone", "200,00")
    fone = ultima_meta_criada(cliente)

    html = lista(cliente)
    assert f'data-meta-id="{show}"' in secao(html, "metas-concluidas")
    assert f'data-meta-id="{fone}"' in secao(html, "metas-em-andamento")
    assert f'data-meta-id="{show}"' not in secao(html, "metas-em-andamento")


# ---------------------------------------------------------------------------
# Atalhos de aporte (R$ 5, R$ 10, R$ 20)
# ---------------------------------------------------------------------------

def atalhos(html: str, meta_id: int) -> list[str]:
    """{valor: chave} de cada atalho de aporte da meta, como o navegador enviaria."""
    cartao = re.search(rf'data-meta-id="{meta_id}".*?</li>', html, re.DOTALL).group(0)
    formularios = re.findall(r'<form class="atalho".*?</form>', cartao, re.DOTALL)
    return {
        re.search(r'name="valor" value="([^"]+)"', form).group(1):
            re.search(r'name="chave_idempotencia" value="([^"]+)"', form).group(1)
        for form in formularios
    }


def test_atalho_so_aparece_quando_cabe_no_que_falta(cliente: FlaskClient) -> None:
    criar_meta(cliente, "Capinha", "30,00")
    capinha = ultima_meta_criada(cliente)
    aportar(cliente, capinha, "22,00")  # faltam R$ 8,00

    assert list(atalhos(lista(cliente), capinha)) == ["5,00"]


def test_dois_atalhos_seguidos_gravam_os_dois_aportes(cliente: FlaskClient, meta_fone: int) -> None:
    formularios = atalhos(lista(cliente), meta_fone)

    aportar(cliente, meta_fone, "5,00", chave=formularios["5,00"])
    aportar(cliente, meta_fone, "10,00", chave=formularios["10,00"])

    assert "R$ 15,00 de R$ 200,00" in lista(cliente)


def test_meta_concluida_aparece_como_comemoracao_e_o_aporte_como_sucesso(cliente: FlaskClient, meta_fone: int) -> None:
    resposta = cliente.post(f"/metas/{meta_fone}/aportes", follow_redirects=True,
                            data={"valor": "200,00", "chave_idempotencia": str(uuid.uuid4())})

    html = resposta.get_data(as_text=True)
    avisos = {re.sub(r"<[^>]+>", "", corpo).strip(): categoria
              for categoria, corpo in re.findall(r'<p class="aviso aviso-(\w+)"[^>]*>(.*?)</p>', html, re.DOTALL)}
    assert avisos.get("Parabéns, você concluiu a meta Fone!") == "conquista"
    assert avisos.get("Aporte de R$ 200,00 guardado!") == "sucesso"
