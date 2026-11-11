# Invariantes do EducaInvest

Regras que não se negociam. Cada uma tem três partes: o invariante, o caminho seguro e o enforcement executável.
Regra sem enforcement é desejo. Promoção: violou uma vez, reescreva; duas vezes, vira teste; três vezes, vira hook.

## Arquiteturais

### A1 · Direção das camadas
- **Invariante:** `routes → services → repositories`, nunca o contrário. `services` não importa `flask` nem `sqlite3`.
- **Caminho seguro:** a regra de negócio precisa de dados? A rota busca no repositório e passa os valores ao service. O service nunca abre conexão.
- **Enforcement:** import-linter, contratos em `pyproject.toml`, rodando no `bash gate.sh` (Stop hook e CI).

### A2 · Toda rota exige perfil
- **Invariante:** toda rota fora da lista de públicas manda o visitante para o login e aceita só um perfil (ALUNO ou PROFESSOR). As exceções são `inicio` e `logout`.
- **Caminho seguro:** crie a rota num Blueprint com `before_request(exigir_perfil(...))`. Rota pública só entra adicionando o endpoint em `ROTAS_PUBLICAS`, e isso é revisado no PR.
- **Enforcement:** meta-teste `tests/integration/test_rotas_protegidas.py`, que percorre o mapa de rotas e acusa rota nova sem proteção.

## De negócio

### N1 · Aluno só acessa os próprios lançamentos e metas
- **Invariante:** todo SELECT, UPDATE e DELETE de lançamento ou meta filtra por `aluno_id` da sessão, e o aporte só é gravado em meta do próprio aluno.
- **Caminho seguro:** use os métodos do `LancamentoRepository` e do `MetaRepository`, que recebem `aluno_id`. Lançamento ou meta de outro aluno responde 404.
- **Enforcement:** `test_*_de_outro_aluno_*` em `tests/integration/test_lancamentos_rotas.py` (listar, editar, atualizar, confirmar e excluir) e em `tests/integration/test_metas_rotas.py` (listar e aportar).

### N2 · Lançamento, meta e aporte não duplicam
- **Invariante:** o mesmo envio do formulário (clique duplo, reenvio após falha de rede) grava uma vez só.
- **Caminho seguro:** todo formulário de criação leva `chave_idempotencia`, e o repositório usa `ON CONFLICT DO NOTHING`.
- **Enforcement:** `UNIQUE (aluno_id, chave_idempotencia)` em `lancamentos` e `metas` e `UNIQUE (meta_id, chave_idempotencia)` em `aportes_meta`, mais `test_reenvio_com_a_mesma_chave_nao_duplica`, `test_reenvio_da_meta_com_a_mesma_chave_nao_duplica` `test_reenvio_do_aporte_com_a_mesma_chave_nao_duplica` e `test_reenvio_do_aporte_que_concluiu_a_meta_responde_como_sucesso`.

### N3 · E-mail único, sem diferenciar maiúsculas
- **Invariante:** dois usuários nunca têm o mesmo e-mail (`Ana@x` = `ana@x`).
- **Caminho seguro:** o cadastro checa antes, para dar uma mensagem boa. O banco garante, inclusive sob concorrência.
- **Enforcement:** `email ... UNIQUE COLLATE NOCASE` em `usuario_repo.py`, mais `test_cadastro_com_email_ja_usado_retorna_400`.
- **Mesma regra para o nome da turma:** único por professor, sem diferenciar maiúsculas (`Turma 2` = `TURMA 2`). Professores diferentes podem repetir o nome.
  Enforcement: índice `ux_turmas_professor_nome (professor_id, nome COLLATE NOCASE)` em `turma_repo.py`, mais `test_banco_recusa_turma_do_mesmo_professor_com_nome_em_outra_caixa` e `test_turma_com_mesmo_nome_em_outra_caixa_retorna_400`.

### N4 · Consentimento obrigatório no cadastro do aluno (RN-05)
- **Invariante:** aluno só é criado com a autorização marcada, e a data e a hora ficam em `consentimento_em`.
- **Caminho seguro:** valide em `auth_service`. Nunca crie aluno por outro caminho.
- **Enforcement:** `test_cadastro_sem_consentimento_e_recusado` (unit) e `test_cadastro_sem_consentimento_retorna_400` (integração).

### N5 · Professor vê a turma sem dados pessoais do aluno
- **Invariante:** as telas do professor mostram o apelido, os agregados da turma e, por aluno, só nível, XP, missões concluídas e se está ativo. Nunca o e-mail nem valores em reais (RN-18). Só a turma do próprio professor; a de outro responde 404.
- **Caminho seguro:** o repositório da turma devolve só as colunas que a tela usa, e o painel lê XP e missões, nunca `lancamentos` nem `metas`.
- **Enforcement:** `test_lista_da_turma_nao_mostra_email_do_aluno`, `test_turma_de_outro_professor_retorna_404`, `test_painel_nao_mostra_valores_em_reais` e `test_tabela_mostra_cada_aluno_sem_email`.

### N6 · XP nunca diminui nem duplica (RN-10 a RN-12)
- **Invariante:** o XP só entra por INSERT no livro-razão `xp_eventos`, cada origem (lançamento, missão, quiz) pontua uma vez por aluno e o crédito vai junto com a ação que o gerou.
- **Caminho seguro:** use `XpRepository.creditar` dentro do mesmo `with conn:` da ação (veja `registrar_progresso` em `app/routes/missoes.py`). Total e nível são calculados, nunca guardados em coluna.
- **Enforcement:** gatilhos `tr_xp_eventos_sem_update`/`tr_xp_eventos_sem_delete` e `UNIQUE (aluno_id, origem, origem_id)` em `xp_repo.py`, mais `test_banco_recusa_apagar_xp`, `test_mesma_origem_pontua_uma_vez_so`, `test_missao_concluida_nao_paga_de_novo` e `test_falha_ao_creditar_xp_nao_salva_o_lancamento`.

## Operacionais: sempre com aprovação humana explícita
Valem independentemente de o CI estar verde.

- **O1 · Schema:** alterar um CREATE TABLE existente ou apagar uma tabela. Tabela nova é permitida, seguindo o padrão `criar_tabela()`.
- **O2 · Acesso e sessão:** `app/routes/acesso.py`, `app/routes/auth.py`, `app/services/auth_service.py`, `app/__init__.py` (`SECRET_KEY`, cookie).
- **O3 · Dependências e portão:** `requirements*.txt`, `pyproject.toml`, `gate.sh`, `.github/workflows/`, `.claude/`.
- **Enforcement:** o hook PreToolUse (`.claude/hooks/protege.py`) pede confirmação antes de editar os arquivos de O2 e O3, e bloqueia `.env*`, `instance/` e `*.db`. O1 é checado pelo subagente `revisor` e na revisão do PR.
