# Estado do projeto

Ponto de retomada entre sessões e computadores: aqui fica só **onde estamos**. Regras de trabalho ficam no AGENTS.md; o que já foi entregue e as decisões antigas, no [HISTORICO.md](HISTORICO.md).
Ao fechar um PR, a linha dele vai para o HISTORICO.md, e este arquivo muda só se a fase, o próximo passo ou o backlog mudou.

**Atualizado em:** 18/11/2026 · **Branch de integração:** `develop` · **Vitrine:** `main`

## Em andamento
O MVP está completo e na `main` (PRs #1 a #41). Na branch `chore/subagentes-papeis`: subagentes `produto`, `designer` e `seguranca` e o contexto enxuto (AGENTS.md sem o que o código já mostra, histórico no HISTORICO.md).

## Próximo passo
1. Ligar CodeQL e Dependabot security updates no GitHub (os dois olham a `main`, que já recebeu o merge).
2. Release `v1.0.0` na `main`. O deploy é interno: nada sobre ele entra no README nem nas notas da release.
3. Executor de migrações (scripts SQL numerados com `PRAGMA user_version`), antes da primeira alteração de tabela com dados no deploy.
4. PWA sobre o visual novo: manifest e service worker, sobre o JS de melhoria progressiva que já existe em `app/static/js/`. O botão de troca de tema entra junto (veja o backlog).

Arquitetura decidida em 16/11/2026 (monólito Flask em camadas, `sqlite3` sem ORM, PostgreSQL só com gatilho): o porquê, os limites e os gatilhos ficam no AGENTS.md, seção "Arquitetura".

## Backlog (issues abertas)
- #5 professor renomeia turma
- #6 professor exclui turma vazia (bloqueada com alunos). `PRAGMA foreign_keys` já fica ligado na conexão (`app/db.py`), então o `ON DELETE CASCADE` de `matriculas` já funciona: falta só a rota de exclusão.
- #7 busca/filtro na lista de turmas
- #33 verificador de tipos (mypy ou pyright) no gate: dependência nova, zona O3, precisa de aprovação
- #14 id gigante na URL responde 500 em vez de 404 (metas e lançamentos)
- Limite de login vale por processo e zera ao reiniciar (`limite_service.py`). Se o deploy passar a ter vários workers, mover a contagem para o banco.
- Aceitar aporte acima da meta junto com "desfazer aporte" (hoje o aporte para no que falta, porque não há como desfazer)
- **Universitários:** usar o app sem entrar numa turma, já que nem sempre há um professor acompanhando. A faixa de 16 a 24 anos já cobre esse público.
- **Ensino fundamental:** produto à parte, mais lúdico, com outra linguagem. Abaixo de 12 anos a LGPD (art. 14) exige o consentimento específico de um dos pais ou responsável, que o RN-05 de hoje não cobre.
- **Mascote** próprio para a marca e a divulgação.
- **Botão de troca de tema** (claro, escuro ou o do sistema), junto com o PWA. Hoje o tema escuro segue o tema do sistema, sem botão; a escolha manual precisa ser guardada (cookie ou JavaScript), e no celular o tema do sistema já resolve.
- Do protótipo, o que ainda falta e precisa de JavaScript: busca ao digitar e sugestões de nome na nova meta.
- **Quiz do dia** com perguntas de cálculo parametrizadas (números novos por aluno e por dia, resposta calculada pelo código, sem IA) e **gerador de perguntas com IA**. O texto das 12 perguntas atuais precisa de revisão.
  - O gerador é um comando Python que chama a API de IA direto, sem n8n nem Zapier (seria mais um serviço e uma credencial fora do gate). Ele pede um lote em JSON com schema e valida com as regras do `quiz_service`.
  - O lote vai para um arquivo no repositório, ao lado do `PERGUNTAS`, e não para o banco: o PR é a revisão humana, e o código da pergunta continua imutável depois de publicado.
  - A geração é offline, em lote, nunca na hora da resposta, e nenhum dado de aluno vai para a API.
- **Supabase (só o Postgres, sem o Supabase Auth)** junto com a troca de deploy, nunca antes. Tirar o banco do servidor libera um host que dorme ou serverless (Render, Koyeb, Cloud Run, Vercel) e vários workers. Também leva o limite de login para o banco, porque em serverless a contagem por processo deixa de proteger.
  - Custo: `psycopg` (dependência nova), `CREATE TABLE` reescritos (O1), `COLLATE NOCASE` (N3) virando `citext` ou índice em `lower()`, gatilhos do XP (N6) em outra sintaxe e banco de teste para a suíte.
  - Ponto de partida: o schema PostgreSQL de referência em `docs/`. Antes de decidir, conferir se o plano grátis ainda pausa o projeto parado.
- **Paperclip** (orquestrador de agentes): avaliado em 17/11/2026 e adiado; o porquê e quando reavaliar estão no HISTORICO.md.

## Decisões pendentes
- Lista de categorias e valor máximo do lançamento ("A confirmar" em `lancamento_service.py`).
- Valores de XP, teto diário e níveis. Quiz: 10 XP por acerto e teto de 40 por dia (`quiz_service.py`).
- Escola como entidade do produto (várias escolas, papel de gestor), antes de qualquer expansão.
- "Dia ativo" e a janela de 7 dias do painel do professor (`JANELA_FREQUENCIA_DIAS` em `turma_service.py`).

## Riscos de segurança aceitos (MVP)
- **Enumeração de e-mail no cadastro:** `/cadastro` responde "e-mail já cadastrado" para e-mail existente, então dá para descobrir quais e-mails têm conta. Aceito: o dado é de baixo valor (apelido, contexto escolar), sem envio de e-mail não dá para o "cadastro silencioso", e limitar por IP brigaria com a turma saindo pelo mesmo Wi-Fi (por isso o login limita por e-mail). Revisitar só se entrar verificação por e-mail. Achado da auditoria de 17/11 (BugHunter); o resto veio limpo.
