"""Fluxo HTTP do quiz: responder, ver a explicação e ganhar XP uma vez só (HU4)."""
import re
import sqlite3
from datetime import date

import pytest

from app.repositories.xp_repo import XpRepository

# Pergunta do banco usada nos testes: R$ 1.000 a 10% ao ano por 2 anos, juros compostos.
# Gabarito conferido à mão: R$ 1.210 é a letra "c"; "a" (R$ 1.200) é a conta de juros simples.
PERGUNTA = "JUROS_1"
CERTA = "c"
ERRADA = "a"

# Gabarito de outras perguntas, conferido à mão no texto do banco (para o teto diário).
GABARITO = {"JUROS_1": "c", "JUROS_2": "b", "JUROS_3": "a", "CREDITO_1": "d", "CREDITO_2": "b"}
AVISO_TETO = "Você já ganhou os 40 XP do quiz hoje."


def responder(cliente, codigo, alternativa=None):
    """Envia a resposta pela rota e devolve a resposta HTTP final (já redirecionada)."""
    dados = {} if alternativa is None else {"alternativa": alternativa}
    return cliente.post(f"/quiz/{codigo}", data=dados, follow_redirects=True)


def xp_total(cliente):
    html = cliente.get("/missoes/").get_data(as_text=True)
    encontrado = re.search(r'<strong class="xp-total">(\d+) XP</strong>', html)
    assert encontrado, "a tela de missões deve mostrar o XP total"
    return int(encontrado.group(1))


def test_acertar_mostra_explicacao_e_da_10_xp(cliente):
    resposta = responder(cliente, PERGUNTA, CERTA)

    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Você acertou!" in html
    assert "+10 XP" in html
    assert "rendem R$ 110: total de R$ 1.210" in html
    assert xp_total(cliente) == 10


def test_errar_mostra_a_resposta_certa_e_a_explicacao_sem_xp(cliente):
    html = responder(cliente, PERGUNTA, ERRADA).get_data(as_text=True)

    assert "Você errou." in html
    assert "Resposta certa: R$ 1.210" in html
    assert "rendem R$ 110: total de R$ 1.210" in html
    assert xp_total(cliente) == 0


def test_enviar_sem_escolher_retorna_400_e_nao_registra(cliente):
    resposta = responder(cliente, PERGUNTA)

    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 400
    assert "Escolha uma alternativa." in html
    # Nada foi gravado: a pergunta continua aberta e o acerto depois ainda rende XP.
    assert 'name="alternativa"' in cliente.get(f"/quiz/{PERGUNTA}").get_data(as_text=True)
    responder(cliente, PERGUNTA, CERTA)
    assert xp_total(cliente) == 10


def test_errar_e_depois_mandar_a_certa_nao_muda_a_resposta_nem_da_xp(cliente):
    # RN-16: uma resposta por pergunta, a primeira vale (reenvio ou nova tentativa).
    responder(cliente, PERGUNTA, ERRADA)

    html = responder(cliente, PERGUNTA, CERTA).get_data(as_text=True)

    assert "Você errou." in html
    assert xp_total(cliente) == 0


def test_reenviar_o_acerto_nao_paga_xp_de_novo(cliente):
    responder(cliente, PERGUNTA, CERTA)
    responder(cliente, PERGUNTA, CERTA)

    assert xp_total(cliente) == 10


def test_quinto_acerto_do_dia_passa_do_teto_e_nao_da_xp(cliente):
    primeiras_4 = ["JUROS_1", "JUROS_2", "JUROS_3", "CREDITO_1"]
    for codigo in primeiras_4:
        responder(cliente, codigo, GABARITO[codigo])
    assert xp_total(cliente) == 40

    # O aviso aparece ANTES de responder, para o aluno decidir se responde hoje.
    assert AVISO_TETO in cliente.get("/quiz/CREDITO_2").get_data(as_text=True)

    html = responder(cliente, "CREDITO_2", GABARITO["CREDITO_2"]).get_data(as_text=True)
    assert "Você acertou!" in html
    assert "XP no quiz" not in html
    assert xp_total(cliente) == 40


def test_tela_do_quiz_lista_os_temas_a_situacao_e_o_xp_de_hoje(cliente):
    responder(cliente, PERGUNTA, CERTA)
    responder(cliente, "INFLACAO_1", "a")  # errada: a certa é "b"

    html = cliente.get("/quiz/").get_data(as_text=True)

    for tema in ("Juros", "Crédito", "Orçamento", "Inflação"):
        assert f">{tema}</h2>" in html
    assert 'data-codigo="JUROS_1" data-status="ACERTOU"' in html
    assert 'data-codigo="INFLACAO_1" data-status="ERROU"' in html
    assert 'data-codigo="CREDITO_1" data-status="NOVA"' in html
    assert "10 de 40 XP hoje" in html


def test_menu_do_aluno_tem_link_para_o_quiz(cliente):
    html = cliente.get("/missoes/").get_data(as_text=True)

    assert 'href="/quiz/"' in html


def test_alternativa_com_espacos_vale_como_a_letra_e_nao_quebra(cliente):
    # Formulário adulterado (" c"): o service aceita a letra sem os espaços; a rota tem
    # que gravar a mesma letra, senão o CHECK do banco derruba a página com 500.
    resposta = responder(cliente, PERGUNTA, f" {CERTA} ")

    assert resposta.status_code == 200
    assert "Você acertou!" in resposta.get_data(as_text=True)


def test_teto_do_quiz_vale_por_dia_no_fuso_do_piaui(cliente, monkeypatch):
    dia = {"hoje": date(2026, 11, 11)}
    monkeypatch.setattr("app.routes.quiz.hoje_no_piaui", lambda: dia["hoje"])
    for codigo in ["JUROS_1", "JUROS_2", "JUROS_3", "CREDITO_1"]:
        responder(cliente, codigo, GABARITO[codigo])
    assert xp_total(cliente) == 40

    dia["hoje"] = date(2026, 11, 12)  # dia seguinte: o teto recomeça
    responder(cliente, "CREDITO_2", GABARITO["CREDITO_2"])

    assert xp_total(cliente) == 50


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_pergunta_inexistente_retorna_404(cliente, metodo):
    assert getattr(cliente, metodo)("/quiz/NAO_EXISTE").status_code == 404


def test_resposta_de_um_aluno_nao_aparece_para_outro(cliente, cliente_outro_aluno):
    responder(cliente, PERGUNTA, ERRADA)

    html = cliente_outro_aluno.get(f"/quiz/{PERGUNTA}").get_data(as_text=True)
    assert 'name="alternativa"' in html
    assert "Você errou." not in html
    responder(cliente_outro_aluno, PERGUNTA, CERTA)
    assert xp_total(cliente_outro_aluno) == 10


def test_falha_ao_creditar_xp_nao_salva_a_resposta(cliente, monkeypatch):
    # INVARIANTES N6: resposta e XP gravados juntos ou nenhum dos dois.
    def falhar(*_args, **_kwargs):
        raise sqlite3.OperationalError("disco cheio (simulado)")

    monkeypatch.setattr(XpRepository, "creditar", falhar)

    with pytest.raises(sqlite3.OperationalError):
        responder(cliente, PERGUNTA, CERTA)

    assert 'name="alternativa"' in cliente.get(f"/quiz/{PERGUNTA}").get_data(as_text=True)
