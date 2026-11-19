---
name: "dev-dirigido-por-ia"
description: "Método e arquitetura para programar com agentes de IA (Claude Code, Codex): AGENTS.md, invariantes, gate, ciclo de 8 passos, contexto, fatias verticais e bugs plausíveis."
---

# Desenvolvimento e arquitetura dirigidos por IA

Adaptação condensada de dois livros de Rogério Silva e Claude Opus 5 (IFPI, 2026): *Desenvolvimento Dirigido por IA* (o método: arquivos de fundação e ciclo por tarefa) e *Arquitetura em Tempos de IA* (como organizar o código para humanos e agentes). Originais sob CC BY-SA 4.0; esta adaptação segue a mesma licença.

Use esta skill ao configurar um repositório para agentes, ao executar ou planejar uma tarefa de código, ao revisar um diff ou PR, ao decidir estrutura de pastas e fronteiras, e ao gerenciar o contexto de uma sessão.

Prioridade: as regras do próprio repositório (AGENTS.md, CLAUDE.md, INVARIANTES.md, regras de commit) vencem esta skill. Não reestruture um projeto existente para seguir a arquitetura daqui sem pedido explícito; aplique os princípios dentro da estrutura que já existe.

## Tese em uma frase

O humano paga por conceito (memória de trabalho); o agente paga por token e por salto entre arquivos (atenção). Código organizado pelo que muda junto, com fronteiras verificadas por máquina, serve aos dois. Delegamos o "como"; o "quê", o "porquê" e o veredito continuam humanos.

## Parte 1 — A fundação: cinco arquivos

Monte uma vez e só ajuste. Precisar de um sexto arquivo costuma ser sinal de burocracia.

| Arquivo | Papel | Regra |
| --- | --- | --- |
| `AGENTS.md` | Como trabalhar no repo | Menos de 150 linhas; portátil entre ferramentas |
| `CLAUDE.md` | Ponte para o Claude Code | Duas linhas de import (`@AGENTS.md`, `@INVARIANTES.md`) + instrução de compactação |
| `INVARIANTES.md` | Regras inegociáveis | 5 a 7 entradas, cada uma com enforcement |
| `docs/UI.md` | Consistência visual | Tokens semânticos, inventário de componentes com precedência, loop visual |
| `gate.sh` | Portão determinístico | Lint, tipos, arquitetura, testes, segredos; do mais barato ao mais caro |

### O que entra no AGENTS.md

- Entra: comandos que o agente não adivinha, como rodar testes, estilo que diverge do padrão, etiqueta de branch/PR/commit, decisões arquiteturais, variáveis de ambiente, armadilhas não óbvias, um mapa curto de onde mora cada feature.
- Fica de fora: o que se descobre lendo o código, convenções padrão da linguagem, documentação de API (linke), coisas que mudam toda semana, tutoriais, descrição arquivo por arquivo, obviedades ("escreva código limpo").
- Se o arquivo precisa listar quais arquivos tocar para cada mudança, o problema é a arquitetura fragmentada, não o arquivo. O mapa de features idealmente é gerado por script, não escrito à mão.

### Invariantes

Invariante que não é executável é decoração. Cada entrada tem sempre três campos:

```
### A1 — Direção de dependência
Invariante: o que nunca pode acontecer.
Caminho seguro: o que fazer em vez disso (não só a proibição).
Enforcement: o teste, regra de lint ou hook que barra a violação.
```

- Comece pelo consequente e não óbvio: o que revisores explicam repetidamente.
- Se remover a regra não mudaria nenhuma revisão, ela não entra.
- Sem o terceiro campo, a regra não está pronta.
- Duas famílias: arquiteturais (direção de dependência, camadas) e de negócio (tenant, imutabilidade, valores). Operacionais (migração, credenciais, pagamento) já nascem com bloqueio por hook ou aprovação.
- Três camadas de força: texto no arquivo (advisório) → teste/lint no gate → hook/CI (impossível violar). Regra violada 3 vezes sobe de camada.

### Gate e hooks

