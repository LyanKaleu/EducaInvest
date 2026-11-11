# EducaInvest · Especificação do MVP

**Versão 2 · 11/11/2026.** Descreve o que o MVP faz hoje. A versão 1 (03/11/2026) era o rascunho de antes da implementação. Esta versão registra o que foi construído e as dúvidas que já foram decididas.

## 1. Visão

O EducaInvest é um app web para jovens que estão começando a lidar com dinheiro. O aluno registra entradas, gastos e metas, e o app transforma esses registros em missões, XP, níveis e sequência de dias. O professor cria a turma e acompanha o engajamento sem ver valores individuais.

| Tema | Decisão |
|---|---|
| Público | Jovens de 16 a 24 anos, com a escola como canal principal |
| Ação central | Registrar entradas, gastos e metas e cumprir missões baseadas nos próprios registros |
| Perfis | Aluno e professor. Gestor e secretaria ficam fora do MVP |
| Dispositivo | Web leve, mobile-first, pensado para conexão instável |
| Stack | Python 3.14, Flask 3.1, SQLite (`sqlite3` da biblioteca padrão), Jinja no servidor, sem JavaScript, pytest |
| Assistente de IA | Fora do MVP |

## 2. Requisitos funcionais

| ID | Requisito | Como o MVP atende |
|---|---|---|
| RF01 | Cadastro e login de aluno e professor; o aluno entra na turma por um código | Login por e-mail e senha. O aluno só conclui o cadastro com um código de turma válido e com a autorização marcada. O professor se cadastra sem código |
| RF02 | O professor cria turmas com código de acesso | Código de 6 caracteres sem os que se confundem (0/O, 1/I/L). O nome da turma é único por professor, sem diferenciar maiúsculas |
| RF03 | O aluno registra entradas e gastos | Tipo, valor, categoria da lista fixa do mesmo tipo, data não futura e descrição opcional. O saldo é calculado na hora. Tem busca, edição e exclusão |
| RF04 | O aluno cria metas e acompanha o progresso | Nome, valor-alvo e prazo opcional. Aportes mostram o valor guardado e o percentual. A meta aparece como concluída quando o guardado chega ao alvo |
| RF05 | Missões geradas a partir dos registros | Trilha de missões com critério verificado pelo app. Cada missão é concluída uma vez só e libera a próxima |
| RF06 | Quiz curto com explicação | 12 perguntas sobre juros, crédito, orçamento e inflação. Cada resposta mostra a explicação, e o acerto dá XP |
| RF07 | XP, níveis, conquistas e sequência de dias | XP num livro-razão que só recebe inserções, teto diário, nível calculado, conquista a cada missão concluída e sequência de dias com XP |
| RF08 | O professor acompanha a turma | XP médio, missões concluídas, alunos ativos em 7 dias e uma linha por aluno. Sem e-mail e sem valores em reais |

## 3. Requisitos não funcionais

| ID | Requisito | Como o MVP atende |
|---|---|---|
| RNF01 | Leve e tolerante a conexão instável | Páginas renderizadas no servidor, sem JavaScript. Todo formulário de criação leva uma chave de idempotência, então reenviar depois de uma falha de rede não duplica nada. Com erro, o formulário volta preenchido |
| RNF02 | Privacidade (LGPD) | Coleta mínima (apelido, e-mail, senha, turma), sem CPF nem dados bancários. A autorização do aluno é obrigatória e fica gravada com data e hora. O professor nunca vê valores em reais nem e-mail |
| RNF03 | Usabilidade | Registrar um gasto: *Início → Registrar gasto* (tipo e data já preenchidos) → valor, categoria e *Salvar*. Áreas de toque de 44px, contraste AA e mensagens junto ao campo |
| RNF04 | Segurança | Senha com hash `scrypt`. Toda rota exige login e um perfil, e um meta-teste acusa rota nova sem proteção. Registro de outro usuário responde 404. Cookie de sessão `SameSite=Lax`. O HTTPS vem da hospedagem |

## 4. Regras de negócio

Os valores marcados com *a confirmar* estão no código como constantes e podem mudar sem migração.

**Usuários e acesso**
- RN-03: o aluno entra pelo código de turma gerado pelo professor e pertence a uma turma só.
- RN-04: o e-mail é único, sem diferenciar maiúsculas (`Ana@x` = `ana@x`).
- RN-05: o aluno só é criado com a autorização marcada ("tenho 18 anos ou mais, ou autorização do responsável ou da escola"). O texto ainda precisa de validação jurídica antes do uso com alunos reais.

