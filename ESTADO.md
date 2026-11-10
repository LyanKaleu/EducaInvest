# Estado do projeto

Ponto de retomada entre sessões e computadores. Atualize no PR que muda a fase ou o próximo passo.
Regras de trabalho ficam no AGENTS.md; aqui fica só **onde estamos**.

**Atualizado em:** 10/11/2026 · **Branch de integração:** `develop` (a `main` só tem o commit inicial)
**Mapa visual (artefato privado do Lyan):** https://claude.ai/artifact/XXL3NbF42XXgsiTX4EHXNY

## Pronto (na `develop`)
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
| HU2: metas e aportes (aporte fora do saldo), card da meta na tela inicial | #13 (em revisão) |

## Próximo passo
**Prazo: 13/11/2026** (2ª avaliação: documento + MVP + pitch). A ordem combinada em 10/11 é HU2 metas e aportes (PR #13) → **HU5 painel agregado do professor** → HU4 quiz, se der tempo.
Refatoração e arquitetura (camadas ou fatias) só depois da entrega, com o feedback do MVP.
As refatorações sem mudança de comportamento já levantadas (11 itens, em ordem, com os testes de cada um) estão em https://claude.ai/artifact/CosbUZ15hganrotte19ggc (artefato privado do Lyan).
**Pitch por último:** depois de completar o escopo do MVP, capturar todas as telas no celular, compartilhar com o grupo e só então estruturar a apresentação.

## Antes de levar para a `main` (depois do MVP)
Combinado em 10/11: enquanto o MVP é construído, tudo entra na `develop`. Quando ele estiver completo, o MVP inteiro vai para a `main`, que é a vitrine do repositório. Antes desse PR `develop → main`, numa branch de arrumação:
- Decidir o que faz sentido na `main` e reformular a documentação para quem visita o repositório, não para o processo do grupo. Candidatos: README, os arquivos de processo dos agentes (AGENTS.md, CLAUDE.md, INVARIANTES.md, ESTADO.md, `.claude/`) e os links para artefatos privados.
- Atenção: o repositório é **público**. A `develop` e as outras branches já são visíveis para qualquer um. O que não pode ser público tem que sair de todas as branches e do histórico, ou o repositório vira privado.

## Backlog (issues abertas)
- #5 professor renomeia turma
- #6 professor exclui turma vazia (bloqueada com alunos; liga `PRAGMA foreign_keys` junto)
- #7 busca/filtro na lista de turmas

## Decisões pendentes do grupo
- Lista de categorias e valor máximo do lançamento ("A confirmar" em `lancamento_service.py`).
- Valores de XP, teto diário e níveis (hoje são os exemplos da especificação).
- Manter as camadas ou migrar para fatias verticais.
- Onde hospedar o protótipo.

## Em andamento
HU2 no PR #13 (`feature/metas` → `develop`), aguardando revisão e merge.
Artefato do plano: https://claude.ai/artifact/3cmboRjs6bgsXewE9HTtU7