- Um script só, chamado pelo agente, pelo hook e pelo CI. Falha cedo nos passos baratos.
- Hook útil: rodar o gate quando arquivos mudaram; bloquear escrita em caminhos protegidos (migrações, `.env`, segredos).
- Saídas de ferramenta curtas (testes em modo silencioso, logs truncados) configuradas no repo, não pedidas a cada vez.

## Parte 2 — O ciclo: oito passos por tarefa

1. **Escrever a tarefa** com quatro campos: *Goal* (o que muda para quem usa), *Context* (@arquivos, erro real, padrão a seguir), *Constraints* (invariantes, o que NÃO mudar, fora de escopo), *Done when* (condições que uma máquina avalia). "Fora de escopo" evita metade dos problemas. Se não sabe o que quer, explore antes de escrever a tarefa.
2. **Planejar ou não.** Se o diff cabe numa frase, pule o plano. Planeje quando a abordagem é incerta, toca vários arquivos, mexe em código desconhecido ou em invariante. Na dúvida, planeje. Bug: plano para diagnosticar (hipótese com evidência), implementação direta para corrigir.
3. **Plan mode:** explorar → planejar → editar o plano você mesmo → sair. O plano é seu, não do agente.
4. **Implementar** com pedido verificável: cite arquivos, o padrão existente a imitar, os invariantes afetados e o comando de verificação. Pare cedo (Esc) quando ele sair do rumo.
5. **Revisão adversarial em contexto novo** (subagente ou sessão separada), contra o plano e os invariantes: "Done when" cumprido, casos de borda testados, nada fora de escopo mudou, invariantes intactos. Peça só lacunas de corretude e requisitos; nada de estilo. Padronize em um `docs/code_review.md`.
6. **Triar os achados.** Três perguntas: pode quebrar em produção? Está no Done when ou nos invariantes? O lint já aceita? Aceite corretude, invariante, requisito e escopo; pergunte sobre casos que talvez nem existam no domínio; recuse especulação ("extraia uma Factory"), estilo e try/catch defensivo. Metade dos achados é ruído por obediência.
7. **PR com evidência:** saída real do gate, nomes dos testes novos, uma linha por invariante afetado dizendo como foi preservado, e o que ficou fora de escopo. Afirmação de sucesso não é evidência; saída de comando é.
8. **Fechar a tarefa:** `/clear`. O contexto é descartável porque a fundação é permanente. Se for voltar, `/rename` antes.

### Decisões rápidas

| Situação | Ação |
| --- | --- |
| Errou 2x a mesma coisa | `/clear` + prompt melhor (não corrija em loop) |
| Próxima tarefa é outro assunto | `/clear` |
| Precisou de `/compact` | A tarefa eram duas |
| Regra violada 3x | Vira hook ou teste |
| Achado é preferência de estilo | Recuse |
| Não consegue verificar | Não faz merge |

## Parte 3 — Contexto como recurso físico

- Contexto tem capacidade, custo e degradação sob carga (context rot): quanto mais cheio e mais antigo, mais o agente esquece regras e erra. Janela longa serve para ler e destilar; sessão curta para alterar.
- Custo cresce com o histórico, não com a tarefa: o mesmo trabalho em sessões separadas sai mais barato e erra menos.
- Ordem de impacto: uma tarefa por sessão; compactar em marcos verificados (plano aprovado, testes verdes), nunca no desespero; exploração ampla delegada a subagentes que devolvem só a conclusão; saídas curtas; regras em arquivos, não no chat.
- Modelo: o padrão no dia a dia, o mais forte na exceção (diagnóstico difícil, desenho); reduza o esforço de raciocínio em tarefa trivial.
- Antipadrões de sessão: sessão pega-tudo, corrigir repetidamente na mesma thread, arquivo de contexto superespecificado, confiar sem verificar, exploração infinita, automatizar cedo demais, regra sem enforcement, aceitar todos os achados.

## Parte 4 — Arquitetura para duas inteligências

**Separe princípio de ritual.** SOLID, Clean Architecture e DDD estratégico continuam valendo. Uma classe por arquivo, interface-espelho de implementação única, mapper de identidade e pasta por camada técnica são rituais que multiplicam saltos.

