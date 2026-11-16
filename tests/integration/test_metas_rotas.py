"""Testes das rotas de metas e aportes (HU2) com banco SQLite temporário (tmp_path)."""
import re
import sqlite3
import uuid

import pytest

from app.repositories.meta_repo import MetaRepository


def criar_meta(cliente, nome="Fone", alvo="200,00", prazo="", chave=None):
    return cliente.post("/metas/nova", data={
        "nome": nome, "alvo": alvo, "prazo": prazo,
        "chave_idempotencia": chave or str(uuid.uuid4()),
    })


def lista(cliente):
    return cliente.get("/metas/").get_data(as_text=True)


def aportar(cliente, meta_id, valor, chave=None):
    return cliente.post(f"/metas/{meta_id}/aportes", data={
        "valor": valor, "chave_idempotencia": chave or str(uuid.uuid4()),
    })


@pytest.fixture
def meta_fone(cliente):
    """Meta "Fone" de R$ 200,00 do aluno logado, criada pela rota. Devolve o id."""
    criar_meta(cliente, "Fone", "200,00")
    encontrado = re.search(r'data-meta-id="(\d+)"', lista(cliente))
    assert encontrado, "a meta criada deve aparecer na lista"
    return int(encontrado.group(1))


# ---------------------------------------------------------------------------
# Criar meta
# ---------------------------------------------------------------------------

def test_meta_criada_aparece_com_0_por_cento(cliente):
    resposta = criar_meta(cliente, "Fone", "200,00")

    assert resposta.status_code == 302
    html = lista(cliente)
    assert "Fone" in html
    assert "R$ 0,00 de R$ 200,00 · 0%" in html


def test_meta_sem_nome_e_com_alvo_zero_retorna_400_e_nao_cria(cliente):
    resposta = criar_meta(cliente, nome="", alvo="0", prazo="2026-12-20")

    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert "Dê um nome para a meta." in html
    assert "O valor precisa ser maior que zero." in html
    assert 'value="2026-12-20"' in html  # o que foi digitado continua lá
    assert "Você ainda não tem metas" in lista(cliente)


def test_meta_com_prazo_no_passado_retorna_400_e_nao_cria(cliente):
    resposta = criar_meta(cliente, prazo="2020-01-01")

    assert resposta.status_code == 400
    assert "O prazo não pode ser no passado." in resposta.get_data(as_text=True)
    assert "Você ainda não tem metas" in lista(cliente)


# ---------------------------------------------------------------------------
# Aportes
# ---------------------------------------------------------------------------

def test_aporte_leva_a_meta_a_50_por_cento(cliente, meta_fone):
    aportar(cliente, meta_fone, "50,00")

    resposta = aportar(cliente, meta_fone, "50,00")

    assert resposta.status_code == 302
    assert "R$ 100,00 de R$ 200,00 · 50%" in lista(cliente)


def test_meta_em_andamento_tem_formulario_de_aporte(cliente, meta_fone):
    assert f'action="/metas/{meta_fone}/aportes"' in lista(cliente)


def test_aporte_que_completa_o_alvo_conclui_a_meta(cliente, meta_fone):
    aportar(cliente, meta_fone, "190,00")

    resposta = aportar(cliente, meta_fone, "10,00")

    assert resposta.status_code == 302
    html = lista(cliente)
    assert "R$ 200,00 de R$ 200,00 · 100%" in html
    assert "Concluída" in html
    assert f'action="/metas/{meta_fone}/aportes"' not in html


def test_aporte_que_completa_a_meta_parabeniza_o_aluno(cliente, meta_fone):
    resposta = cliente.post(f"/metas/{meta_fone}/aportes", follow_redirects=True,
                            data={"valor": "200,00", "chave_idempotencia": str(uuid.uuid4())})

    assert "Parabéns, você concluiu a meta Fone!" in resposta.get_data(as_text=True)


def test_meta_concluida_recusa_novo_aporte(cliente, meta_fone):
    aportar(cliente, meta_fone, "200,00")

    resposta = aportar(cliente, meta_fone, "10,00")

    assert resposta.status_code == 400
    assert "Essa meta já foi concluída." in resposta.get_data(as_text=True)
    assert "R$ 200,00 de R$ 200,00 · 100%" in lista(cliente)