**Registro financeiro**
- RN-07: valor maior que zero e até R$ 100.000,00 (*a confirmar*), data não futura no fuso do Piauí (UTC−3) e categoria do mesmo tipo:
  - entrada: Mesada, Trabalho/bico, Benefício, Outras entradas;
  - saída: Alimentação, Transporte, Lazer, Compras, Estudos, Outras saídas (*a confirmar*).
- RN-08: saldo = entradas − saídas, sempre calculado. Dinheiro é guardado em centavos inteiros.
- Aporte em meta é um valor separado: não desconta do saldo e não rende XP. O aporte não passa do que falta para concluir a meta, porque ainda não existe "desfazer aporte".

**Missões e gamificação**
- RN-09/10: trilha fixa. *Primeiros passos* (registre 3 gastos, +30 XP) libera *Hábito em construção* (registre 7 lançamentos, +50 XP). Uma missão concluída continua concluída mesmo se o aluno excluir registros.
- RN-11: cada lançamento novo rende 10 XP, com teto de 50 XP por dia. Depois do teto, o lançamento é salvo e o aluno vê um aviso. Editar não rende XP.
- RN-12: o XP nunca diminui. Níveis: Iniciante (0), Aprendiz (100), Organizado (300) (*a confirmar*).
- RN-13: a sequência conta dias seguidos com XP, no fuso do Piauí. O dia de hoje ainda não acabou, então só um dia inteiro em branco zera a sequência.
- RN-14: no quiz, cada pergunta aceita uma resposta só. Vale a primeira: acerto dá 10 XP, com teto de 40 XP por dia no quiz (*a confirmar*), e erro mostra a resposta certa e a explicação.
- O lançamento, a missão ou a resposta e o XP que geram são gravados na mesma transação: ou tudo, ou nada.

**Professor**
- RN-15/18: o painel mostra só agregados e, por aluno, apelido, nível, XP, missões concluídas e se está ativo. "Ativo" é quem ganhou XP nos últimos 7 dias (*a confirmar*). A turma de outro professor responde 404.

**Medição**
- RN-16/17: o questionário de confiança financeira (antes e depois) e a pesquisa sobre o hábito de poupar são aplicados por formulário externo. Metas: 50% de confiantes e 20% poupando.

## 5. Histórias de usuário e critérios de aceite

Os cenários são cobertos pelos testes de `tests/unit/` e `tests/integration/`.

### HU1 · Registrar um gasto em poucos toques (RF03)
| Cenário | Dado | Quando | Então |
|---|---|---|---|
| Gasto válido | aluno logado | registra saída de R$ 25,00 em Alimentação, hoje | o lançamento aparece na lista e o saldo diminui R$ 25,00 |
| Entrada válida | aluno logado | registra entrada de R$ 50,00 | o saldo aumenta R$ 50,00 |
| Valor inválido | aluno no formulário | deixa o valor vazio, zero ou negativo | nada é salvo, a mensagem aparece junto ao campo e o resto continua preenchido |
| Data futura | aluno no formulário | escolhe uma data depois de hoje | nada é salvo e o app avisa que a data não pode ser futura |
| Sem categoria | aluno no formulário | salva sem categoria | nada é salvo e o app pede a categoria |
| Reenvio | conexão caiu durante o envio | o aluno envia de novo | o lançamento é gravado uma vez só |

### HU2 · Criar meta e ver o progresso (RF04)
| Cenário | Dado | Quando | Então |
|---|---|---|---|
| Criar meta | aluno logado | cria "Fone" com alvo de R$ 200,00 | a meta aparece com 0% |
| Aporte | meta de R$ 200,00 com R$ 50,00 | aporta R$ 50,00 | mostra R$ 100,00 de R$ 200,00 · 50% |
| Meta concluída | meta com R$ 190,00 | aporta R$ 10,00 | chega a 100% e aparece como concluída |
| Dados inválidos | aluno criando meta | deixa o nome vazio ou o alvo ≤ 0 | a meta não é criada e as mensagens indicam os campos |
| Prazo no passado | aluno criando meta | informa prazo anterior a hoje | a meta não é criada e o app explica |
| Aporte inválido | meta existente | aporta zero, negativo ou mais do que falta | o aporte não é gravado e o progresso não muda |