**Meça a profundidade de descoberta:** quantas leituras em série o agente faz até entender uma feature. Leituras encadeadas tornam o custo quase quadrático; é a métrica que a arquitetura controla.

### Padrões que se reforçam

1. **Fatia vertical:** uma pasta por feature/contexto com domínio, casos de uso e adaptadores. Organize pelo que muda junto.
2. **Módulo profundo:** interface estreita, implementação rica.
3. **Porta definida pelo consumidor:** a interface de saída mora no arquivo do caso de uso, só com os métodos que ele usa. Fatias não se importam entre si; a composição as conecta.
4. **Snapshot único:** um tipo de dados por agregado, servindo persistência e resposta, em vez de DTO → entidade → row → mapper → DTO.
5. **Raiz de composição manual:** um arquivo que instancia e conecta tudo com construtores, sem container mágico.
6. **Fronteira executável:** regra de dependência no lint (import-linter, dependency-cruiser, ArchUnit) dentro do gate. Fronteira é lint, não pasta.

Convenção: todo arquivo começa com um comentário de uma linha dizendo o que contém.

Forma típica de uma fatia: `<agregado>` (entidade, invariantes, snapshot; só importa `shared/`), `<verbo>-<agregado>` (um caso de uso + portas + input), `*.adapters` (ORM, HTTP), `*.contrato` / `*.fake` (teste), `composicao` (conecta tudo). `shared/` é folha: não importa nenhuma fatia.

Divida quando dois atores pedem mudanças no mesmo arquivo, quando o agente lê o arquivo inteiro e usa uma fração pequena em tarefas diferentes, ou quando ele não cabe com folga numa leitura (meça em tokens). Divida criando outro caso de uso ou outra fatia, não outra camada.

Antipadrões: camadas fractais (controllers/dtos/mappers dentro da fatia), fatia-deus (um contexto que engoliu vários), `shared/` virando `utils/`, fatias importando fatias. Migre de camadas para fatias estrangulando uma fatia por vez, nunca em big bang.

Paralelismo entre agentes exige conjuntos de escrita disjuntos: cada agente numa fatia; junções globais (rotas, schema, composição) poucas e serializadas.

## Parte 5 — Qualidade: o bug plausível

O bug plausível compila, passa no lint, passa nos testes (escritos pela mesma sessão, com o mesmo engano) e lê bem na revisão. Defesas específicas:

- **ORM:** N+1 em laço (use orçamento de queries nos testes); consultar-depois-inserir (corrida; use restrição única no banco e trate o conflito); atualização em massa que pula validações e hooks do agregado.
- **Auth:** decodificar token não é verificar (use `verify`, nunca `decode`); autenticado não é autorizado (cheque dono/tenant); rota sem política. Defesa: toda rota declara política e um meta-teste falha o build se alguma não declarar.
- **Invariante em camadas:** agregado dá a mensagem de erro, banco dá a garantia (constraint), teste de propriedade dá a confiança.
- **Testes que mordem:** o humano define propriedades, ataques e limites; o agente escreve. Toda correção tem prova de revert: o teste falha sem a correção e passa com ela (verifique mecanicamente, por exemplo com `git stash` do arquivo corrigido). Expected values vêm de fonte independente, nunca recalculados como no código.
- **Débito técnico com catraca:** uma métrica guardada no repo (fragmentação, avisos, cobertura) que o gate compara a cada PR. Pode melhorar, não pode piorar.

## As dez regras

1. Separe princípio de ritual.
2. Meça a profundidade de descoberta.
3. Trate o contexto como recurso físico.
4. Uma tarefa, uma sessão.
5. Mapa, não receita de travessia.
6. Organize pelo que muda junto.
7. Fronteira é lint, não pasta.
8. Invariante em camadas: agregado, banco, teste de propriedade.
9. Segurança como erro de build.
10. Teste que não morde não conta.

Cinco frases para lembrar: gerenciar contexto é controle de qualidade, não economia; invariante que não é executável é decoração; se o diff cabe numa frase, pule o plano; metade dos achados de um revisor é ruído por obediência; se você não consegue verificar, não faz merge.