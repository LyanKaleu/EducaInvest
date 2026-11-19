---
name: "diagramas-archify"
description: "Use quando o usuário quiser um diagrama (arquitetura, fluxo, sequência, ERD, timeline etc.) ou um explicador em página única, como HTML navegável e exportável, em vez de uma imagem estática."
---

# Diagramas e explicadores em página única (Archify)

Inspirado no projeto `archify` (tt-a1i/archify). Gera diagramas validados como HTML autônomo e explorável, em vez de uma imagem SVG simples.

## Quando usar

- Visualizar sistemas, chamadas de API, pipelines, schemas de dados, históricos ou passos de um processo.
- Transformar uma explicação em texto numa página única com a conclusão primeiro, painéis estruturados e diagramas/gráficos nativos, quando o usuário pedir algo como "faz uma página sobre isso" ou "explica isso numa página".
- Não usar para dashboards de métricas (isso é outro tipo de artifact).

## Instalação (fazer antes do primeiro uso)

O Archify **não** é instalado pelo npm. O pacote `archify` do npm é um projeto diferente, sem relação com este: **nunca rode `npx archify` nem `npm install archify`**. A CLI de verdade fica dentro do repositório do GitHub:

```bash
# só se a pasta ainda não existir
git clone --depth 1 https://github.com/tt-a1i/archify ~/.archify-src
ARCHIFY="node $HOME/.archify-src/archify/bin/archify.mjs"
$ARCHIFY doctor   # deve terminar com "Archify is ready."
```

Requer Node 18 ou superior. Nos comandos abaixo, `$ARCHIFY` é esse caminho absoluto.

Comandos principais:
- `$ARCHIFY guide "<cenário>" --json`: recomenda o tipo de diagrama (architecture, workflow, sequence, erd...) para o que o usuário descreveu.
- `$ARCHIFY finalize <tipo> <candidate.json> <saida.html> --quality showcase --json`: valida o candidato e gera o HTML final. Para um diagrama baseado em código, acrescente `--repo-root <raiz-do-repo>`.
- `$ARCHIFY demo <pasta>`: gera exemplos de referência.

Para detalhes do formato do `candidate.json` de cada tipo, leia `~/.archify-src/archify/SKILL.md` e as referências da mesma pasta.

## Workflow

1. Identifique o tipo de artefato (use `$ARCHIFY guide` se estiver em dúvida):
   - **Diagrama nativo**: para visualizar um sistema/fluxo real. Se houver um repositório de código envolvido, inspecione evidências reais no código antes de desenhar (não invente componentes ou chamadas que não existem no código).
   - **Explicador de uma página**: para responder uma pergunta com conclusão primeiro + seções estruturadas + diagramas de apoio.
2. Rode os comandos `$ARCHIFY` a partir do diretório de trabalho atual; crie uma pasta nova por pedido de artefato (ex.: `.archify/<tipo>-<slug>-<timestamp>/`) para manter candidato e saída juntos e permitir reparos posteriores.
3. Para um diagrama nativo, monte o `candidate.json` descrevendo a estrutura (ou aceite Mermaid como entrada) e gere o HTML final com `$ARCHIFY finalize`.
4. Para um explicador, use o `candidate.archify.md` com a conclusão em primeiro lugar, depois os painéis de apoio.
5. Valide a saída (o próprio `archify` valida o candidato antes de gerar o HTML final) e entregue o arquivo gerado ao usuário, publicando como artifact quando fizer sentido para o fluxo de trabalho.
6. Um pedido novo de diagrama ganha uma pasta nova; só reutilize a pasta existente para corrigir o mesmo artefato.