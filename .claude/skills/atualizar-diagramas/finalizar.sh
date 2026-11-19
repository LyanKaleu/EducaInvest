#!/usr/bin/env bash
# Valida e gera o HTML de cada diagrama com o Archify, contra o código commitado.
# Uso: bash .claude/skills/atualizar-diagramas/finalizar.sh [nomes sem .json]   (sem nomes: todos)
set -u
RAIZ=$(git rev-parse --show-toplevel)
D="$RAIZ/docs/diagramas"
ARCHIFY="$HOME/.archify-src/archify/bin/archify.mjs"
[ -f "$ARCHIFY" ] || { echo "Archify não instalado: veja o passo 0 da skill."; exit 1; }
nomes="$*"; [ -z "$nomes" ] && nomes=$(ls "$D/fonte" | sed 's/\.json$//')
falhou=0
for n in $nomes; do
  tipo=$(node -e 'console.log(require(process.argv[1]).diagram_type)' "$D/fonte/$n.json")
  node "$ARCHIFY" finalize "$tipo" "$D/fonte/$n.json" "$D/$n.html" --repo-root "$RAIZ" --quality showcase --json 2>&1 \
  | node -e '
    let s = ""; process.stdin.on("data", (d) => (s += d)).on("end", () => {
      const n = process.argv[1];
      try {
        const r = JSON.parse(s), out = [];
        (function w(o) { if (o && typeof o === "object") {
          if (o.code && o.message) out.push(`   - ${o.code} @${(o.subject && (o.subject.path || o.subject.nodeId)) || ""}: ${o.message.slice(0, 240)}`);
          for (const k in o) w(o[k]); } })(r.diagnostics || []);
        console.log(`${r.ok ? "OK  " : "ERRO"} ${n}`);
        if (out.length) console.log([...new Set(out)].slice(0, 15).join("\n"));
        process.exitCode = r.ok ? 0 : 1;
      } catch { console.log(`ERRO ${n} (saída não-JSON)\n${s.slice(-800)}`); process.exitCode = 1; }
    });' "$n" || falhou=1
done
exit $falhou
