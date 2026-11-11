"""Valida metas e aportes e calcula o progresso percentual (RN-08)."""
from datetime import date

from app.filtros import reais
from app.services.erros import ErroValidacao
from app.services.formulario import converter_chave, converter_valor, ler_data, texto_do_campo
from app.services.lancamento_service import hoje_no_piaui

NOME_MAX = 60  # o mesmo CHECK da tabela metas


def validar_meta(dados, hoje: date | None = None) -> dict:
    """Valida o formulário de nova meta e devolve os dados normalizados.

    Confere todos os campos antes de responder, para a tela mostrar todos os
    erros de uma vez, cada um junto ao seu campo.

    Args:
        dados: objeto com `.get(nome)` (`request.form` ou dict), com os campos
            `nome`, `alvo`, `prazo` (opcional) e `chave_idempotencia`, como texto.
        hoje: data considerada "hoje" para recusar prazo no passado. Se for
            None, usa `hoje_no_piaui()`. Os testes passam uma data fixa.

    Returns:
        dict: `nome`, `valor_alvo_centavos` (int), `prazo` ("AAAA-MM-DD" ou
        None) e `chave_idempotencia`, com os nomes dos parâmetros de
        `MetaRepository.criar`.

    Raises:
        ErroValidacao: se algum campo for inválido, com a mensagem por campo.
    """
    hoje = hoje or hoje_no_piaui()
    erros: dict[str, str] = {}

    def campo(nome, conversor, *args):
        try:
            return conversor(texto_do_campo(dados, nome), *args)
        except ValueError as erro:
            erros[nome] = str(erro)
            return None

    nome = campo("nome", _converter_nome)
    valor_alvo = campo("alvo", converter_valor)
    prazo = campo("prazo", _converter_prazo, hoje)
    chave = campo("chave_idempotencia", converter_chave)

    if erros:
        raise ErroValidacao(erros)

    return {
        "nome": nome,
        "valor_alvo_centavos": valor_alvo,
        "prazo": prazo.isoformat() if prazo else None,
        "chave_idempotencia": chave,
    }


def validar_aporte(dados) -> dict:
    """Valida o formulário de aporte (campos `valor` e `chave_idempotencia`).

    Returns:
        dict: `valor_centavos` (int) e `chave_idempotencia`.

    Raises:
        ErroValidacao: se algum campo for inválido, com a mensagem por campo.
    """
    erros: dict[str, str] = {}
    resultado = {}
    for campo, chave, conversor in (("valor", "valor_centavos", converter_valor),
                                    ("chave_idempotencia", "chave_idempotencia", converter_chave)):
        try:
            resultado[chave] = conversor(texto_do_campo(dados, campo))
        except ValueError as erro:
            erros[campo] = str(erro)
    if erros:
        raise ErroValidacao(erros)
    return resultado


def conferir_limite_do_aporte(valor_centavos: int, alvo_centavos: int, guardado_centavos: int) -> None:
    """Recusa o aporte maior do que falta para concluir a meta.

    Sem resgate nem exclusão de aporte, um dígito a mais fecharia a meta para
    sempre. Fica fora de `validar_aporte` porque a rota checa o reenvio antes:
    o reenvio do aporte que concluiu a meta (falta zero) é sucesso, não erro.

    Raises:
        ErroValidacao: em `valor`, com o quanto falta.
    """
    falta = alvo_centavos - guardado_centavos
    if valor_centavos > falta:
        raise ErroValidacao(
            {"valor": f"Faltam só {reais(falta)} para concluir esta meta. Guarde até esse valor."}
        )


def progresso(alvo_centavos: int, guardado_centavos: int) -> dict:
    """Progresso da meta: valor guardado / valor-alvo (RN-08).

    Returns:
        dict: `percentual` (int de 0 a 100, arredondado para baixo, para só
        mostrar 100% quando o alvo foi atingido) e `concluida` (bool).
    """
    return {
        "percentual": min(guardado_centavos * 100 // alvo_centavos, 100),
        "concluida": guardado_centavos >= alvo_centavos,
    }


def mais_perto_de_concluir(metas: list[dict]) -> dict | None:
    """A meta em andamento mais perto de concluir, para o card da tela inicial.

    Args:
        metas: dicts com `id`, `valor_alvo_centavos` e `guardado_centavos`
            (como em `MetaRepository.listar`).

    Returns:
        dict | None: a meta não concluída com o maior percentual (no empate, a
        mais antiga, de menor id), com as chaves de `progresso` somadas; ou
        None se não houver meta em andamento.
    """
    em_andamento = [
        {**meta, **progresso(meta["valor_alvo_centavos"], meta["guardado_centavos"])}
        for meta in metas
    ]
    em_andamento = [meta for meta in em_andamento if not meta["concluida"]]
    if not em_andamento:
        return None
    return min(em_andamento, key=lambda meta: (-meta["percentual"], meta["id"]))


def _converter_nome(texto):
    if not texto:
        raise ValueError("Dê um nome para a meta.")
    if len(texto) > NOME_MAX:
        raise ValueError(f"O nome pode ter no máximo {NOME_MAX} caracteres.")
    return texto


def _converter_prazo(texto, hoje):
    if not texto:
        return None
    prazo = ler_data(texto)
    if prazo < hoje:
        raise ValueError("O prazo não pode ser no passado.")
    return prazo