### HU3 · Missões com XP (RF05, RF07)
| Cenário | Dado | Quando | Então |
|---|---|---|---|
| Progresso parcial | 2 gastos registrados | abre Missões | aparece "2 de 3" |
| Concluir missão | 2 gastos registrados | registra o 3º | +30 XP, a conquista aparece e a próxima missão é liberada |
| Teto diário | aluno com 50 XP de registros hoje | registra outro gasto | o lançamento é salvo sem XP e o aluno vê o aviso |
| Missão repetida | missão concluída | cumpre o critério de novo | o XP não é creditado outra vez |
| Falha parcial | o crédito de XP falha | o app processa o lançamento | nem o lançamento nem o XP são gravados |
| Nível | XP chega a 100 | o XP é creditado | o aluno sobe para Aprendiz e vê o aviso |

### HU4 · Quiz com explicação (RF06)
| Cenário | Dado | Quando | Então |
|---|---|---|---|
| Resposta certa | pergunta aberta | escolhe a certa | mostra a explicação e credita XP |
| Resposta errada | pergunta aberta | escolhe a errada | mostra a explicação e a resposta certa, sem XP |
| Sem seleção | pergunta aberta | envia sem marcar | nada é gravado e o app pede uma alternativa |
| Pergunta repetida | pergunta já respondida | responde de novo | a resposta não muda e não há XP |
| Teto diário | aluno com 40 XP do quiz hoje | acerta outra | a resposta vale, sem XP |

### HU5 · Turma e painel do professor (RF02, RF08)
| Cenário | Dado | Quando | Então |
|---|---|---|---|
| Criar turma | professor logado | cria "2º A" | o app gera e mostra um código único |
| Aluno entra | turma com código válido | o aluno se cadastra com o código | o aluno aparece na turma |
| Painel | turma com alunos | o professor abre a turma | vê XP médio, missões e ativos, sem reais nem e-mail |
| Turma vazia | turma sem alunos | o professor abre a turma | aparece "Nenhum aluno ainda." |
| Código inexistente | aluno no cadastro | informa um código que não existe | o cadastro não é concluído |
| Turma sem nome | professor criando turma | deixa o nome vazio | a turma não é criada |
| Acesso indevido | aluno logado | tenta abrir a página do professor | o acesso é negado |

## 6. Decisões tomadas desde a versão 1

| Dúvida da v1 | Decisão |
|---|---|
| O aporte desconta do saldo? | Não. É um valor separado, sem XP |
| Quem cria a conta do professor? | Autocadastro |
| Aluno entra com e-mail e senha ou só apelido e código? | E-mail e senha, com o código da turma no cadastro |
| Quem erra o quiz pode tentar de novo? | Não. Vale a primeira resposta |
| Como funcionam as missões? | Trilha fixa com pré-requisito, contando os lançamentos do aluno |
| O que é "dia ativo"? | Um dia em que o aluno ganhou XP (a mesma regra da sequência) |
| Qual stack? | Flask com SQLite e páginas renderizadas no servidor, sem JavaScript |

Continuam em aberto: os valores de XP, teto e níveis, a lista de categorias, o valor máximo do lançamento e a janela de 7 dias do painel.

## 7. Fora do MVP

Assistente de IA · professor atribuir missões · integração bancária · ranking entre alunos · cartão, dívidas e investimentos · modo offline completo e app nativo · notificações · painel de gestores · pagamentos · questionários automatizados no app.

## 8. Modelo de dados

SQLite. O `CREATE TABLE` em `criar_tabela()` de cada repositório (`app/repositories/`) é a fonte da verdade. O esboço em PostgreSQL de antes da implementação está em [`educainvest_schema.sql`](educainvest_schema.sql).

| Tabela | Função | Garantias no banco |
|---|---|---|
| `usuarios` | alunos e professores, com hash da senha e data da autorização | e-mail `UNIQUE COLLATE NOCASE` |
| `turmas` · `matriculas` | turma do professor e vínculo do aluno | código único; nome único por professor sem diferenciar maiúsculas; cada aluno numa turma só (PK `aluno_id`) |
| `lancamentos` | entradas e gastos em centavos | `UNIQUE (aluno_id, chave_idempotencia)` |
| `metas` · `aportes_meta` | metas e aportes | chave de idempotência única por aluno e por meta |
| `xp_eventos` | livro-razão de XP | `UNIQUE (aluno_id, origem, origem_id)`; gatilhos recusam `UPDATE` e `DELETE` |
| `missoes_concluidas` | missões concluídas por aluno | PK `(aluno_id, missao_codigo)` |
| `quiz_respostas` | uma resposta por pergunta | PK `(aluno_id, pergunta_codigo)` |

As missões e as perguntas do quiz ficam no código (`MISSOES` e `PERGUNTAS`), e só o progresso vai para o banco. Total de XP, nível, saldo e progresso das metas são calculados, nunca guardados.
