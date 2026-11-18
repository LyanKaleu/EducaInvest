"""Testes do CSS: as cores só existem nos tokens, e os pares de texto e fundo passam no contraste AA."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_CSS = RAIZ / "app" / "static" / "css"
# Hex, rgb(), hsl() e as cores com nome mais comuns (transparent e currentColor podem).
COR_FIXA = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\("
    r"|(?<![\w-])(?:white|black|red|green|blue|gray|grey|silver|yellow|orange|purple|pink|navy)(?![\w-])",
    re.IGNORECASE,
)


def cores_fixas(css):
    """As cores escritas direto no CSS, sem contar os comentários."""
    return COR_FIXA.findall(re.sub(r"/\*.*?\*/", "", css, flags=re.S))


def test_nenhuma_cor_fixa_fora_dos_tokens():
    """Cor nova vai para o tokens.css (com a versão clara e a escura), nunca direto no CSS."""
    por_arquivo = {
        arquivo.name: cores_fixas(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(PASTA_CSS.glob("*.css"))
        if arquivo.name != "tokens.css"
    }

    assert {nome: cores for nome, cores in por_arquivo.items() if cores} == {}


def test_cor_fixa_pega_hex_funcao_e_nome_mas_nao_propriedade():
    css = "a { color: White; } b { background: #fff; } i { color: rgb(0 0 0); } /* white */ p { white-space: nowrap; }"

    assert cores_fixas(css) == ["White", "#fff", "rgb("]


# ---------------------------------------------------------------------------
# Contraste WCAG dos tokens, no tema claro e no escuro
# ---------------------------------------------------------------------------

TEXTO_NORMAL = 4.5   # WCAG 1.4.3 (AA)
COMPONENTE = 3.0     # WCAG 1.4.11: borda de campo e anel de foco

# (cor da frente, cor do fundo, mínimo). Cada par existe na tela, em algum componente.
PARES = [
    ("texto", "fundo", TEXTO_NORMAL),
    ("texto", "suave", TEXTO_NORMAL),
    ("texto-suave", "fundo", TEXTO_NORMAL),
    ("texto-suave", "suave", TEXTO_NORMAL),
    ("texto", "cartao-hover", TEXTO_NORMAL),
    ("texto-suave", "cartao-hover", TEXTO_NORMAL),
    ("primaria-texto", "cartao-hover", TEXTO_NORMAL),
    ("perigo-texto", "cartao-hover", TEXTO_NORMAL),
    ("texto", "sucesso-fundo", TEXTO_NORMAL),
    ("texto", "erro-fundo", TEXTO_NORMAL),
    ("texto", "foco-fundo", TEXTO_NORMAL),
    ("fundo", "texto", TEXTO_NORMAL),                    # chip marcado
    ("texto-sobre-cor", "primaria", TEXTO_NORMAL),       # botão, cartão do saldo, selo
    ("texto-sobre-cor", "primaria-escura", TEXTO_NORMAL),
    ("texto-sobre-cor", "perigo", TEXTO_NORMAL),         # excluir, saldo negativo
    ("texto-sobre-cor", "perigo-escura", TEXTO_NORMAL),
    ("primaria-texto", "fundo", TEXTO_NORMAL),
    ("primaria-texto", "suave", TEXTO_NORMAL),
    ("primaria-texto", "sucesso-fundo", TEXTO_NORMAL),   # selo de XP
    ("primaria-texto-hover", "fundo", TEXTO_NORMAL),
    ("perigo-texto", "fundo", TEXTO_NORMAL),
    ("perigo-texto", "suave", TEXTO_NORMAL),
    ("perigo-texto", "erro-fundo", TEXTO_NORMAL),        # alerta de inativos
    ("borda", "fundo", COMPONENTE),
    ("borda", "suave", COMPONENTE),
    ("foco", "fundo", COMPONENTE),
    ("foco", "suave", COMPONENTE),
    ("foco", "foco-fundo", COMPONENTE),                  # borda da alternativa marcada
    ("primaria", "suave", COMPONENTE),                   # preenchimento da barra sobre o trilho
    ("primaria-texto", "fundo", COMPONENTE),             # marca do dia com XP na sequência
    # Anel de foco dentro do cartão colorido (saldo): o contorno usa --texto-sobre-cor.
    ("texto-sobre-cor", "primaria", COMPONENTE),
    ("texto-sobre-cor", "perigo", COMPONENTE),
]


def _tokens(bloco):
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", bloco))


def temas():
    """{"claro": {token: cor}, "escuro": {token: cor}}; o escuro herda do claro o que não redefine."""
    texto = (PASTA_CSS / "tokens.css").read_text(encoding="utf-8")
    claro = _tokens(re.search(r"^:root\s*\{(.*?)^\}", texto, re.S | re.M).group(1))
    bloco_escuro = re.search(r"@media \(prefers-color-scheme: dark\)\s*\{\s*:root\s*\{(.*?)\}", texto, re.S)
    assert bloco_escuro, "o tokens.css precisa do bloco @media (prefers-color-scheme: dark)"
    return {"claro": claro, "escuro": {**claro, **_tokens(bloco_escuro.group(1))}}


def contraste(frente, fundo):
    def luminancia(cor):
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    claro, escuro = sorted([luminancia(frente), luminancia(fundo)], reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_pares_de_cor_passam_no_contraste_aa_nos_dois_temas():
    falhas = [
        f"{tema}: --{frente} sobre --{fundo} = {contraste(cores[frente], cores[fundo]):.2f} (mínimo {minimo})"
        for tema, cores in temas().items()
        for frente, fundo, minimo in PARES
        if contraste(cores[frente], cores[fundo]) < minimo
    ]

    assert falhas == []


def test_tema_escuro_troca_o_fundo_da_pagina():
    cores = temas()

    assert contraste(cores["escuro"]["suave"], "#000000") < 1.5   # fundo escuro de verdade
    assert cores["escuro"]["texto"] != cores["claro"]["texto"]


def test_cor_da_barra_do_navegador_e_o_fundo_de_cada_tema():
    """A meta theme-color não aceita var(), então o base.html repete o --fundo à mão."""
    html = (RAIZ / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    meta = dict(
        (tema, cor.lower())
        for cor, tema in re.findall(
            r'<meta name="theme-color" content="(#[0-9a-fA-F]{6})" media="\(prefers-color-scheme: (\w+)\)">', html
        )
    )
    cores = temas()

    assert meta == {"light": cores["claro"]["fundo"], "dark": cores["escuro"]["fundo"]}


def test_contraste_bate_com_valores_conhecidos():
    """A conta segue a fórmula da WCAG: preto no branco é 21:1, e #767676 no branco é 4,54:1."""
    assert round(contraste("#000000", "#ffffff"), 2) == 21.0
    assert round(contraste("#767676", "#ffffff"), 2) == 4.54
