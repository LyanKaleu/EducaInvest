"""Fluxo HTTP de registrar gasto e ver a missão avançar (HU1 + HU3)."""
import re
import sqlite3
import uuid

import pytest

from app.repositories.xp_repo import XpRepository

PRIMEIRA = "REG_3_GASTOS"
SEGUNDA = "REG_7_LANCAMENTOS"


def registrar(cliente, vezes=1, tipo="saida", categoria="Alimentação"):
    """Registra `vezes` lançamentos pela rota e devolve a resposta do último (já redirecionada)."""
    resposta = None
    for _ in range(vezes):
        form = {"tipo": tipo, "categoria": categoria, "valor": "10,00", "data": "2026-11-01",
                "descricao": "", "chave_idempotencia": str(uuid.uuid4())}
        resposta = cliente.post("/lancamentos/novo", data=form, follow_redirects=True)
    return resposta


def tela_missoes(cliente):
    resposta = cliente.get("/missoes/")
    assert resposta.status_code == 200
    return resposta.get_data(as_text=True)


def xp_total(cliente):
    encontrado = re.search(r'<strong class="xp-total">(\d+) XP</strong>', tela_missoes(cliente))
    assert encontrado, "a tela de missões deve mostrar o XP total"
    return int(encontrado.group(1))


def status_da_missao(cliente, codigo):
    encontrado = re.search(rf'data-codigo="{codigo}" data-status="(\w+)"', tela_missoes(cliente))
    assert encontrado, f"a missão {codigo} deve aparecer na tela"
    return encontrado.group(1)


def id_do_primeiro_lancamento(cliente):
    html = cliente.get("/lancamentos/").get_data(as_text=True)
    return int(re.search(r'href="/lancamentos/(\d+)/editar"', html).group(1))


# ---------------------------------------------------------------------------
# Tela de missões
# ---------------------------------------------------------------------------

def test_aluno_novo_comeca_com_0_xp_no_nivel_1(cliente):
    html = tela_missoes(cliente)

    assert '<strong class="xp-total">0 XP</strong>' in html
    assert "Nível 1 · Iniciante" in html


def test_menu_do_aluno_tem_link_para_missoes(cliente):
    html = cliente.get("/lancamentos/").get_data(as_text=True)

    assert 'href="/missoes/"' in html


def test_missoes_mostra_2_de_3_apos_dois_gastos(cliente):
    registrar(cliente, vezes=2)

    assert "2 de 3" in tela_missoes(cliente)
    assert status_da_missao(cliente, PRIMEIRA) == "ATIVA"
    assert status_da_missao(cliente, SEGUNDA) == "BLOQUEADA"


# ---------------------------------------------------------------------------
# XP por lançamento e teto diário (RN-11)
# ---------------------------------------------------------------------------

def test_lancamento_credita_10_xp_e_avisa(cliente):
    html = registrar(cliente).get_data(as_text=True)

    assert "Lançamento salvo! +10 XP" in html
    assert xp_total(cliente) == 10


def test_lancamento_acima_do_teto_e_salvo_sem_xp_e_avisa(cliente):
    # Entradas, para nenhuma missão de gastos interferir: 5 x 10 XP = teto de 50.
    registrar(cliente, vezes=5, tipo="entrada", categoria="Mesada")
    assert xp_total(cliente) == 50

    html = registrar(cliente, tipo="entrada", categoria="Mesada").get_data(as_text=True)

    assert "Você já ganhou o máximo de XP por registros hoje (50 XP)" in html
    assert html.count('<strong class="valor">') == 6  # o lançamento foi salvo
    assert xp_total(cliente) == 50


def test_reenvio_com_a_mesma_chave_nao_credita_xp_de_novo(cliente, form_valido):
    cliente.post("/lancamentos/novo", data=form_valido)
    cliente.post("/lancamentos/novo", data=form_valido)

    assert xp_total(cliente) == 10


# ---------------------------------------------------------------------------
# Missão: conclusão, conquista e desbloqueio (RN-09, RN-10)
# ---------------------------------------------------------------------------

def test_terceiro_gasto_conclui_missao_credita_30_xp_e_desbloqueia_a_proxima(cliente):
    registrar(cliente, vezes=2)

    html = registrar(cliente).get_data(as_text=True)

    assert "Conquista desbloqueada: Primeiros passos! +30 XP" in html
    assert xp_total(cliente) == 3 * 10 + 30
    assert status_da_missao(cliente, PRIMEIRA) == "CONCLUIDA"
    assert status_da_missao(cliente, SEGUNDA) == "ATIVA"


def test_missao_concluida_aparece_nas_conquistas(cliente):
    registrar(cliente, vezes=3)

    html = tela_missoes(cliente)

    assert re.search(r'<section[^>]*id="conquistas".*Primeiros passos', html, re.DOTALL)


def test_missao_concluida_nao_paga_de_novo(cliente):
    registrar(cliente, vezes=3)  # 30 + 30 da missão
    cliente.post(f"/lancamentos/{id_do_primeiro_lancamento(cliente)}/excluir")

    registrar(cliente)  # volta a 3 gastos: +10 do registro, nada da missão

    assert xp_total(cliente) == 70


def test_editar_entrada_para_gasto_conclui_a_missao(cliente):
    registrar(cliente, vezes=2)
    registrar(cliente, tipo="entrada", categoria="Mesada")
    lancamento_id = id_do_primeiro_lancamento(cliente)  # o mais recente: a entrada

    cliente.post(f"/lancamentos/{lancamento_id}/editar", data={
        "tipo": "saida", "categoria": "Lazer", "valor": "10,00", "data": "2026-11-01",
    })

    assert status_da_missao(cliente, PRIMEIRA) == "CONCLUIDA"
    assert xp_total(cliente) == 30 + 30  # editar não dá XP de registro


# ---------------------------------------------------------------------------
# Nível (RN-12)
# ---------------------------------------------------------------------------

def test_aluno_sobe_para_o_nivel_2_ao_passar_de_100_xp(cliente):
    registrar(cliente, vezes=6)  # 50 (teto) + 30 da 1ª missão = 80

    html = registrar(cliente).get_data(as_text=True)  # 7º: +50 da 2ª missão = 130

    assert "Você subiu para o nível 2 (Aprendiz)!" in html
    assert xp_total(cliente) == 130
    assert "Nível 2 · Aprendiz" in tela_missoes(cliente)


# ---------------------------------------------------------------------------
# Atomicidade e isolamento
# ---------------------------------------------------------------------------

def test_falha_ao_creditar_xp_nao_salva_o_lancamento(cliente, monkeypatch):
    # Spec, HU3 "falha parcial": lançamento e XP gravados juntos ou nenhum dos dois.
    def falhar(*_args, **_kwargs):
        raise sqlite3.OperationalError("disco cheio (simulado)")

    monkeypatch.setattr(XpRepository, "creditar", falhar)

    with pytest.raises(sqlite3.OperationalError):
        registrar(cliente)

    assert "Você ainda não registrou nada" in cliente.get("/lancamentos/").get_data(as_text=True)


def test_missoes_nao_mostram_xp_de_outro_aluno(cliente, cliente_outro_aluno):
    registrar(cliente, vezes=3)

    assert xp_total(cliente_outro_aluno) == 0
    assert status_da_missao(cliente_outro_aluno, PRIMEIRA) == "ATIVA"
