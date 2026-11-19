# Construindo produtos com IA: guia de arquitetura

## Sumário
1. Escolhendo o padrão certo
2. RAG
3. Ferramentas e agentes
4. Prompts e saídas estruturadas
5. Avaliação
6. Custo e latência
7. Observabilidade
8. Segurança e guardrails
9. Checklist antes de ir para produção

## 1. Escolhendo o padrão certo

Do mais simples ao mais complexo; pare no primeiro que resolve:

| Padrão | Use quando | Cuidado |
|---|---|---|
| Regra/código tradicional | O problema é determinístico | Não force LLM onde `if` resolve |
| Prompt único + saída estruturada | Classificar, extrair, resumir, reescrever | Defina o formato e valide |
| RAG | Resposta depende de documentos próprios/atuais | Qualidade da busca decide tudo |
| Ferramentas (function calling) | O modelo precisa consultar ou agir | Permissões mínimas, validação |
| Fluxo encadeado (workflow) | Passos conhecidos e fixos | Mais previsível que agente |
| Agente autônomo | Passos não previsíveis de antemão | Limites de passos/custo, logs |

## 2. RAG

- **Ingestão**: limpeza do texto, divisão em chunks com sobreposição razoável, metadados (fonte, data, seção).
- **Recuperação**: busca vetorial, busca por palavras-chave (BM25) ou híbrida; reranking costuma dar ganho grande.
- **Geração**: instruir o modelo a responder só com base no contexto recuperado, citar fontes e dizer "não sei" quando faltar informação.
- **Falhas típicas**: chunks grandes ou pequenos demais, perguntas que exigem várias fontes, documentos desatualizados, ausência de avaliação da recuperação separada da geração.
- Avalie recuperação (o trecho certo veio?) e geração (a resposta é fiel ao contexto?) separadamente.

## 3. Ferramentas e agentes

- Descreva cada ferramenta com nome claro, descrição objetiva e esquema de parâmetros estrito.
- Valide argumentos no código; nunca confie cegamente no que o modelo gerou.
- Dê o menor conjunto de permissões possível; ações destrutivas ou irreversíveis exigem confirmação humana.
- Defina limite de iterações, de tempo e de custo; trate loops.
- Registre cada chamada de ferramenta e resultado para depuração.
- Se o fluxo é previsível, prefira um workflow fixo a um agente.

## 4. Prompts e saídas estruturadas

- Seja explícito sobre papel, tarefa, formato e restrições; explique o porquê das regras importantes.
- Use exemplos (positivos e negativos) para comportamentos difíceis de descrever.
- Separe instruções de dados do usuário (delimitadores/tags) para reduzir injeção.
- Peça saída em JSON/esquema e valide (pydantic em Python, Zod em TypeScript); trate falha de parsing com retry controlado.
- Versione prompts como código e mude uma coisa por vez.

## 5. Avaliação

Sem avaliação, otimizar é chute.

1. Monte um conjunto inicial de 20 a 50 casos reais, incluindo difíceis e casos de borda.
2. Defina critérios: exatidão, fidelidade ao contexto, formato, tom, segurança.
3. Combine verificações automáticas (regras, comparação com gabarito), avaliação por modelo (LLM-as-judge, calibrada com amostras humanas) e revisão humana.
4. Rode a avaliação a cada mudança de prompt, modelo ou parâmetro; compare com a versão anterior.
5. Realimente com falhas encontradas em produção.

## 6. Custo e latência

- Escolha o menor modelo que atinge a qualidade necessária; use modelos maiores só onde importa.
- Reduza tokens: contexto enxuto, resumo de histórico, recuperação precisa.
- Use cache de prompt/resposta quando disponível e adequado; processamento em lote para tarefas não interativas.
- Streaming melhora a percepção de velocidade; paralelize chamadas independentes.
- Meça custo por requisição e por usuário desde cedo e configure alertas.

## 7. Observabilidade

- Registre entrada, saída, modelo, parâmetros, versão do prompt, tokens, latência, custo e erros (cuidando de dados pessoais).
- Rastreie cadeias de chamadas (traces) em fluxos com várias etapas.
- Colete feedback do usuário (positivo/negativo) e use para ampliar o conjunto de avaliação.

## 8. Segurança e guardrails

- **Prompt injection**: trate qualquer texto externo (páginas, e-mails, documentos) como dado, não como instrução; limite o que o modelo pode fazer com ele.
- **Vazamento de dados**: não inclua no contexto o que o usuário não pode ver; aplique controle de acesso na recuperação.
- **Saídas**: valide e sanitize antes de executar, renderizar ou gravar.
- **Privacidade**: minimize dados pessoais enviados, observe LGPD, defina retenção.
- **Moderação e limites**: filtros de entrada/saída quando o risco justificar; rate limiting.
- **Alucinação**: exija fontes, permita "não sei", verifique fatos críticos.

## 9. Checklist antes de ir para produção

- [ ] Um LLM é realmente necessário, e o padrão é o mais simples possível?
- [ ] Existe conjunto de avaliação e resultado de referência?
- [ ] Custo por uso estimado e com alerta?
- [ ] Timeouts, retries e fallback definidos?
- [ ] Saídas validadas por esquema?
- [ ] Defesas contra prompt injection e controle de acesso aos dados?
- [ ] Logs e métricas sem expor dados sensíveis?
- [ ] Plano para mudança de modelo/versão e rollback?
- [ ] Supervisão humana para ações de alto impacto?
