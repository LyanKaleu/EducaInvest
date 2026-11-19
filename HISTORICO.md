# Histórico do projeto

O que já foi entregue e as decisões já tomadas. Fica fora do contexto carregado em toda sessão: o ponto de retomada é o [ESTADO.md](ESTADO.md).
Ao fechar um PR, acrescente a linha dele na tabela.

## Entregue
A especificação v2 está em [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md).

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
| `PRAGMA foreign_keys` ligado na conexão e enumeração de e-mail no cadastro registrada como risco aceito | #28 |
| Senha em argon2id (pwdlib), com migração do hash antigo no login | #30 |
| Dependências com uv: `uv.lock` fixa a árvore inteira, `.python-version` em 3.14, CI com `uv sync --locked` e Dependabot `uv` | #31 |
| Redesign igual ao protótipo navegável: menu no rodapé, cartões, chips sem JavaScript, sequência de 7 dias, resumo e atalhos nas metas, ranking e inativos no painel da turma | #26 |
| Animações só em CSS (troca de página, avisos, comemoração, toque, barras) e CSS dividido em um arquivo por assunto | #29 |
| PEP 8 a 79 colunas com `ruff format`, lint amplo, docstrings em `app/` e anotação de tipo em todo o código | #32 |
| `main` atualizada com os PRs #26 a #32 | #34 e o seguinte |
| Tema escuro automático pelo tema do sistema (sem botão e sem JavaScript), cores só nos tokens e contraste AA testado nos dois temas | #38 |
| Movimento do transitions.dev com JS puro como melhoria progressiva: toast de sucesso com check que some sozinho, campo com erro tremendo, pílula no Gasto/Entrada, XP rolando num tambor e barra do nível enchendo, troca de página com direção e quiz em cascata | #40 |
| Camada de hover e toque do taste-skill (sublinhado com reserva, hover firme na borda, hover do link só com mouse) | #41 |

## Decisões registradas
- **Hospedagem:** Fly e Render foram descartados: a Fly exige cartão e o Render grátis apaga o SQLite quando o app dorme. Container (`gunicorn`, `Dockerfile`) só volta se o banco sair do SQLite local.
- **Setup do GitHub:** ligados em 11/11 a varredura de segredos, o push protection, os alertas do Dependabot e o ruleset `protege-main-develop` (`main` e `develop` só recebem mudança por PR com o check `gate` verde, sem force push e sem apagar a branch). O `.github/dependabot.yml` (zona O3) cobre uv e github-actions, toda segunda, com PR para a `develop`, minor e patch agrupados e major em PR separado. Discussions e Projects só se a equipe for usar de verdade; Wiki e Packages ficam desligados.
- **Paperclip (orquestrador de agentes, open source)**, avaliado em 17/11/2026 e adiado. Ele comanda Claude Code, Codex e Gemini CLI por heartbeat, com organograma, orçamento e aprovações. O Antigravity não entra, porque é uma IDE, não um CLI.
  - Por que não agora: os adaptadores rodam em modo automático (sem plan mode aprovado nem TDD com o teste vermelho), o hook `protege.py` e o Stop hook só valem para o Claude, o adaptador do Gemini não isola a árvore de trabalho, a documentação não cita Windows e cada heartbeat gasta a cota das assinaturas. Também não há tarefa paralela em volume: o próximo passo é sequencial.
  - Quando reavaliar: tarefa recorrente e autônoma com revisão no PR (ex.: o gerador de perguntas do quiz), sempre com o check `gate` como rede comum.
  - Enquanto isso: Claude Code implementa, Codex dá a segunda opinião na revisão do PR e Antigravity/Gemini ficam com protótipo de tela e teste no navegador, cada um na sua branch ou worktree, todos lendo o `AGENTS.md`.
- **OpenSpec (framework de spec-driven development, CLI em Node)**, avaliado em 18/11/2026 e adiado. O ciclo é `propose` (proposta, design, delta de spec e tarefas), `apply`, `archive` (junta os deltas numa spec viva por funcionalidade) e `explore` para projeto existente.
  - Por que não agora: o projeto já faz SDD (plan mode com a tarefa em 4 campos e seams, `ESPECIFICACAO.md`, `INVARIANTES.md`, PR com evidência). O `apply` roda todas as tarefas de uma vez, sem o teste vermelho por fatia nem o `revisor`. O `openspec init` escreve em `.claude/` (O3) e traz Node, e a pasta `openspec/` na raiz ficaria pública, enquanto a `docs/` é privada.
  - O que ele teria de bom: spec separada por funcionalidade e atualizada a cada mudança, em vez de um documento único que alguém precisa lembrar de atualizar.
  - Quando reavaliar: quando a `ESPECIFICACAO.md` ficar desatualizada ou pesada demais. O teste seria uma mudança só, numa branch, usando só o `propose` e implementando com o TDD de sempre.
