# Estado do projeto

Ponto de retomada entre sessões e computadores. Atualize no PR que muda a fase ou o próximo passo.
Regras de trabalho ficam no AGENTS.md; aqui fica só **onde estamos**.

**Atualizado em:** 16/11/2026 · **Branch de integração:** `develop` · **Vitrine:** `main`

## Pronto
O escopo do MVP está completo. A especificação v2 está em [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md).

| Item | PR |
|---|---|
| Base, login, perfis e turmas (RF01, RF02) | #1, #2 |
| Setup do Claude Code, gate e CI | #3 |
| Nome de turma único por professor, sem diferenciar maiúsculas | #4 |
| HU1: lançamentos (CRUD, busca, idempotência) | #1 |
| HU3: missões em trilha, XP com teto diário e nível | #8 |
| Perfil visível no cadastro, no login e no topo | #9 |
| Plan mode obrigatório, TDD por seams, skills no AGENTS.md | #10 |
| Tela inicial do aluno: saldo, sequência de dias (RN-13), XP, nível e missão | #12 |
| HU2: metas e aportes (aporte fora do saldo e limitado ao que falta), card da meta na tela inicial | #13 |
| DESIGN.md: guia visual para gerar telas em ferramentas de design | #15 |
| HU5: painel da turma (XP médio, missões, ativos em 7 dias e linha por aluno, sem reais nem e-mail) | #16 |
| HU4: quiz com 12 perguntas, uma resposta por pergunta, 10 XP por acerto e teto de 40 por dia | #19 |
| Arrumação para a `main`: README curto com prints, especificação v2 em Markdown, PDF v1 fora do repositório | #20 |
| MVP completo na `main` | #21 |
| Deploy interno de teste, só para o grupo (onde está e como atualizar: notas privadas, fora do Git) | #22 |
| Correções da auditoria de segurança: limite de login por e-mail, CSRF (Flask-WTF), código de turma com 8 caracteres, cookie `Secure`, headers, sessão de 12 h e aporte sem corrida | #23 |
| Dependências com uv: `uv.lock` fixa a árvore inteira, `.python-version` em 3.14, CI com `uv sync --locked` e Dependabot `uv` | #31 |
| Redesign igual ao protótipo navegável: menu no rodapé, cartões, chips sem JavaScript, sequência de 7 dias, resumo e atalhos nas metas, ranking e inativos no painel da turma | (este PR) |

## Próximo passo
1. Ligar CodeQL e Dependabot security updates (a `main` já recebeu o merge; veja "Setup do GitHub" abaixo).
2. Release `v1.0.0` na `main`. O deploy é interno: nada sobre ele entra no README nem nas notas da release.
3. Executor de migrações (scripts SQL numerados com `PRAGMA user_version`), antes da primeira alteração de tabela com dados no deploy.
4. PWA sobre o visual novo (o redesign já seguiu o protótipo navegável): manifest e service worker, com JavaScript só como melhoria progressiva.

Fly e Render foram descartados: a Fly exige cartão e o Render grátis apaga o SQLite quando o app dorme. Container (`gunicorn`, `Dockerfile`) só volta se o banco sair do SQLite local.

Arquitetura decidida em 16/11/2026: monólito Flask em camadas, `sqlite3` sem ORM, PWA sobre o Jinja e PostgreSQL só quando um gatilho acontecer. O porquê, os limites e os gatilhos ficam no AGENTS.md, seção "Arquitetura".

## Setup do GitHub (depois do merge na `main`)
- **CodeQL** e **Dependabot security updates:** ligar depois do merge na `main`, porque os dois olham a branch padrão.
- **Dependabot de versões:** `.github/dependabot.yml` criado (pip e github-actions, toda segunda, PR para a `develop`, minor e patch agrupados, major em PR separado). Só passa a valer depois do merge na `main`. É zona O3.
- **Discussions e Projects:** só se a equipe for usar de verdade. Wiki e Packages ficam desligados.
- Já ligados em 11/11: varredura de segredos, push protection, alertas do Dependabot e o ruleset `protege-main-develop` (`main` e `develop` só recebem mudança por PR com o check `gate` verde, sem force push e sem apagar a branch).

