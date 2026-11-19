#!/usr/bin/env bash
# Refaz o grafo do Graphify a partir de app/ numa pasta temporária (sem criar graphify-out/ no repositório)
# e copia o HTML para docs/diagramas/00-grafo-graphify.html. Não usa IA nem tokens.
set -eu
RAIZ=$(git rev-parse --show-toplevel)
command -v graphify >/dev/null || { echo "Graphify não instalado: uv tool install graphifyy"; exit 1; }
TMP=$(mktemp -d)
cp -r "$RAIZ/app" "$TMP/"
(cd "$TMP" && graphify update . --force 2>&1 | grep -E "Rebuilt|nodes" || true)
cp "$TMP/graphify-out/graph.html" "$RAIZ/docs/diagramas/00-grafo-graphify.html"
sed -n '/## God Nodes/,/^## Surprising/p' "$TMP/graphify-out/GRAPH_REPORT.md" | head -14
echo "Relatório completo: $TMP/graphify-out/GRAPH_REPORT.md"
