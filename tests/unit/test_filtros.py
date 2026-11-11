"""Testes dos filtros de formatação usados nas telas (dinheiro em reais)."""
import pytest

from app.filtros import reais


@pytest.mark.parametrize(
    ("centavos", "esperado"),
    [
        (123456, "R$ 1.234,56"),
        (0, "R$ 0,00"),
        (-1050, "-R$ 10,50"),        # saldo negativo: gastou mais do que entrou
        (-123456, "-R$ 1.234,56"),
    ],
)
def test_reais_formata_positivo_zero_e_negativo(centavos, esperado):
    assert reais(centavos) == esperado
