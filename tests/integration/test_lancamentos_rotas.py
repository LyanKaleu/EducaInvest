"""Testes das rotas de lançamentos (HU1) com banco SQLite temporário (tmp_path)."""
import re
from datetime import timedelta

from app.services.lancamento_service import hoje_no_piaui


def quantas_vezes_na_lista(cliente, valor):
    """Quantos cartões da lista mostram `valor` em destaque.

    Conta só o <strong class="valor">: o mesmo valor também aparece nos textos
    ocultos dos links Editar/Excluir (para leitor de tela).
    """
    html = cliente.get("/lancamentos/").get_data(as_text=True)
    return len(re.findall(rf'<strong class="valor">[^<]*{re.escape(valor)}</strong>', html))


# ---------------------------------------------------------------------------
# Acesso
# ---------------------------------------------------------------------------

def test_inicio_redireciona_para_a_lista(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/lancamentos/")


def test_lista_sem_login_redireciona_para_o_login(cliente_sem_login):
    # Comportamento NOVO (login real): antes era 401.
    resposta = cliente_sem_login.get("/lancamentos/")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/login")


# ---------------------------------------------------------------------------
# Listar
# ---------------------------------------------------------------------------

def test_lista_vazia_convida_a_registrar(cliente):
    resposta = cliente.get("/lancamentos/")

    assert resposta.status_code == 200
    assert "Você ainda não registrou nada" in resposta.get_data(as_text=True)


def test_lista_mostra_valor_e_data_formatados(cliente, lancamento_existente):
    html = cliente.get("/lancamentos/").get_data(as_text=True)

    assert "R$ 25,00" in html
    assert "01/11/2026" in html


def test_lista_nao_mostra_lancamentos_de_outro_aluno(cliente_outro_aluno, lancamento_existente):
    html = cliente_outro_aluno.get("/lancamentos/").get_data(as_text=True)

    assert "Você ainda não registrou nada" in html


def test_busca_encontra_pela_categoria(cliente, lancamento_existente):
    html = cliente.get("/lancamentos/?busca=aliment").get_data(as_text=True)

    assert "R$ 25,00" in html


def test_busca_sem_resultado_avisa_que_nada_foi_encontrado(cliente, lancamento_existente):
    html = cliente.get("/lancamentos/?busca=viagem").get_data(as_text=True)

    assert "Nada encontrado para “viagem”" in html


def test_busca_escapa_html_digitado(cliente):
    html = cliente.get("/lancamentos/?busca=<script>").get_data(as_text=True)

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# Criar
# ---------------------------------------------------------------------------

def test_formulario_novo_vem_com_gasto_marcado_e_chave_gerada(cliente):
    html = cliente.get("/lancamentos/novo").get_data(as_text=True)

    assert 'value="saida" checked' in html
    assert re.search(r'name="chave_idempotencia" value="[0-9a-f-]{36}"', html)


def test_criar_valido_redireciona_para_a_lista(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data=form_valido)

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/lancamentos/")


def test_criar_valido_mostra_mensagem_de_sucesso(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data=form_valido, follow_redirects=True)

    assert "Lançamento salvo!" in resposta.get_data(as_text=True)


def test_criar_valido_aparece_na_lista(cliente, form_valido):
    cliente.post("/lancamentos/novo", data=form_valido)

    assert quantas_vezes_na_lista(cliente, "R$ 25,00") == 1


def test_reenvio_com_a_mesma_chave_nao_duplica(cliente, form_valido):
    cliente.post("/lancamentos/novo", data=form_valido)
    cliente.post("/lancamentos/novo", data=form_valido)

    assert quantas_vezes_na_lista(cliente, "R$ 25,00") == 1


def test_criar_invalido_retorna_400(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data={**form_valido, "valor": ""})

    assert resposta.status_code == 400


def test_criar_invalido_mostra_flash_de_erro(cliente, form_valido):
    html = cliente.post("/lancamentos/novo", data={**form_valido, "valor": ""}).get_data(as_text=True)

    assert 'role="alert"' in html
    assert "Confira os campos destacados" in html


def test_criar_invalido_mostra_erro_junto_ao_campo(cliente, form_valido):
    html = cliente.post("/lancamentos/novo", data={**form_valido, "valor": ""}).get_data(as_text=True)

    assert 'aria-invalid="true" aria-describedby="erro-valor"' in html
    assert '<p class="erro-campo" id="erro-valor">Informe o valor.</p>' in html


def test_criar_invalido_preserva_o_que_foi_digitado(cliente, form_valido):
    form = {**form_valido, "valor": "", "descricao": "pastel da cantina"}
    html = cliente.post("/lancamentos/novo", data=form).get_data(as_text=True)

    assert 'value="pastel da cantina"' in html
    assert 'value="2026-11-01"' in html
    assert f'value="{form_valido["chave_idempotencia"]}"' in html


def test_criar_invalido_nao_grava_nada(cliente, form_valido):
    cliente.post("/lancamentos/novo", data={**form_valido, "valor": "0"})

    assert "Você ainda não registrou nada" in cliente.get("/lancamentos/").get_data(as_text=True)


def test_criar_com_data_futura_retorna_400(cliente, form_valido):
    amanha = (hoje_no_piaui() + timedelta(days=1)).isoformat()
    resposta = cliente.post("/lancamentos/novo", data={**form_valido, "data": amanha})

    assert resposta.status_code == 400
    assert "A data não pode ser no futuro." in resposta.get_data(as_text=True)


def test_criar_com_data_inexistente_retorna_400(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data={**form_valido, "data": "31/02/2026"})

    assert resposta.status_code == 400
    assert "Essa data não existe." in resposta.get_data(as_text=True)


def test_criar_com_descricao_de_141_caracteres_retorna_400(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data={**form_valido, "descricao": "a" * 141})

    assert resposta.status_code == 400


def test_criar_com_descricao_de_140_caracteres_redireciona(cliente, form_valido):
    resposta = cliente.post("/lancamentos/novo", data={**form_valido, "descricao": "a" * 140})

    assert resposta.status_code == 302


# ---------------------------------------------------------------------------
# Editar
# ---------------------------------------------------------------------------

def test_editar_mostra_formulario_preenchido(cliente, lancamento_existente):
    html = cliente.get(f"/lancamentos/{lancamento_existente['id']}/editar").get_data(as_text=True)

    assert 'value="25,00"' in html
    assert '<option value="Alimentação" selected' in html


def test_formulario_de_edicao_nao_tem_campo_de_chave(cliente, lancamento_existente):
    html = cliente.get(f"/lancamentos/{lancamento_existente['id']}/editar").get_data(as_text=True)

    assert "chave_idempotencia" not in html


def test_editar_inexistente_retorna_404(cliente):
    assert cliente.get("/lancamentos/9999/editar").status_code == 404


def test_editar_lancamento_de_outro_aluno_retorna_404(cliente_outro_aluno, lancamento_existente):
    resposta = cliente_outro_aluno.get(f"/lancamentos/{lancamento_existente['id']}/editar")

    assert resposta.status_code == 404


def test_atualizar_valido_altera_o_valor_na_lista(cliente, lancamento_existente, form_valido):
    url = f"/lancamentos/{lancamento_existente['id']}/editar"
    cliente.post(url, data={**form_valido, "valor": "30"})

    assert quantas_vezes_na_lista(cliente, "R$ 30,00") == 1


def test_atualizar_valido_redireciona_com_mensagem(cliente, lancamento_existente, form_valido):
    url = f"/lancamentos/{lancamento_existente['id']}/editar"
    resposta = cliente.post(url, data=form_valido, follow_redirects=True)

    assert "Lançamento atualizado!" in resposta.get_data(as_text=True)


def test_atualizar_invalido_retorna_400_no_formulario_de_edicao(cliente, lancamento_existente, form_valido):
    url = f"/lancamentos/{lancamento_existente['id']}/editar"
    resposta = cliente.post(url, data={**form_valido, "categoria": "Mesada"})

    assert resposta.status_code == 400
    assert f'action="{url}"' in resposta.get_data(as_text=True)


def test_atualizar_inexistente_retorna_404(cliente, form_valido):
    assert cliente.post("/lancamentos/9999/editar", data=form_valido).status_code == 404


def test_atualizar_lancamento_de_outro_aluno_retorna_404(cliente_outro_aluno, lancamento_existente, form_valido):
    url = f"/lancamentos/{lancamento_existente['id']}/editar"

    assert cliente_outro_aluno.post(url, data=form_valido).status_code == 404


# ---------------------------------------------------------------------------
# Excluir
# ---------------------------------------------------------------------------

def test_confirmacao_de_exclusao_mostra_resumo(cliente, lancamento_existente):
    html = cliente.get(f"/lancamentos/{lancamento_existente['id']}/excluir").get_data(as_text=True)

    assert "Excluir este lançamento?" in html
    assert "R$ 25,00" in html


def test_abrir_confirmacao_nao_apaga(cliente, lancamento_existente):
    cliente.get(f"/lancamentos/{lancamento_existente['id']}/excluir")

    assert quantas_vezes_na_lista(cliente, "R$ 25,00") == 1


def test_confirmacao_de_exclusao_inexistente_retorna_404(cliente):
    assert cliente.get("/lancamentos/9999/excluir").status_code == 404


def test_confirmacao_de_exclusao_de_outro_aluno_retorna_404_sem_mostrar_o_valor(
        cliente_outro_aluno, lancamento_existente):
    resposta = cliente_outro_aluno.get(f"/lancamentos/{lancamento_existente['id']}/excluir")

    assert resposta.status_code == 404
    assert "R$ 25,00" not in resposta.get_data(as_text=True)


def test_excluir_via_post_remove_da_lista(cliente, lancamento_existente):
    cliente.post(f"/lancamentos/{lancamento_existente['id']}/excluir")

    assert quantas_vezes_na_lista(cliente, "R$ 25,00") == 0


def test_excluir_mostra_mensagem_de_sucesso(cliente, lancamento_existente):
    resposta = cliente.post(f"/lancamentos/{lancamento_existente['id']}/excluir", follow_redirects=True)

    assert "Lançamento excluído." in resposta.get_data(as_text=True)


def test_excluir_inexistente_retorna_404(cliente):
    assert cliente.post("/lancamentos/9999/excluir").status_code == 404


def test_excluir_lancamento_de_outro_aluno_retorna_404(cliente_outro_aluno, lancamento_existente):
    resposta = cliente_outro_aluno.post(f"/lancamentos/{lancamento_existente['id']}/excluir")

    assert resposta.status_code == 404


def test_tentativa_de_outro_aluno_excluir_nao_apaga_do_dono(cliente, cliente_outro_aluno, lancamento_existente):
    cliente_outro_aluno.post(f"/lancamentos/{lancamento_existente['id']}/excluir")

    assert quantas_vezes_na_lista(cliente, "R$ 25,00") == 1
