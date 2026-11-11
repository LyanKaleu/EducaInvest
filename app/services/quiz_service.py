"""Corrige a resposta, mostra a explicação e impede XP repetido (RN-14)."""
from app.services.erros import ErroValidacao

# Valores a confirmar pelo grupo (como os de xp_service). Equilíbrio: um lançamento vale 10
# com teto de 50 por dia; o quiz fica abaixo disso para registrar continuar sendo o hábito
# principal, e o teto impede ganhar o nível 2 de uma vez respondendo o banco inteiro.
XP_POR_ACERTO = 10
TETO_DIARIO_QUIZ = 40

# Temas da spec (RF06), na ordem em que aparecem na tela.
TEMAS = {"JUROS": "Juros", "CREDITO": "Crédito", "ORCAMENTO": "Orçamento", "INFLACAO": "Inflação"}

# Banco local do MVP: cada quiz curto é uma pergunta (spec, limitações). Texto A REVISAR pelo
# grupo; o código (`codigo`) não muda depois de publicado, porque a resposta do aluno aponta
# para ele. Mudar a ordem ou a letra certa de uma pergunta já respondida muda o histórico.
PERGUNTAS = (
    {
        "codigo": "JUROS_1",
        "tema": "JUROS",
        "enunciado": "Você aplica R$ 1.000 a 10% ao ano, com juros compostos. Quanto terá depois de 2 anos?",
        "alternativas": {"a": "R$ 1.200", "b": "R$ 1.020", "c": "R$ 1.210", "d": "R$ 1.100"},
        "correta": "c",
        "explicacao": "No 1º ano, R$ 1.000 viram R$ 1.100. No 2º, os 10% incidem sobre R$ 1.100 e rendem "
                      "R$ 110: total de R$ 1.210. Com juros simples seriam R$ 1.200, porque o juro "
                      "não renderia sobre o juro.",
    },
    {
        "codigo": "JUROS_2",
        "tema": "JUROS",
        "enunciado": "Uma dívida cobra 2% de juros ao mês. Em um ano, quanto ela cresce?",
        "alternativas": {"a": "Exatamente 24%", "b": "Mais de 24%: cerca de 27%", "c": "2%", "d": "12%"},
        "correta": "b",
        "explicacao": "Os juros de cada mês entram na conta do mês seguinte. 1,02 multiplicado 12 vezes "
                      "dá cerca de 1,268: a dívida cresce quase 27% no ano, não 24%.",
    },
    {
        "codigo": "JUROS_3",
        "tema": "JUROS",
        "enunciado": "Por que começar a guardar dinheiro cedo faz diferença?",
        "alternativas": {
            "a": "Porque os juros compostos têm mais tempo para render sobre os rendimentos anteriores",
            "b": "Porque o banco paga um bônus para quem é jovem",
            "c": "Não faz diferença: só importa o total depositado",
            "d": "Porque a inflação é menor para quem é jovem",
        },
        "correta": "a",
        "explicacao": "Com juros compostos, o rendimento de hoje também rende amanhã. Quanto mais tempo "
                      "o dinheiro fica aplicado, maior o efeito, mesmo com depósitos pequenos.",
    },
    {
        "codigo": "CREDITO_1",
        "tema": "CREDITO",
        "enunciado": "Ao comparar dois empréstimos, qual informação mostra o custo total, com juros, "
                     "tarifas, impostos e seguros?",
        "alternativas": {
            "a": "O valor da parcela",
            "b": "A taxa de juros anunciada",
            "c": "O número de parcelas",
            "d": "O CET (Custo Efetivo Total)",
        },
        "correta": "d",
        "explicacao": "O CET soma tudo o que você vai pagar, não só os juros. O banco é obrigado a "
                      "informar o CET antes da contratação: compare por ele.",
    },
    {
        "codigo": "CREDITO_2",
        "tema": "CREDITO",
        "enunciado": "Um celular custa R$ 1.000 em 10x \"sem juros\" ou R$ 900 à vista. O que isso indica?",
        "alternativas": {
            "a": "As duas opções custam o mesmo",
            "b": "O parcelado tem juros embutidos: quem paga à vista economiza R$ 100",
            "c": "O parcelado é melhor porque não tem juros",
            "d": "O à vista é mais caro porque você paga tudo de uma vez",
        },
        "correta": "b",
        "explicacao": "Se existe desconto à vista, o preço parcelado já inclui um custo extra. "
                      "Parcelar só compensa quando o preço é o mesmo nas duas formas.",
    },
    {
        "codigo": "CREDITO_3",
        "tema": "CREDITO",
        "enunciado": "Se você paga só o valor mínimo da fatura do cartão, o que acontece com o restante?",
        "alternativas": {
            "a": "É perdoado pelo banco",
            "b": "Vai para a próxima fatura sem nenhum acréscimo",
            "c": "Vira dívida no crédito rotativo, com juros muito altos",
            "d": "É dividido automaticamente sem juros",
        },
        "correta": "c",
        "explicacao": "O que fica sem pagar entra no rotativo, um dos créditos mais caros do país. "
                      "Pague a fatura inteira sempre que puder.",
    },
    {
        "codigo": "ORCAMENTO_1",
        "tema": "ORCAMENTO",
        "enunciado": "O que é uma reserva de emergência?",
        "alternativas": {
            "a": "Dinheiro guardado para imprevistos, como um conserto ou a perda da renda",
            "b": "Um limite extra no cartão de crédito",
            "c": "Dinheiro separado para as férias",
            "d": "Um empréstimo pré-aprovado pelo banco",
        },
        "correta": "a",
        "explicacao": "A reserva é seu dinheiro, guardado num lugar seguro e fácil de sacar. Ela evita "
                      "que um imprevisto vire dívida. Limite e empréstimo pré-aprovado são crédito, "
                      "não reserva.",
    },
    {
        "codigo": "ORCAMENTO_2",
        "tema": "ORCAMENTO",
        "enunciado": "Na regra 50-30-20 de orçamento, para que servem os 20%?",
        "alternativas": {
            "a": "Lazer e compras",
            "b": "Contas essenciais, como transporte e alimentação",
            "c": "Presentes e datas especiais",
            "d": "Guardar, investir ou quitar dívidas",
        },
        "correta": "d",
        "explicacao": "A regra sugere 50% para o essencial, 30% para desejos e 20% para o futuro: "
                      "poupar, investir ou quitar dívidas. É um ponto de partida, ajuste à sua realidade.",
    },
    {
        "codigo": "ORCAMENTO_3",
        "tema": "ORCAMENTO",
        "enunciado": "Você recebe R$ 800 por mês e seus gastos somam R$ 850. O que fazer primeiro?",
        "alternativas": {
            "a": "Usar o cheque especial todo mês para cobrir a diferença",
            "b": "Ignorar, porque são só R$ 50",
            "c": "Listar os gastos e cortar os não essenciais até caberem na renda",
            "d": "Parcelar as compras para a conta fechar",
        },
        "correta": "c",
        "explicacao": "Gastar mais do que entra gera dívida todo mês, e cheque especial e parcelamento "
                      "só adiam o problema com juros. O primeiro passo é saber para onde o dinheiro vai.",
    },
    {
        "codigo": "INFLACAO_1",
        "tema": "INFLACAO",
        "enunciado": "O que a inflação faz com o dinheiro parado na carteira?",
        "alternativas": {
            "a": "Ele rende automaticamente",
            "b": "Ele compra menos coisas com o passar do tempo",
            "c": "Ele passa a valer mais",
            "d": "Nada: a inflação só afeta as empresas",
        },
        "correta": "b",
        "explicacao": "Inflação é a alta geral dos preços. A mesma nota de R$ 50 compra menos no ano "
                      "seguinte, por isso dinheiro parado perde poder de compra.",
    },
    {
        "codigo": "INFLACAO_2",
        "tema": "INFLACAO",
        "enunciado": "Qual índice mede a inflação oficial do Brasil?",
        "alternativas": {"a": "Selic", "b": "Ibovespa", "c": "CDI", "d": "IPCA, calculado pelo IBGE"},
        "correta": "d",
        "explicacao": "O IPCA é o índice oficial de inflação. A Selic é a taxa básica de juros, definida "
                      "pelo Banco Central; o CDI é a taxa entre bancos; o Ibovespa mede a bolsa.",
    },
    {
        "codigo": "INFLACAO_3",
        "tema": "INFLACAO",
        "enunciado": "Seu investimento rendeu 6% em um ano e a inflação foi de 4%. Qual foi, mais ou "
                     "menos, o seu ganho real?",
        "alternativas": {"a": "Cerca de 2%", "b": "10%", "c": "6%", "d": "4%"},
        "correta": "a",
        "explicacao": "Ganho real é o que sobra depois da inflação. A conta exata é 1,06 ÷ 1,04 = 1,019: "
                      "cerca de 2% a mais de poder de compra.",
    },
)


