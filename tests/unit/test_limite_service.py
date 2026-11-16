"""Testes do limite de tentativas de login (auditoria, achado 1). Só o service, relógio falso."""
from app.services.limite_service import LimiteDeTentativas


class RelogioFalso:
    """Relógio controlado pelo teste, em segundos."""

    def __init__(self):
        self.agora = 1000.0

    def __call__(self):
        return self.agora


def limite_com_relogio(**extra):
    relogio = RelogioFalso()
    return LimiteDeTentativas(maximo=5, janela_segundos=900, relogio=relogio, **extra), relogio


def tentar(limite, chave, vezes):
    return [limite.tentar(chave) for _ in range(vezes)]


def test_as_5_primeiras_tentativas_passam():
    limite, _ = limite_com_relogio()

    assert tentar(limite, "ana@x.br", 5) == [True] * 5


def test_a_sexta_tentativa_e_recusada():
    # A tentativa conta antes de a senha ser conferida: não depende de registrar a falha depois.
    limite, _ = limite_com_relogio()
    tentar(limite, "ana@x.br", 5)

    assert limite.tentar("ana@x.br") is False


def test_bloqueio_acaba_15_minutos_depois_da_primeira_tentativa():
    limite, relogio = limite_com_relogio()
    tentar(limite, "ana@x.br", 5)

    relogio.agora += 901

    assert limite.tentar("ana@x.br") is True


def test_bloqueio_continua_aos_14_minutos():
    limite, relogio = limite_com_relogio()
    tentar(limite, "ana@x.br", 5)

    relogio.agora += 14 * 60

    assert limite.tentar("ana@x.br") is False


def test_tentativas_antigas_nao_somam_com_as_novas():
    limite, relogio = limite_com_relogio()
    tentar(limite, "ana@x.br", 4)
    relogio.agora += 901

    assert tentar(limite, "ana@x.br", 5) == [True] * 5


def test_limpar_zera_as_tentativas():
    limite, _ = limite_com_relogio()
    tentar(limite, "ana@x.br", 5)
    limite.limpar("ana@x.br")

    assert limite.tentar("ana@x.br") is True


def test_bloqueio_de_uma_chave_nao_afeta_outra():
    limite, _ = limite_com_relogio()
    tentar(limite, "ana@x.br", 5)

    assert limite.tentar("bia@x.br") is True


def test_janelas_vencidas_sao_descartadas_quando_ha_muitas_chaves():
    # E-mails aleatórios não podem fazer a memória crescer até o servidor reiniciar.
    limite, relogio = limite_com_relogio(max_chaves=3)
    for email in ["a@x.br", "b@x.br", "c@x.br"]:
        limite.tentar(email)
    relogio.agora += 901

    limite.tentar("d@x.br")

    assert len(limite) == 1
