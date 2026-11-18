"""Testes do CSS: as cores só existem nos tokens, e os pares de texto e fundo passam no contraste AA."""
import re
from pathlib import Path

PASTA_CSS = Path(__file__).resolve().parents[2] / "app" / "static" / "css"
COR_FIXA = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")


def test_nenhuma_cor_fixa_fora_dos_tokens():
    """Cor nova vai para o tokens.css (com a versão clara e a escura), nunca direto no CSS."""
    cores_fixas = {
        arquivo.name: COR_FIXA.findall(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(PASTA_CSS.glob("*.css"))
        if arquivo.name != "tokens.css"
    }

    assert {nome: cores for nome, cores in cores_fixas.items() if cores} == {}