def situacao(respostas: dict[str, bool]) -> list[dict]:
    """Cada pergunta do banco com o estado para a tela, na ordem do catálogo.

    Args:
        respostas: {código: acertou} das perguntas que o aluno já respondeu.

    Returns:
        list[dict]: cada pergunta com `tema_nome` e `status`: "NOVA", "ACERTOU" ou "ERROU".
    """
    resultado = []
    for pergunta in PERGUNTAS:
        if pergunta["codigo"] not in respostas:
            status = "NOVA"
        else:
            status = "ACERTOU" if respostas[pergunta["codigo"]] else "ERROU"
        resultado.append({**pergunta, "tema_nome": TEMAS[pergunta["tema"]], "status": status})
    return resultado


def buscar(codigo) -> dict | None:
    """Pergunta do banco pelo código, ou None se não existir."""
    return next((pergunta for pergunta in PERGUNTAS if pergunta["codigo"] == codigo), None)


def xp_do_acerto(ganho_hoje: int) -> int:
    """XP que um acerto rende, respeitando o teto diário do quiz.

    Args:
        ganho_hoje: XP que o aluno já ganhou hoje com o quiz (fuso do Piauí).

    Returns:
        int: `XP_POR_ACERTO`, ou só o que falta para o teto, ou 0. Nunca negativo.
    """
    return max(0, min(XP_POR_ACERTO, TETO_DIARIO_QUIZ - ganho_hoje))


def corrigir(pergunta: dict, escolha) -> bool:
    """Diz se a alternativa escolhida é a correta da pergunta.

    Args:
        pergunta: item do catálogo, com `alternativas` ({id: texto}) e `correta` (id).
        escolha: id enviado pelo formulário ("a" a "d"), ou None/vazio se nada foi marcado.

    Returns:
        bool: True se acertou.

    Raises:
        ErroValidacao: `{"alternativa": ...}` se nada foi escolhido ou se o id não é
            de uma alternativa da pergunta (formulário adulterado).
    """
    escolha = (escolha or "").strip()
    if not escolha:
        raise ErroValidacao({"alternativa": "Escolha uma alternativa."})
    if escolha not in pergunta["alternativas"]:
        raise ErroValidacao({"alternativa": "Escolha uma das alternativas da pergunta."})
    return escolha == pergunta["correta"]