## Backlog (issues abertas)
- #5 professor renomeia turma
- #6 professor exclui turma vazia (bloqueada com alunos). `PRAGMA foreign_keys` já fica ligado na conexão (`app/db.py`), então o `ON DELETE CASCADE` de `matriculas` já funciona: falta só a rota de exclusão.
- #7 busca/filtro na lista de turmas
- #14 id gigante na URL responde 500 em vez de 404 (metas e lançamentos)
- Limite de login vale por processo e zera ao reiniciar (`limite_service.py`). Se o deploy passar a ter vários workers, mover a contagem para o banco.
- Aceitar aporte acima da meta junto com "desfazer aporte" (hoje o aporte para no que falta, porque não há como desfazer)
- **Universitários:** usar o app sem entrar numa turma, já que nem sempre há um professor acompanhando. A faixa de 16 a 24 anos já cobre esse público.
- **Ensino fundamental:** produto à parte, mais lúdico, com outra linguagem. Abaixo de 12 anos a LGPD (art. 14) exige o consentimento específico de um dos pais ou responsável, que o RN-05 de hoje não cobre.
- **Mascote** próprio para a marca e a divulgação.
- Do protótipo, o que ficou de fora por precisar de JavaScript: avisos que somem sozinhos, comemoração de nível, busca ao digitar e sugestões de nome na nova meta.
- **Quiz do dia** com perguntas de cálculo parametrizadas (números novos por aluno e por dia, resposta calculada pelo código, sem IA) e **gerador de perguntas com IA**. O texto das 12 perguntas atuais precisa de revisão.
  - O gerador é um comando Python que chama a API de IA direto, sem n8n nem Zapier (seria mais um serviço e uma credencial fora do gate). Ele pede um lote em JSON com schema e valida com as regras do `quiz_service`.
  - O lote vai para um arquivo no repositório, ao lado do `PERGUNTAS`, e não para o banco: o PR é a revisão humana, e o código da pergunta continua imutável depois de publicado.
  - A geração é offline, em lote, nunca na hora da resposta, e nenhum dado de aluno vai para a API.
- **Supabase (só o Postgres, sem o Supabase Auth)** junto com a troca de deploy, nunca antes. Tirar o banco do servidor libera um host que dorme ou serverless (Render, Koyeb, Cloud Run, Vercel) e vários workers. Também leva o limite de login para o banco, porque em serverless a contagem por processo deixa de proteger.
  - Custo: `psycopg` (dependência nova), `CREATE TABLE` reescritos (O1), `COLLATE NOCASE` (N3) virando `citext` ou índice em `lower()`, gatilhos do XP (N6) em outra sintaxe e banco de teste para a suíte.
  - Ponto de partida: o schema PostgreSQL de referência em `docs/`. Antes de decidir, conferir se o plano grátis ainda pausa o projeto parado.
- **Paperclip (orquestrador de agentes, open source)**, avaliado em 17/11/2026 e adiado. Ele comanda Claude Code, Codex e Gemini CLI por heartbeat, com organograma, orçamento e aprovações. O Antigravity não entra, porque é uma IDE, não um CLI.
  - Por que não agora: os adaptadores rodam em modo automático (sem plan mode aprovado nem TDD com o teste vermelho), o hook `protege.py` e o Stop hook só valem para o Claude, o adaptador do Gemini não isola a árvore de trabalho, a documentação não cita Windows e cada heartbeat gasta a cota das assinaturas. Também não há tarefa paralela em volume: o próximo passo é sequencial.
  - Quando reavaliar: tarefa recorrente e autônoma com revisão no PR (ex.: o gerador de perguntas do quiz), sempre com o check `gate` como rede comum.
  - Enquanto isso: Claude Code implementa, Codex dá a segunda opinião na revisão do PR e Antigravity/Gemini ficam com protótipo de tela e teste no navegador, cada um na sua branch ou worktree, todos lendo o `AGENTS.md`.

## Decisões pendentes
- Lista de categorias e valor máximo do lançamento ("A confirmar" em `lancamento_service.py`).
- Valores de XP, teto diário e níveis. Quiz: 10 XP por acerto e teto de 40 por dia (`quiz_service.py`).
- Escola como entidade do produto (várias escolas, papel de gestor), antes de qualquer expansão.
- Tema escuro entra no design system? (A faixa lateral ficou, nos itens de lista, como no protótipo.)
- "Dia ativo" e a janela de 7 dias do painel do professor (`JANELA_FREQUENCIA_DIAS` em `turma_service.py`).

## Riscos de segurança aceitos (MVP)
- **Enumeração de e-mail no cadastro:** `/cadastro` responde "e-mail já cadastrado" para e-mail existente, então dá para descobrir quais e-mails têm conta. Aceito: o dado é de baixo valor (apelido, contexto escolar), sem envio de e-mail não dá para o "cadastro silencioso", e limitar por IP brigaria com a turma saindo pelo mesmo Wi-Fi (por isso o login limita por e-mail). Revisitar só se entrar verificação por e-mail. Achado da auditoria de 17/11 (BugHunter); o resto veio limpo.

## Em andamento
Redesign (`feature/redesign-v2`) em revisão. Depois, a release.
