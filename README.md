# EducaInvest

**Gestão financeira gamificada para jovens de 16 a 24 anos.** O aluno registra entradas, gastos e metas, e o sistema transforma esses registros em missões com XP. O professor cria a turma e acompanha o progresso agregado.

Protótipo (MVP) web, leve e mobile-first, feito para funcionar bem no celular e com conexão instável. Desenvolvido como projeto da disciplina de Empreendedorismo.

> **Estado atual:** protótipo em desenvolvimento. Estão implementados **contas, login e turmas**, o **registro de entradas e gastos**, as **missões com XP e nível** e a **tela inicial do aluno**, com saldo e sequência de dias. O que ainda falta está listado em [Em desenvolvimento](#em-desenvolvimento).

---

## Funcionalidades

### Prontas: contas, login e turmas (RF01, RF02)

- **Cadastro de aluno** com apelido (2 a 40 caracteres), e-mail, senha (8 a 128 caracteres), **código da turma** e uma caixa de **autorização obrigatória** ("tenho 18 anos ou mais, ou autorização do responsável ou da escola"). A data e a hora do aceite ficam gravadas (RN-05).
- **Cadastro de professor** aberto, com apelido, e-mail e senha.
- **Login por e-mail e senha.** A mensagem de erro é a mesma para e-mail inexistente e para senha errada. A senha é guardada só como hash e nunca volta preenchida na página.
- **Sair** encerra a sessão. Por segurança, isso só funciona pelo botão (envio `POST`).
- **Acesso por perfil:** sem login, o visitante vai para a tela de entrar. O aluno não acessa as páginas do professor, e o professor não acessa os lançamentos (403).
- **Turmas do professor:** criar turma (nome único por professor, até 60 caracteres) com um **código de acesso de 6 caracteres**, sem os que se confundem (0/O, 1/I/L). A página da turma mostra o **apelido** dos alunos matriculados, nunca o e-mail.

### Prontas: registro de entradas e gastos (HU1)

- **Listar** os lançamentos do aluno, do mais recente para o mais antigo, com valor em reais (`R$ 1.234,50`) e data no formato brasileiro (`04/11/2026`).
- **Buscar** por categoria ou descrição.
- **Criar, editar e excluir** lançamentos. A exclusão pede confirmação, e só um envio `POST` apaga o registro.
- **Validação com mensagens em português** junto a cada campo. O formulário volta preenchido (status 400) quando há erro:
  - tipo: entrada ou gasto;
  - categoria de uma lista fixa, compatível com o tipo;
  - valor maior que zero, até R$ 100.000,00, aceitando `25`, `25,50`, `25.50` e `1.234,56`;
  - data não futura no fuso do Piauí (UTC−3); se ficar vazia, vale o dia de hoje; aceita `dd/mm/aaaa` e `aaaa-mm-dd`;
  - descrição opcional, de até 140 caracteres.
- **Sem lançamentos duplicados:** cada formulário leva uma chave única. Se o envio se repetir (clique duplo, ou reenvio depois de uma falha de rede), o lançamento é gravado uma vez só.
- **Isolamento entre alunos:** cada aluno só vê, edita e exclui os próprios lançamentos. O registro de outro aluno responde 404.
- **Acessibilidade:** HTML semântico, link "Pular para o conteúdo", mensagens anunciadas por leitores de tela, foco visível, áreas de toque de 44px e contraste AA. Não usa JavaScript.

### Prontas: missões, XP e nível (HU3)

- **Missões em trilha:** a tela **Missões** mostra o progresso de cada missão (por exemplo, "2 de 3") a partir dos lançamentos do aluno. Concluir uma missão dá XP, aparece como **conquista** e libera a próxima. Cada missão é concluída uma vez só, mesmo que o aluno exclua registros depois.
  - "Primeiros passos": registre 3 gastos (+30 XP).
  - "Hábito em construção": registre 7 lançamentos (+50 XP), liberada pela anterior.
- **XP por registro:** cada lançamento novo rende 10 XP, com **teto diário de 50 XP** de registros (fuso do Piauí). Depois do teto, o lançamento é salvo normalmente e o aluno vê um aviso. Editar não rende XP de registro, e o reenvio do mesmo formulário não pontua duas vezes.
- **Nível pelo XP acumulado:** Iniciante (0), Aprendiz (100) e Organizado (300). A tela mostra quanto falta para o próximo nível e avisa quando o aluno sobe.
- **XP nunca diminui nem duplica:** o XP fica num livro-razão só de inserções, e o banco recusa alterar ou apagar um evento. O lançamento e o XP que ele gera são gravados na mesma transação: ou os dois, ou nenhum.
- Os valores de XP, teto e níveis são exemplos da especificação e ainda serão confirmados pelo grupo.

### Prontas: tela inicial do aluno, com saldo e sequência de dias

Depois de entrar, o aluno cai no **Início**, que mostra:

- o **saldo** (entradas menos gastos), com o total de cada um. O saldo negativo aparece como `-R$ 10,50`, em vermelho;
- o botão **Registrar gasto**, que abre o formulário com gasto e a data de hoje já preenchidos;
- a **sequência de dias** (RN-13): dias seguidos em que o aluno ganhou XP, no fuso do Piauí. O dia de hoje ainda não acabou, então só um dia inteiro em branco zera a sequência;
- **XP e nível**, com quanto falta para o próximo;
- a **missão em andamento**, com a barra de progresso.

### Em desenvolvimento

Estes itens têm arquivos reservados na estrutura de pastas, mas **ainda não têm código**:

| Funcionalidade | Situação |
|---|---|
| Metas e aportes (HU2) | Não iniciado |
| Quizzes (HU4) | Não iniciado |
| Painel agregado do professor: XP médio, missões e frequência (HU5) | Não iniciado (hoje a turma mostra só a lista de alunos) |

---

## Pré-requisitos

- **Python 3.10 ou mais recente** (desenvolvido e testado com Python 3.14)
- **Git**
- Não é preciso instalar banco de dados: o projeto usa **SQLite**, que já vem com o Python.

---

## Instalação

```bash
git clone https://github.com/LyanKaleu/EducaInvest.git
cd EducaInvest
python -m venv .venv
```

Ative o ambiente virtual:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Windows (Git Bash) | `source .venv/Scripts/activate` |
| Linux / macOS | `source .venv/bin/activate` |

> No PowerShell, se a ativação for bloqueada, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Instale as dependências (Flask e pytest):

```bash
python -m pip install -r requirements.txt
```

---

## Como rodar

```bash
python run.py
```

Abra **http://127.0.0.1:5000** no navegador. Em desenvolvimento não é preciso definir `SECRET_KEY`: o `run.py` liga o modo debug, que gera uma chave temporária.

Para experimentar o fluxo completo:

1. Clique em **Criar conta** e depois em **Cadastre-se como professor**.
2. Crie uma turma (por exemplo, "2º A") e anote o **código de acesso**.
3. Clique em **Sair**, crie uma conta de **aluno** com esse código e registre um gasto.
4. Entre de novo como professor: o aluno aparece na página da turma.

- O banco é criado sozinho no primeiro acesso, em `instance/educainvest.db`. Essa pasta fica fora do Git.
- Em produção, não use o `run.py`. Use a fábrica do app (por exemplo, `gunicorn "app:create_app()"`) com a `SECRET_KEY` definida.
- Para ver como fica no celular, abra as ferramentas do navegador (F12) e ative o modo dispositivo (Ctrl+Shift+M).

---

## Como testar

```bash
pytest
```

Para ver o nome de cada teste:

```bash
pytest -v
```

| Pasta | O que testa |
|---|---|
| `tests/unit/` | Regras de negócio (services), sem Flask e sem banco |
| `tests/integration/` | Rotas HTTP, cada teste com um banco SQLite novo em pasta temporária |

O projeto é desenvolvido com **TDD**: os testes de cada funcionalidade são escritos antes do código.

---

## Estrutura de pastas

As camadas seguem um único sentido: **routes → services → repositories → banco**.

```
EducaInvest/
├── app/
│   ├── __init__.py              # create_app(): configura o app, liga o banco e registra as rotas
│   ├── db.py                    # conexão SQLite: uma por requisição, fechada no fim
│   ├── filtros.py               # filtros Jinja `reais` (R$ 1.234,56) e `data_br` (04/11/2026)
│   ├── routes/                  # recebem a requisição HTTP e devolvem a página
│   │   ├── acesso.py            #   exigir_perfil(): login + perfil para um Blueprint inteiro
│   │   ├── auth.py              #   cadastro (aluno e professor), login e logout
│   │   ├── professor.py         #   turmas do professor (só perfil PROFESSOR)
│   │   ├── lancamentos.py       #   CRUD de lançamentos (só perfil ALUNO)
│   │   ├── missoes.py           #   tela de missões e registrar_progresso() (XP na transação do lançamento)
│   │   └── painel.py            #   tela inicial do aluno: saldo, XP, nível, sequência e missão (só ALUNO)
│   ├── services/                # regras de negócio: sem SQL e sem Flask
│   │   ├── erros.py             #   ErroValidacao (campo → mensagem)
│   │   ├── formulario.py        #   texto_do_campo(): leitura de campo de formulário
│   │   ├── auth_service.py      #   perfis, validação de cadastro/login e hash de senha
│   │   ├── turma_service.py     #   nome da turma e código de acesso
│   │   ├── lancamento_service.py#   validar_lancamento()
│   │   ├── missao_service.py    #   trilha de missões: progresso, conclusão e desbloqueio
│   │   └── xp_service.py        #   XP por lançamento com teto diário e nível
│   ├── repositories/            # único lugar com SQL, sempre com parâmetros (?)
│   │   ├── conversao.py         #   linha_para_dict()
│   │   ├── usuario_repo.py      #   tabela usuarios
│   │   ├── turma_repo.py        #   tabelas turmas e matriculas
│   │   ├── lancamento_repo.py   #   tabela lancamentos (CRUD)
│   │   ├── missao_repo.py       #   tabela missoes_concluidas
│   │   └── xp_repo.py           #   tabela xp_eventos (livro-razão de XP, só inserções)
│   ├── templates/
│   │   ├── base.html            #   layout, menu por perfil e mensagens (flash)
│   │   ├── _formulario.html     #   macros `erro` e `invalido` dos formulários
│   │   ├── auth/                #   cadastro, login
│   │   ├── aluno/               #   painel, lancamentos, lancamento_form, lancamento_excluir, missoes
│   │   └── professor/           #   turmas, turma
│   └── static/css/app.css       # estilo único, sem framework
├── tests/
│   ├── conftest.py              # fixtures: app de teste, banco temporário, clientes HTTP
│   ├── unit/
│   └── integration/
├── docs/
│   ├── EducaInvest_Especificacao_MVP.pdf   # requisitos, regras e histórias
│   └── educainvest_schema.sql              # modelo de dados de referência (PostgreSQL)
├── run.py                       # inicia o servidor de desenvolvimento
├── requirements.txt
└── pytest.ini
```

Os arquivos de **metas e quiz** em `routes/`, `services/`, `repositories/` e `templates/`, além de `professor/progresso.html`, são **reservas**: por enquanto só têm uma linha de descrição. O mesmo vale para `app/config.py` e `db/schema.sql`.

---

## Variáveis de ambiente

| Variável | Obrigatória | Para que serve |
|---|---|---|
| `SECRET_KEY` | **Sim**, fora de teste e de debug | Assina o cookie de sessão, que guarda o login e as mensagens. **Sem ela, o app se recusa a iniciar** com uma mensagem explicando como gerar uma. Em teste e em debug (`python run.py`), uma chave temporária é gerada, e as sessões caem quando o servidor reinicia. |

Para definir a variável:

```powershell
# PowerShell
$env:SECRET_KEY = "uma-chave-longa-e-aleatoria"
```

```bash
# Linux / macOS / Git Bash
export SECRET_KEY="uma-chave-longa-e-aleatoria"
```

Para gerar uma chave: `python -c "import secrets; print(secrets.token_hex(32))"`

### Configurações internas (não são variáveis de ambiente)

Estas configurações são passadas em código, por `create_app({...})`, e servem para testes e desenvolvimento:

| Chave | Padrão | Uso |
|---|---|---|
| `DATABASE` | `instance/educainvest.db` | Caminho do arquivo SQLite. Os testes usam uma pasta temporária. |
| `TESTING` | `False` | Modo de teste do Flask. Dispensa a `SECRET_KEY`. |
| `DEBUG` | `False` (o `run.py` usa `True`) | Modo de desenvolvimento. Dispensa a `SECRET_KEY`. |

---

## Documentação

- [Especificação do MVP](docs/EducaInvest_Especificacao_MVP.pdf): requisitos, regras de negócio, histórias com critérios de aceite, escopo e riscos.
- [Modelo de dados](docs/educainvest_schema.sql): o schema completo de referência, com 16 tabelas em PostgreSQL. A versão em SQLite está sendo implementada aos poucos, junto com cada funcionalidade.
