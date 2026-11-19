# EducaInvest: instruções para agentes de código

Protótipo (MVP) de gestão financeira gamificada para jovens de 16 a 24 anos.
Priorize o núcleo demonstrável. Nada de abstração "para o futuro".

## Stack
Python 3.14 · Flask 3.1 · SQLite via `sqlite3` da stdlib (sem ORM) · Jinja renderizado no servidor, com JS puro só como melhoria progressiva (`app/static/js/`, sem framework e sem build) · pytest

## Comandos
Dependências com [uv](https://docs.astral.sh/uv/): o `uv.lock` fixa a árvore inteira e o `.python-version` fixa o Python (3.14). Os mesmos comandos valem no Git Bash e no PowerShell.

```
uv sync                               instala o Python e a árvore do uv.lock em .venv/ (com as ferramentas do gate)
bash gate.sh                          portão: formato → lint → arquitetura → testes (o mesmo do CI)
bash gate.sh --sem-testes             só formato + lint + arquitetura (passo 1 do TDD)
uv run ruff format .                  formata (79 colunas, aspas duplas); o gate só confere
uv run ruff check --fix .             lint com as correções automáticas seguras
uv run pytest -q tests/x.py::nome     teste único (PREFIRA durante a implementação)
uv run pytest -q                      suíte inteira
uv run run.py                         servidor de desenvolvimento (debug)
uv add pacote==x.y / uv add --dev     dependência nova (pergunte antes): grava no pyproject.toml e no uv.lock
uv lock --upgrade-package pacote      sobe só esse pacote
```
Nunca edite o `uv.lock` à mão nem volte com `requirements*.txt`. O CI roda `uv sync --locked`, que falha se o lock estiver atrasado em relação ao `pyproject.toml`.

O Stop hook roda o gate quando há arquivo alterado. Mudança só em `tests/` roda sem a suíte, porque o teste novo ainda está vermelho.

## Estrutura
```
app/routes/        Blueprints HTTP: leem o request, chamam service/repositório, renderizam
app/services/      regras de negócio (validação, cálculo). SEM flask e SEM sqlite3
app/repositories/  SQL com sqlite3. O CREATE TABLE em criar_tabela() é a fonte da verdade do schema
app/templates/     Jinja: auth/, aluno/, professor/
tests/unit/        services, sem Flask
tests/integration/ rotas via test_client com banco temporário (fixtures em tests/conftest.py)
docs/              especificação do MVP (ESPECIFICACAO.md), prints do README (img/) e schema de referência em PostgreSQL
```
- O código de uma pergunta do quiz (`PERGUNTAS` em `quiz_service`) não muda depois de publicado: as respostas gravadas apontam para ele.

## Arquitetura (decidida em 16/11/2026)
Monólito Flask em camadas, com HTML renderizado no servidor. Não troque framework, banco ou camada enquanto um gatilho abaixo não tiver acontecido de fato. "Parece melhor" ou "é mais usado" não é gatilho.
- **Por quê:** o problema é CRUD com regras de integridade (dinheiro, XP, idempotência) para alunos no celular com rede ruim. Um processo, um deploy e páginas leves resolvem isso com o menor número de partes móveis, e o grupo domina Python.
- **O que ela garante:** regra de negócio testável sem Flask (contratos do import-linter), todo o SQL isolado em `app/repositories/` e reenvio sem duplicar (N2).
- **Limites conhecidos:** um processo e um arquivo de banco; estado em memória que vale por processo (limite de login); nenhuma migração de schema; nenhuma entidade escola nem papel de gestor; interação só com recarga de página.
- **Não entra sem gatilho:** ORM, schemas (pydantic, marshmallow), camada de API, framework de JavaScript, Docker/Gunicorn, Redis/Celery, microsserviços, troca para Django ou FastAPI.
- **Evolução, nesta ordem:**
  1. Executor de migrações: scripts SQL numerados com `PRAGMA user_version`, sem dependência nova. Entra antes da primeira alteração de tabela com dados reais.
  2. PWA (manifest e service worker) sobre o JS de melhoria progressiva, que já existe desde o movimento (`app/static/js/`): toda tela continua funcionando sem ele.
  3. PostgreSQL: os repositórios são reescritos com as mesmas assinaturas, e o estado em memória vai para o banco. SQLAlchemy Core e Alembic são avaliados nesse momento, não antes.
  4. `app/api/` ao lado de `app/routes/`, chamando os mesmos services, só se um cliente nativo for necessário.
- **Gatilhos, ou quando a arquitetura atual deixa de servir:**
  - mais de um processo ou servidor escrevendo: PostgreSQL;
  - várias escolas ou backup automático obrigatório: PostgreSQL e modelo de escola;
  - app na App Store, câmera, biometria ou widget: API e cliente nativo;
  - entrada em JSON vinda de fora (o lote do gerador de perguntas com IA ou o corpo da `app/api/`): Pydantic só nessa fronteira. Os formulários continuam com `ErroValidacao` nos services, porque a regra de negócio depende do banco e do relógio e a mensagem é em português, por campo;
  - um domínio com mais de uns 5 arquivos por camada, ou duas pessoas se atrapalhando no mesmo diretório: fatias por domínio;
  - gargalo medido, não suposto: cache ou fila.

## Convenções que divergem do padrão
- Nomes, docstrings, testes e mensagens ao usuário em português.
- Estilo: PEP 8 a 79 colunas, aplicado pelo `ruff format` e pelas regras do `[tool.ruff.lint]` no pyproject (lá está o porquê de cada família que entra e que fica de fora). Função e método públicos de `app/` têm docstring no estilo Google, e todo código, inclusive os testes, tem anotação de tipo.
- Erro de validação: `ErroValidacao({campo: mensagem})` (app/services/erros.py). A rota renderiza o formulário de novo com status 400 e preserva o que foi digitado.
- Dinheiro em centavos (`int`), nunca `float`. O "hoje" vem de `hoje_no_piaui()` (UTC−3).
- Registro de outro usuário responde 404, não 403: não revela que o id existe.
- Rota nova: Blueprint com `before_request(exigir_perfil(...))`. Rota pública só entra pela lista `ROTAS_PUBLICAS` em tests/integration/test_rotas_protegidas.py.
- Tabela nova: `criar_tabela()` no repositório e chamada em app/db.py.
- Formulário POST novo leva `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` (Flask-WTF). O meta-teste em tests/integration/test_seguranca.py acusa o que faltar. Nos testes o CSRF fica desligado (`WTF_CSRF_ENABLED=False` em tests/conftest.py).
- Tela nova ou alterada segue o DESIGN.md. Sem `style` inline (a CSP bloqueia), e a tela funciona sem JavaScript: escolhas são rádios estilizados com `:has`. O JS de `app/static/js/` só acrescenta (movimento, pílula, contador): nunca é o único caminho, nunca é inline (a CSP bloqueia) e o CSS que depende dele fica sob `.js`.
- Antes de criar um arquivo, abra o irmão equivalente (ex.: os `lancamento_*`) e siga o padrão dele.

## Fluxo de trabalho
- **Sempre comece pelo plan mode** antes de escrever código, seja funcionalidade nova ou continuação de uma, por menor que seja. Só implemente depois que o plano for aprovado. Mudança só em documentação pode ir direto. Pergunte antes de implementar feature vaga.
- O plano traz a tarefa em 4 campos (Goal, Context, Constraints e Done when, verificável por máquina), as **seams** a testar (a interface pública de cada teste, com uma linha sobre o que ela pega e o que deixa passar) e as skills que serão usadas.
- TDD em fatias verticais, uma por vez:
  1. Um teste numa seam aprovada: rode e mostre a falha.
  2. A implementação mínima para ele passar. Repita o passo 1 com o próximo teste.
  3. No fim, sugira refatorações (na revisão, fora do ciclo).
- Teste pela interface pública, com valor esperado escrito à mão (nunca recalculado do jeito que o código calcula). Mock só em fronteira do sistema (tempo, ambiente, falha de banco simulada).
- Teste de correção precisa FALHAR se a correção for revertida.
- Antes do PR: revisão pelo subagente `revisor`, em contexto novo. Na triagem, recuse estilo e especulação.
- Os outros papéis entram por fase, só leitura, em `.claude/agents/`: `produto` antes do plano (ideia vaga vira HU e tarefa em 4 campos), `designer` antes e depois de mexer numa tela (contra o DESIGN.md) e `seguranca` antes do PR que toca rota, formulário, SQL, sessão, dados de aluno ou dependência. Codex e Gemini não carregam subagentes: leem o mesmo `.md` como instrução.
- PR com a saída real do `bash gate.sh`, os testes novos e os invariantes tocados. Afirmação sem evidência não vale.
- Saídas curtas: `pytest -q`. Nunca cole log inteiro; use `tail -n 30`.

## Skills
Carregue a skill quando a tarefa chegar nela e cite no plano quais vai usar. Se uma skill não estiver instalada, siga a regra resumida aqui.
- `dev-dirigido-por-ia`: o método deste projeto (tarefa em 4 campos, ciclo de 8 passos, revisão em contexto novo, PR com evidência, uma tarefa por sessão). Exceção: a skill diz para pular o plano quando o diff cabe numa frase; aqui o plan mode é sempre obrigatório.
- `engenheiro-software-ia`: postura em toda tarefa (recomende um caminho e justifique, questione pedido ambíguo, prefira o simples, diga o que foi verificado e o que não foi).
- `tdd`: todo código novo ou correção (seams, fatias verticais, anti-padrões de teste).
- `ui-taste`: toda tela nova ou alterada. Mantenha o visual atual (CSS em `app/static/css/`, um arquivo por assunto, sem framework; JS só como melhoria progressiva) e, antes de dar como pronta, abra a tela no celular (375px) e no desktop e confira os estados (vazio, erro, sucesso).
- `transitions-dev` e `transitions-polish` (transitions.dev): toda transição nova e todo ajuste de tempo. O padrão vem da referência da transição; o tempo, dos tokens de movimento do `tokens.css` (o uso decide o token, não o número mais próximo).
- `design-taste-frontend` (tasteskill.dev): só as referências de movimento e acabamento. Os scripts dela pedem Node, que o projeto não usa.
- `seo-audit`: não se aplica ao MVP (o app fica atrás de login). Não adicione nada de SEO.

## Git (regras do grupo)
- Commit: `tipo(escopo): descrição`, em português, no imperativo ("adiciona", não "adicionei"), minúscula depois dos dois-pontos, sem ponto final.
- Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- Escopos:
  - domínio: `lancamentos`, `auth`, `turmas`, `metas`, `missoes`, `xp`, `quiz`, `painel`;
  - técnicos: `db`, `ui`, `seguranca`, `config`, `deps`, `testes`;
  - documentação: `readme`, `docs`.
- `main` (produção) e `develop` (integração) nunca recebem commit direto. Trabalhe em `feature/xxx` ou `fix/xxx` (kebab-case) e abra sempre um PR.
- Um commit é uma mudança lógica. Nunca commite `.env`.

## Proibido
- Instalar dependência sem perguntar (`pyproject.toml`, `uv.lock`).
- Alterar CREATE TABLE existente, autenticação/sessão ou `SECRET_KEY` sem aprovação (INVARIANTES, seção operacional).
- "Consertar" o gate relaxando regra: `noqa`, `ignore` no pyproject, contrato removido, teste ajustado para passar. Corrija a causa. A única exceção é o falso positivo provado: `# noqa: REGRA` com o motivo num comentário junto (na linha ou logo acima), revisado no PR (ex.: o S608 nos `IN (?, ?)` dos repositórios).
- Publicar arquivo de `docs/` além dos liberados no `.gitignore`. Os outros documentos são privados.

## Decisões pendentes do grupo
- Lista de categorias e valor máximo do lançamento (marcados "A confirmar" em app/services/lancamento_service.py).
- Escola como entidade do produto (várias escolas, papel de gestor). Muda o modelo e o controle de acesso, por isso precisa ser decidida antes de expandir.

## Invariantes
Ver INVARIANTES.md. Se a tarefa parece exigir violar um deles, PARE e pergunte.
