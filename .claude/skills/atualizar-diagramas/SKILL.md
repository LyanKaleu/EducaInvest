---
name: atualizar-diagramas
description: Atualiza os diagramas UML/ER de docs/diagramas (Archify) e o grafo do código (Graphify) depois que o código mudou. Use quando pedirem para atualizar, conferir ou refazer os diagramas, ao fechar um PR que mexeu em app/, ou quando ele perguntar se os diagramas ainda batem com o código.
---

# Atualizar os diagramas do EducaInvest

`docs/diagramas/index.html` junta 13 diagramas do Archify e o grafo do Graphify. A pasta é privada (`docs/*` no `.gitignore`): **nunca a commite**.
Cada diagrama nasce de um candidato em `docs/diagramas/fonte/<n>.json`, fixado num commit (`meta.repository.revision`), e cada peça cita arquivo e linha desse commit.

O Graphify se atualiza sozinho e sem IA. O Archify **não**: ele só valida e desenha o que estiver no candidato. Quem decide o que muda no desenho é você, lendo o código.

## 0. Pré-requisitos (só na primeira vez em cada máquina)
- Graphify: `command -v graphify` (senão `uv tool install graphifyy`).
- Archify: `~/.archify-src/archify/bin/archify.mjs` precisa existir. Se não existir, siga a instalação da skill `diagramas-archify`: `git clone --depth 1 https://github.com/tt-a1i/archify ~/.archify-src` e depois `node ~/.archify-src/archify/bin/archify.mjs doctor`. Nunca use `npm install archify`, que é outro projeto.
- `docs/diagramas/fonte/` precisa existir. Ela não vai pelo Git: em outra máquina, peça a quem tem os diagramas para copiar a pasta `docs/diagramas/` inteira.

## 1. O código precisa estar commitado
O Archify confere as citações contra os bytes de um commit, não contra a árvore de trabalho. Rode `git status --short -- app run.py`: se houver mudança sem commit em `app/`, pare e avise.

## 2. Descubra o que mudou
```bash
node .claude/skills/atualizar-diagramas/afetados.mjs
```
- `AFETADO <diagrama>: <arquivos>`: algum arquivo citado mudou desde a revisão do diagrama.
- `ESTRUTURA`: há `.py` novo, removido ou renomeado. Avalie pacotes (07), componentes (05), classes (03) e banco (13), mesmo sem citação.
- `NADA a atualizar`: pare aqui. Rode só o passo 3, se quiserem o grafo novo.

O mapa mental (01) depende de AGENTS.md, INVARIANTES.md e ESTADO.md: atualize-o só se mudou funcionalidade, regra ou próximo passo, não por ajuste de texto.

## 3. Grafo do Graphify
```bash
bash .claude/skills/atualizar-diagramas/grafo.sh
```
Ele refaz o grafo numa pasta temporária e substitui `00-grafo-graphify.html`. Use as peças mais ligadas que ele imprime e `graphify explain "<nó>" --graph <tmp>/graphify-out/graph.json` para achar as chamadas novas, antes de abrir os arquivos.

## 4. Para cada diagrama afetado
1. Veja o que mudou: `git diff <revisão>..HEAD -- <arquivos citados>`.
2. Releia o código atual com número de linha (`nl -ba arquivo | sed -n 'a,bp'`). Corrija no candidato só o que mudou: rótulos, peças, ligações e `sources` (`line` e `end_line`). Não invente peça que o código não mostra.
3. Ponha `meta.repository.revision` = `git rev-parse HEAD`.
4. Valide: `bash .claude/skills/atualizar-diagramas/finalizar.sh <n> [<n> ...]`.
5. Se der ERRO, conserte a causa que o diagnóstico aponta e rode de novo. Pegadinhas já vistas:
   - `architecture` com `row`/`col` exige `layout: {mode: "grid", cols, cellW, cellH}`. Sem isso dá `internal/unclassified ... reading '0'`.
   - `*-label-overflow`: encurte o rótulo, ponha o nome técnico no `sublabel` ou aumente o `size`.
   - Mensagens de sequência a menos de 28px uma da outra: espalhe os `y` de 32 em 32.
   - `workflow/column-capacity`: passe para `schema_version: 2`. O workflow aceita no máximo 6 colunas (0 a 5).
   - `layout/marker-capacity` no diagrama de classes: setas demais num lado só. Tire a relação que um atributo já mostra.
6. Quando todos passarem, rode `bash .claude/skills/atualizar-diagramas/finalizar.sh` sem nomes para conferir o conjunto.

Os quatro diagramas marcados como "aproximação" (casos de uso, objetos, estrutura composta e comunicação) usam o tipo do Archify mais parecido, e o subtítulo de cada um diz isso. Mantenha esse aviso.

## 5. Página central e conferência visual
- Troque o commit citado no subtítulo de `docs/diagramas/index.html` ("no commit xxxxxxx") pelo novo.
- Diagrama novo ou removido: ajuste a lista do `<nav>` no `index.html`.
- Abra com `preview_start` no servidor `diagramas` (`.claude/launch.json`, porta 5010) e olhe pelo menos os diagramas refeitos. O painel do app não carrega os quadros por `file://`.

## 6. Relatório
Diga quais diagramas mudaram e por quê (o commit e o que mudou no código), quais passaram e quais você olhou de fato. Não commite nada de `docs/diagramas`.
