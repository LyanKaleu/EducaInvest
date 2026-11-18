"""Testes do CSS: cores só nos tokens e contraste AA nos dois temas."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_CSS = RAIZ / "app" / "static" / "css"
NOMES_DE_COR = (
    "white|black|red|green|blue|gray|grey|silver|yellow|orange|purple|pink"
    "|navy"
)
# Hex, rgb(), hsl() e as cores com nome mais comuns. transparent e
# currentColor podem.
COR_FIXA = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\("
    rf"|(?<![\w-])(?:{NOMES_DE_COR})(?![\w-])",
    re.IGNORECASE,
)


def cores_fixas(css: str) -> list[str]:
    """As cores escritas direto no CSS, sem contar os comentários."""
    sem_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return COR_FIXA.findall(sem_comentarios)


def test_nenhuma_cor_fixa_fora_dos_tokens() -> None:
    """Cor nova vai para o tokens.css (clara e escura), nunca direto no CSS."""
    por_arquivo = {
        arquivo.name: cores_fixas(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(PASTA_CSS.glob("*.css"))
        if arquivo.name != "tokens.css"
    }

    assert {nome: cor for nome, cor in por_arquivo.items() if cor} == {}


def test_cor_fixa_pega_hex_funcao_e_nome_mas_nao_propriedade() -> None:
    css = (
        "a { color: White; } b { background: #fff; } "
        "i { color: rgb(0 0 0); } /* white */ p { white-space: nowrap; }"
    )

    assert cores_fixas(css) == ["White", "#fff", "rgb("]


# ---------------------------------------------------------------------------
# Contraste WCAG dos tokens, no tema claro e no escuro
# ---------------------------------------------------------------------------

TEXTO_NORMAL = 4.5  # WCAG 1.4.3 (AA)
COMPONENTE = 3.0  # WCAG 1.4.11: borda de campo, barra e anel de foco

# (cor da frente, cor do fundo, mínimo). Cada par existe na tela.
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
    ("fundo", "texto", TEXTO_NORMAL),  # chip marcado
    # Botão, cartão do saldo e selo; também o anel de foco dentro do cartão.
    ("texto-sobre-cor", "primaria", TEXTO_NORMAL),
    ("texto-sobre-cor", "primaria-escura", TEXTO_NORMAL),
    ("texto-sobre-cor", "perigo", TEXTO_NORMAL),  # excluir, saldo negativo
    ("texto-sobre-cor", "perigo-escura", TEXTO_NORMAL),
    # Links, entradas e XP; também a marca do dia com XP na sequência.
    ("primaria-texto", "fundo", TEXTO_NORMAL),
    ("primaria-texto", "suave", TEXTO_NORMAL),
    ("primaria-texto", "sucesso-fundo", TEXTO_NORMAL),  # selo de XP
    ("primaria-texto-hover", "fundo", TEXTO_NORMAL),
    ("perigo-texto", "fundo", TEXTO_NORMAL),
    ("perigo-texto", "suave", TEXTO_NORMAL),
    ("perigo-texto", "erro-fundo", TEXTO_NORMAL),  # alerta de inativos
    ("borda", "fundo", COMPONENTE),
    ("borda", "suave", COMPONENTE),
    ("foco", "fundo", COMPONENTE),
    ("foco", "suave", COMPONENTE),
    ("foco", "foco-fundo", COMPONENTE),  # borda da alternativa marcada
    ("primaria", "suave", COMPONENTE),  # barra cheia sobre o trilho
]


def _tokens(bloco: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", bloco))


def temas() -> dict[str, dict[str, str]]:
    """Cores de cada tema. O escuro herda do claro o que não redefine."""
    texto = (PASTA_CSS / "tokens.css").read_text(encoding="utf-8")
    bloco_claro = re.search(
        r"^:root\s*\{(.*?)^\}", texto, re.DOTALL | re.MULTILINE
    )
    bloco_escuro = re.search(
        r"@media \(prefers-color-scheme: dark\)\s*\{\s*:root\s*\{(.*?)\}",
        texto,
        re.DOTALL,
    )
    assert bloco_claro
    assert bloco_escuro, "falta o bloco @media (prefers-color-scheme: dark)"
    claro = _tokens(bloco_claro.group(1))
    return {
        "claro": claro,
        "escuro": {**claro, **_tokens(bloco_escuro.group(1))},
    }


def contraste(frente: str, fundo: str) -> float:
    """Razão de contraste da WCAG entre duas cores #rrggbb."""

    def luminancia(cor: str) -> float:
        canais = [int(cor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = [
            c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            for c in canais
        ]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    claro, escuro = sorted(
        [luminancia(frente), luminancia(fundo)], reverse=True
    )
    return (claro + 0.05) / (escuro + 0.05)


def test_pares_de_cor_passam_no_contraste_aa_nos_dois_temas() -> None:
    falhas = [
        f"{tema}: --{frente} sobre --{fundo} = "
        f"{contraste(cores[frente], cores[fundo]):.2f} (mínimo {minimo})"
        for tema, cores in temas().items()
        for frente, fundo, minimo in PARES
        if contraste(cores[frente], cores[fundo]) < minimo
    ]

    assert falhas == []


def test_tema_escuro_troca_o_fundo_da_pagina() -> None:
    cores = temas()

    # O fundo da página fica perto do preto.
    assert contraste(cores["escuro"]["suave"], "#000000") < 1.5
    assert cores["escuro"]["texto"] != cores["claro"]["texto"]


def test_cor_da_barra_do_navegador_e_o_fundo_de_cada_tema() -> None:
    """A meta theme-color não aceita var(): o base.html repete o --fundo."""
    html = (RAIZ / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    meta = {
        tema: cor.lower()
        for cor, tema in re.findall(
            r'<meta name="theme-color" content="(#[0-9a-fA-F]{6})"'
            r' media="\(prefers-color-scheme: (\w+)\)">',
            html,
        )
    }
    cores = temas()

    assert meta == {
        "light": cores["claro"]["fundo"],
        "dark": cores["escuro"]["fundo"],
    }


def test_contraste_bate_com_valores_conhecidos() -> None:
    """Fórmula da WCAG: preto no branco é 21:1; #767676 no branco, 4,54:1."""
    assert round(contraste("#000000", "#ffffff"), 2) == 21.0
    assert round(contraste("#767676", "#ffffff"), 2) == 4.54
