# EducaInvest: instruções para agentes de código

Protótipo (MVP) da disciplina de Empreendedorismo: gestão financeira gamificada para jovens de 16 a 24 anos.
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
docs/              especificação do MVP (PDF) e schema de referência em PostgreSQL
```
- `db/schema.sql` e `app/config.py` são reservas vazias. Não use como referência.
- Missões e XP (HU3) estão implementados: `missao_service`/`xp_service`, `missao_repo`/`xp_repo` e `routes/missoes.py`. O crédito de XP roda dentro da transação do lançamento (`registrar_progresso`).
- Metas, quiz e painel (HU2, HU4 e HU5) só têm a docstring. Ainda não estão implementados.

## Convenções que divergem do padrão
- Nomes, docstrings, testes e mensagens ao usuário em português.
- Erro de validação: `ErroValidacao({campo: mensagem})` (app/services/erros.py). A rota renderiza o formulário de novo com status 400 e preserva o que foi digitado.
- Dinheiro em centavos (`int`), nunca `float`. O "hoje" vem de `hoje_no_piaui()` (UTC−3).
- Registro de outro usuário responde 404, não 403: não revela que o id existe.
- Rota nova: Blueprint com `before_request(exigir_perfil(...))`. Rota pública só entra pela lista `ROTAS_PUBLICAS` em tests/integration/test_rotas_protegidas.py.
- Tabela nova: `criar_tabela()` no repositório e chamada em app/db.py.
- Antes de criar um arquivo, abra o irmão equivalente (ex.: os `lancamento_*`) e siga o padrão dele.

## Fluxo de trabalho
- Tarefa em 4 campos: Goal, Context, Constraints e Done when, verificável por máquina.
- TDD em 3 passos:
  1. Só os testes: rode e mostre a falha.
  2. Implementação mínima.
  3. Sugira refatorações.
- Teste de correção precisa FALHAR se a correção for revertida.
- Se o diff não cabe numa frase, comece pelo plan mode. Pergunte antes de implementar feature vaga.
- Antes do PR: revisão pelo subagente `revisor`, em contexto novo. Na triagem, recuse estilo e especulação.
- PR com a saída real do `bash gate.sh`, os testes novos e os invariantes tocados. Afirmação sem evidência não vale.
- Saídas curtas: `pytest -q`. Nunca cole log inteiro; use `tail -n 30`.

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
- Publicar arquivo de `docs/` além dos liberados no `.gitignore`. Os trabalhos da disciplina são privados.

## Decisões pendentes do grupo
- Lista de categorias e valor máximo do lançamento (marcados "A confirmar" em app/services/lancamento_service.py).
- Arquitetura: manter as camadas ou migrar para fatias verticais por funcionalidade.

## Invariantes
Ver INVARIANTES.md. Se a tarefa parece exigir violar um deles, PARE e pergunte.
