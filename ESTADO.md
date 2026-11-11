# Estado do projeto

Ponto de retomada entre sessões e computadores. Atualize no PR que muda a fase ou o próximo passo.
Regras de trabalho ficam no AGENTS.md; aqui fica só **onde estamos**.

**Atualizado em:** 11/11/2026 · **Branch de integração:** `develop` (a `main` só tem o commit inicial)
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
| HU2: metas e aportes (aporte fora do saldo e limitado ao que falta), card da meta na tela inicial | #13 |
| HU5: painel da turma (XP médio, missões, ativos em 7 dias e linha por aluno, sem reais nem e-mail) | #16 |

## Próximo passo
**Prazo: 13/11/2026** (2ª avaliação: documento + MVP + pitch). A ordem combinada em 10/11 é HU2 metas e aportes (PR #13, pronta) → HU5 painel do professor (PR #16) → **HU4 quiz, se der tempo**.
Combinado em 11/11: antes das capturas para o pitch, um passe visual (`ui-taste`, só `app.css`, sem JavaScript) e a limpeza das reservas vazias `db/` e `app/config.py`.
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
- #14 id gigante na URL responde 500 em vez de 404 (metas e lançamentos)
- Depois do MVP: aceitar aporte acima da meta junto com "desfazer aporte" (hoje o aporte para no que falta, porque não há como desfazer)

## Decisões pendentes do grupo
- Lista de categorias e valor máximo do lançamento ("A confirmar" em `lancamento_service.py`).
- Valores de XP, teto diário e níveis (hoje são os exemplos da especificação).
- Manter as camadas ou migrar para fatias verticais.
- Onde hospedar o protótipo.
- "Dia ativo" e a janela de 7 dias do painel do professor (`JANELA_FREQUENCIA_DIAS` em `turma_service.py`).

## Em andamento
HU5 no PR #16, aguardando merge. Decisões de 11/11: o painel mostra os agregados e uma linha por aluno (ordem de apelido), e "ativo" é quem ganhou XP nos últimos 7 dias (a confirmar pelo grupo).
Artefato da HU5 (decisões, testes e verificação): https://claude.ai/artifact/D4zhtUyWtAwTPpW6Fnsac2
Artefato da HU2 (plano, decisões e revisão sênior): https://claude.ai/artifact/3cmboRjs6bgsXewE9HTtU7
