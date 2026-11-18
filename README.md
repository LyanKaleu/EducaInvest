<div align="center">

<a href="https://github.com/LyanKaleu/EducaInvest/actions/workflows/gate.yml"><img src="https://img.shields.io/github/actions/workflow/status/LyanKaleu/EducaInvest/gate.yml?branch=main&label=gate" alt="Gate do CI"></a>
<img src="https://img.shields.io/badge/python-3.14-1d6b3f?logo=python&logoColor=white" alt="Python 3.14">
<img src="https://img.shields.io/badge/flask-3.1-1d6b3f?logo=flask&logoColor=white" alt="Flask 3.1">
<img src="https://img.shields.io/badge/sqlite-3-1d6b3f?logo=sqlite&logoColor=white" alt="SQLite">

<br><br>

<img src="docs/img/hero.gif" width="100%" alt="EducaInvest: finanças na prática, com cara de jogo. Um celular passa pela tela inicial do aluno, pelo registro de um gasto, pelas missões, pelas metas, pelo quiz e pelo painel do professor.">

**Educação financeira na prática para jovens de 16 a 24 anos.**
O aluno registra o próprio dinheiro, cumpre missões e ganha XP. O professor acompanha a turma sem ver valores.

[Especificação](docs/ESPECIFICACAO.md) · [Telas](#telas) · [Rodar localmente](#rodar-localmente) · [Reportar problema](https://github.com/LyanKaleu/EducaInvest/issues)

</div>

## Por que existe

- **Aprender fazendo.** O jovem até sabe o que é orçamento, mas não pratica. Aqui cada gasto registrado vira progresso.
- **O professor acompanha sem invadir.** Ele vê XP, missões e frequência da turma, nunca valores em reais nem e-mail.
- **Leve e confiável no celular.** Sem JavaScript, e um reenvio depois de a conexão cair não duplica nada.

## Funcionalidades

**Aluno**
- **Lançamentos:** entradas e gastos com categoria, busca e saldo na hora.
- **Missões e XP:** trilha de missões, níveis, conquistas e sequência de dias, com teto diário de XP.
- **Metas:** valor-alvo, aportes e barra de progresso.
- **Quiz:** perguntas sobre juros, crédito, orçamento e inflação, sempre com explicação.

**Professor**
- **Turmas:** cada turma tem um código de 8 caracteres para os alunos entrarem.
- **Painel da turma:** XP médio, missões concluídas, alunos ativos em 7 dias e uma linha por aluno.

## Telas

<table>
  <tr>
    <th align="center">Início</th>
    <th align="center">Lançamentos</th>
    <th align="center">Metas</th>
  </tr>
  <tr>
    <td><img src="docs/img/inicio.jpg" width="250" alt="Tela inicial com saldo, sequência de 4 dias, nível e missão em andamento"></td>
    <td><img src="docs/img/lancamentos.jpg" width="250" alt="Lista de lançamentos com totais de entradas e gastos e cartões com faixa verde ou vermelha"></td>
    <td><img src="docs/img/metas.jpg" width="250" alt="Metas com o total guardado, a barra de progresso e os atalhos de R$ 5, R$ 10 e R$ 20"></td>
  </tr>
  <tr>
    <th align="center">Missões</th>
    <th align="center">Quiz</th>
    <th align="center">Painel do professor</th>
  </tr>
  <tr>
    <td><img src="docs/img/missoes.jpg" width="250" alt="Missões com o nível em destaque, o XP de hoje e a trilha"></td>
    <td><img src="docs/img/quiz.jpg" width="250" alt="Pergunta do quiz respondida, com a alternativa certa marcada e a explicação"></td>
    <td><img src="docs/img/turma.jpg" width="250" alt="Painel da turma com alunos ativos, alerta de inatividade e ranking por XP, sem valores em reais"></td>
  </tr>
</table>

Os dados das telas são fictícios.

## Rodar localmente

Precisa do [uv](https://docs.astral.sh/uv/getting-started/installation/), que instala o Python 3.14 e as versões exatas do `uv.lock`. O banco SQLite é criado sozinho no primeiro acesso.

```bash
git clone https://github.com/LyanKaleu/EducaInvest.git && cd EducaInvest
uv sync          # cria o .venv com o Python e as dependências do uv.lock
uv run run.py    # http://127.0.0.1:5000
```

O `run.py` liga o modo debug: use só na sua máquina e nunca com `host="0.0.0.0"`, porque o depurador deixa executar código no servidor.

Em produção, sirva `create_app()` por um servidor WSGI, com a variável `SECRET_KEY` definida e HTTPS (fora do debug, o cookie de sessão só viaja por HTTPS). O banco fica em `instance/educainvest.db`, que precisa estar num disco que não se apaga ao reiniciar.

## Testes

```bash
bash gate.sh   # lint, contratos de arquitetura e testes (o uv sync já instala as ferramentas)
```

## Próximos passos

- Quiz do dia com perguntas de cálculo que mudam a cada dia.
- Gerador de perguntas com IA, com revisão antes de publicar.
- Desfazer aporte em meta.
- Renomear e excluir turma.
