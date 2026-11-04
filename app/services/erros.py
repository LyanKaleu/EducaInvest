"""Erros de regra de negócio compartilhados pelos services."""


class ErroValidacao(Exception):
    """Dados de formulário inválidos.

    `erros` mapeia o nome do campo do formulário para a mensagem em português,
    para a tela mostrar cada mensagem junto ao seu campo (HU1).
    """

    def __init__(self, erros: dict[str, str]):
        """Guarda os erros por campo e monta a mensagem geral da exceção.

        Args:
            erros: dicionário {nome_do_campo: mensagem}. Uma cópia é guardada
                em `self.erros`, e `str(excecao)` junta todas as mensagens.
        """
        self.erros = dict(erros)
        super().__init__(" ".join(self.erros.values()))