def test_aporte_acima_do_que_falta_retorna_400_e_a_meta_nao_conclui(cliente, meta_fone):
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
def test_aporte_zero_ou_negativo_retorna_400_e_o_progresso_nao_muda(cliente, meta_fone, valor):
    aportar(cliente, meta_fone, "50,00")

    resposta = aportar(cliente, meta_fone, valor)

    assert resposta.status_code == 400
    html = resposta.get_data(as_text=True)
    assert f'<p class="erro-campo" id="erro-valor-{meta_fone}">O valor precisa ser maior que zero.</p>' in html
    assert "R$ 50,00 de R$ 200,00 · 25%" in lista(cliente)


# ---------------------------------------------------------------------------
# Acesso (N1): meta de outro aluno é invisível e responde 404
# ---------------------------------------------------------------------------

def test_aporte_em_meta_de_outro_aluno_retorna_404_e_nao_muda_nada(cliente, meta_fone, cliente_outro_aluno):
    resposta = aportar(cliente_outro_aluno, meta_fone, "50,00")

    assert resposta.status_code == 404
    assert "R$ 0,00 de R$ 200,00 · 0%" in lista(cliente)


def test_lista_nao_mostra_metas_de_outro_aluno(meta_fone, cliente_outro_aluno):
    assert "Você ainda não tem metas" in lista(cliente_outro_aluno)


def test_aporte_em_meta_inexistente_retorna_404(cliente):
    assert aportar(cliente, 999, "50,00").status_code == 404


# ---------------------------------------------------------------------------
# Reenvio (N2): o mesmo envio grava uma vez só
# ---------------------------------------------------------------------------

def test_reenvio_da_meta_com_a_mesma_chave_nao_duplica(cliente):
    chave = str(uuid.uuid4())
    criar_meta(cliente, "Fone", "200,00", chave=chave)

    resposta = criar_meta(cliente, "Fone", "200,00", chave=chave)

    assert resposta.status_code == 302
    assert lista(cliente).count("data-meta-id=") == 1


def test_reenvio_do_aporte_com_a_mesma_chave_nao_duplica(cliente, meta_fone):
    chave = str(uuid.uuid4())
    aportar(cliente, meta_fone, "50,00", chave=chave)

    resposta = aportar(cliente, meta_fone, "50,00", chave=chave)

    assert resposta.status_code == 302
    assert "R$ 50,00 de R$ 200,00 · 25%" in lista(cliente)


def test_reenvio_do_aporte_que_concluiu_a_meta_responde_como_sucesso(cliente, meta_fone):
    # Clique duplo no aporte que completa o alvo: o 2º envio não pode virar "meta já concluída".
    aportar(cliente, meta_fone, "190,00")
    chave = str(uuid.uuid4())
    aportar(cliente, meta_fone, "10,00", chave=chave)

    resposta = aportar(cliente, meta_fone, "10,00", chave=chave)

    assert resposta.status_code == 302
    assert "R$ 200,00 de R$ 200,00 · 100%" in lista(cliente)


def test_reenvio_do_aporte_com_a_chave_em_maiusculas_responde_como_sucesso(cliente, meta_fone):
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

def aporte_concorrente_depois_da_conferencia(monkeypatch, app, meta_id, centavos, chave):
    """Na 1ª conferência de reenvio, outra requisição grava e commita um aporte nesta meta.

    Simula a corrida real: a rota já leu o "guardado" e conferiu o limite, mas o
    INSERT dela ainda não rodou. O outro aporte entra por outra conexão, como
    entraria por outro processo.
    """
    original = MetaRepository.aporte_registrado
    disparou = []

    def conferir_e_deixar_outro_passar(self, *args):
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


def test_aporte_que_perde_a_corrida_e_passaria_do_alvo_retorna_400(monkeypatch, app, cliente, meta_fone):
    aporte_concorrente_depois_da_conferencia(monkeypatch, app, meta_fone, 15000, "outro-envio")

    resposta = aportar(cliente, meta_fone, "100,00")

    assert resposta.status_code == 400
    assert "Faltam só R$ 50,00 para concluir esta meta." in resposta.get_data(as_text=True)
    monkeypatch.undo()
    assert "R$ 150,00 de R$ 200,00 · 75%" in lista(cliente)


def test_clique_duplo_simultaneo_no_aporte_responde_como_sucesso(monkeypatch, app, cliente, meta_fone):
    chave = str(uuid.uuid4())
    aporte_concorrente_depois_da_conferencia(monkeypatch, app, meta_fone, 10000, chave)

    resposta = aportar(cliente, meta_fone, "100,00", chave=chave)

    assert resposta.status_code == 302
    monkeypatch.undo()
    assert "R$ 100,00 de R$ 200,00 · 50%" in lista(cliente)
