# Estado do projeto

Ponto de retomada entre sessões e computadores. Atualize no PR que muda a fase ou o próximo passo.
Regras de trabalho ficam no AGENTS.md; aqui fica só **onde estamos**.

**Atualizado em:** 11/11/2026 · **Branch de integração:** `develop` · **Vitrine:** `main`

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
| Arrumação para a `main`: README curto com prints, especificação v2 em Markdown, PDF v1 fora do repositório | (este PR) |

## Próximo passo
1. PR `develop → main` com o MVP completo.
2. **Deploy no Fly.io:** `gunicorn` (zona O3), `Dockerfile`, `fly.toml`, volume para o SQLite, `SECRET_KEY` como secret e contas de demonstração. Depois, o link entra no README ("Experimente online").
3. Release `v1.0.0` na `main`, com o link do app nas notas.

Refatoração e arquitetura (camadas ou fatias) ficam para depois do MVP, com o feedback de uso.

## Setup do GitHub (depois do merge na `main`)
- **CodeQL** e **Dependabot security updates:** ligar depois do merge na `main`, porque os dois olham a branch padrão.
- **Dependabot de versões:** `.github/dependabot.yml` (pip e github-actions), com `target-branch: develop` e atualizações agrupadas. É zona O3.
- **Discussions e Projects:** só se a equipe for usar de verdade. Wiki e Packages ficam desligados.
- Já ligados em 11/11: varredura de segredos, push protection, alertas do Dependabot e o ruleset `protege-main-develop` (`main` e `develop` só recebem mudança por PR com o check `gate` verde, sem force push e sem apagar a branch).

## Backlog (issues abertas)
- #5 professor renomeia turma
- #6 professor exclui turma vazia (bloqueada com alunos; liga `PRAGMA foreign_keys` junto)
- #7 busca/filtro na lista de turmas
- #14 id gigante na URL responde 500 em vez de 404 (metas e lançamentos)
- Aceitar aporte acima da meta junto com "desfazer aporte" (hoje o aporte para no que falta, porque não há como desfazer)
- **Quiz do dia** com perguntas de cálculo parametrizadas (números novos por aluno e por dia, resposta calculada pelo código) e **gerador de perguntas com IA** (comando que pede um lote em JSON com schema, valida e grava no banco). O texto das 12 perguntas atuais precisa de revisão.

## Decisões pendentes
- Lista de categorias e valor máximo do lançamento ("A confirmar" em `lancamento_service.py`).
- Valores de XP, teto diário e níveis. Quiz: 10 XP por acerto e teto de 40 por dia (`quiz_service.py`).
- Manter as camadas ou migrar para fatias verticais.
- "Dia ativo" e a janela de 7 dias do painel do professor (`JANELA_FREQUENCIA_DIAS` em `turma_service.py`).

## Em andamento
Arrumação para a `main` (branch `feature/arruma-main`).
