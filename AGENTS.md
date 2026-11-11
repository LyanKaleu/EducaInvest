# EducaInvest: instruções para agentes de código

Protótipo (MVP) de gestão financeira gamificada para jovens de 16 a 24 anos.
Priorize o núcleo demonstrável. Nada de abstração "para o futuro".

## Stack
Python 3.14 · Flask 3.1 · SQLite via `sqlite3` da stdlib (sem ORM) · Jinja renderizado no servidor, sem JavaScript · pytest

## Comandos
No Git Bash. No PowerShell, troque `python` por `.venv\Scripts\python`.

```
bash gate.sh                          portão: lint → arquitetura → testes (o mesmo do CI)
bash gate.sh --sem-testes             só lint + arquitetura (passo 1 do TDD)
python -m pytest -q tests/x.py::nome  teste único (PREFIRA durante a implementação)
python -m pytest -q                   suíte inteira
python run.py                         servidor de desenvolvimento (debug)
python -m pip install -r requirements.txt -r requirements-dev.txt
```

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
- Missões e XP (HU3) estão implementados: `missao_service`/`xp_service`, `missao_repo`/`xp_repo` e `routes/missoes.py`. O crédito de XP roda dentro da transação do lançamento (`registrar_progresso`).
- A tela inicial do aluno (`routes/painel.py`) mostra saldo, XP, nível, sequência de dias (`xp_service.sequencia`, com os dias que têm XP em `xp_eventos`), a missão e a meta em andamento.
- Metas e aportes (HU2) estão implementados: `meta_service`, `meta_repo` e `routes/metas.py`. O aporte não entra no saldo nem rende XP, não passa do que falta (`conferir_limite_do_aporte`, checado depois do reenvio), e "concluída" é calculada (guardado ≥ alvo).
- O painel da turma (HU5) fica na rota `professor.turma`: `turma_service.painel_da_turma` calcula os agregados e a linha por aluno a partir de `XpRepository.resumo_por_aluno` e `MissaoRepository.contar_por_aluno`. "Ativo" = ganhou XP nos últimos `JANELA_FREQUENCIA_DIAS` (7, a confirmar). Nunca mostra reais nem e-mail.
- O quiz (HU4) usa um banco local `PERGUNTAS` em `quiz_service`, no padrão do `MISSOES`, e só grava as respostas em `quiz_repo`, uma por pergunta. O código da pergunta não muda depois de publicado. O XP do acerto (teto diário de 40) entra no mesmo `with conn:` da resposta, em `routes/quiz.py`.

## Convenções que divergem do padrão
- Nomes, docstrings, testes e mensagens ao usuário em português.
- Erro de validação: `ErroValidacao({campo: mensagem})` (app/services/erros.py). A rota renderiza o formulário de novo com status 400 e preserva o que foi digitado.
- Dinheiro em centavos (`int`), nunca `float`. O "hoje" vem de `hoje_no_piaui()` (UTC−3).
- Registro de outro usuário responde 404, não 403: não revela que o id existe.
- Rota nova: Blueprint com `before_request(exigir_perfil(...))`. Rota pública só entra pela lista `ROTAS_PUBLICAS` em tests/integration/test_rotas_protegidas.py.
- Tabela nova: `criar_tabela()` no repositório e chamada em app/db.py.
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
- PR com a saída real do `bash gate.sh`, os testes novos e os invariantes tocados. Afirmação sem evidência não vale.
- Saídas curtas: `pytest -q`. Nunca cole log inteiro; use `tail -n 30`.

## Skills
Carregue a skill quando a tarefa chegar nela e cite no plano quais vai usar. Se uma skill não estiver instalada, siga a regra resumida aqui.
- `dev-dirigido-por-ia`: o método deste projeto (tarefa em 4 campos, ciclo de 8 passos, revisão em contexto novo, PR com evidência, uma tarefa por sessão). Exceção: a skill diz para pular o plano quando o diff cabe numa frase; aqui o plan mode é sempre obrigatório.
- `engenheiro-software-ia`: postura em toda tarefa (recomende um caminho e justifique, questione pedido ambíguo, prefira o simples, diga o que foi verificado e o que não foi).
- `tdd`: todo código novo ou correção (seams, fatias verticais, anti-padrões de teste).
- `ui-taste`: toda tela nova ou alterada. Mantenha o visual atual (app.css, sem framework, sem JavaScript) e, antes de dar como pronta, abra a tela no celular (375px) e no desktop e confira os estados (vazio, erro, sucesso).
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
- Instalar dependência sem perguntar (`requirements*.txt`).
- Alterar CREATE TABLE existente, autenticação/sessão ou `SECRET_KEY` sem aprovação (INVARIANTES, seção operacional).
- "Consertar" o gate relaxando regra: `noqa`, `ignore` no pyproject, contrato removido, teste ajustado para passar. Corrija a causa.
- Publicar arquivo de `docs/` além dos liberados no `.gitignore`. Os outros documentos são privados.

## Decisões pendentes do grupo
- Lista de categorias e valor máximo do lançamento (marcados "A confirmar" em app/services/lancamento_service.py).
- Arquitetura: manter as camadas ou migrar para fatias verticais por funcionalidade.

## Invariantes
Ver INVARIANTES.md. Se a tarefa parece exigir violar um deles, PARE e pergunte.
