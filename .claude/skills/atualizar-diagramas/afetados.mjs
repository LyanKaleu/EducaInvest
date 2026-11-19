// Lista os diagramas de docs/diagramas que o código mudado desde a revisão deles afeta.
// Uso: node .claude/skills/atualizar-diagramas/afetados.mjs [revisão-alvo, padrão HEAD]
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const FONTE = process.env.FONTE || "docs/diagramas/fonte";
const alvo = process.argv[2] || "HEAD";
const git = (...args) => execFileSync("git", args, { encoding: "utf8" }).trim();

// Todo objeto com `path` de arquivo dentro do candidato é uma referência ao código.
const caminhos = (obj, acc = new Set()) => {
  if (Array.isArray(obj)) obj.forEach((o) => caminhos(o, acc));
  else if (obj && typeof obj === "object") {
    if (typeof obj.path === "string" && /\.\w+$/.test(obj.path)) acc.add(obj.path);
    Object.values(obj).forEach((v) => caminhos(v, acc));
  }
  return acc;
};

const diagramas = fs.readdirSync(FONTE).filter((f) => f.endsWith(".json")).sort().map((f) => {
  const c = JSON.parse(fs.readFileSync(path.join(FONTE, f), "utf8"));
  return { nome: f.replace(/\.json$/, ""), rev: c.meta?.repository?.revision, paths: [...caminhos(c)] };
});
const revs = diagramas.map((d) => d.rev).filter(Boolean);
const conta = (r) => revs.filter((x) => x === r).length;
const revComum = [...revs].sort((a, b) => conta(b) - conta(a))[0];
const head = git("rev-parse", alvo);

let algum = false;
for (const d of diagramas) {
  const rev = d.rev || revComum;
  // O mapa mental não cita código: ele resume a documentação de produto.
  const paths = d.paths.length ? d.paths : ["AGENTS.md", "INVARIANTES.md", "ESTADO.md"];
  if (rev === head) continue;
  const mudou = git("diff", "--name-only", rev, head, "--", ...paths).split("\n").filter(Boolean);
  if (mudou.length) {
    algum = true;
    console.log(`AFETADO ${d.nome} (desde ${rev.slice(0, 7)}): ${mudou.join(", ")}`);
  }
}
// Arquivo novo ou removido em app/ não aparece em nenhuma citação: pacotes, componentes,
// classes e banco podem precisar de uma peça nova.
const novos = git("diff", "--name-status", "--diff-filter=ADR", revComum, head, "--", ":(glob)app/**/*.py", "run.py")
  .split("\n").filter(Boolean);
if (novos.length) {
  algum = true;
  console.log(`ESTRUTURA arquivos novos, removidos ou renomeados desde ${revComum.slice(0, 7)}:\n  ${novos.join("\n  ")}`);
}
if (!algum) console.log(`NADA a atualizar: nenhum arquivo citado mudou até ${head.slice(0, 7)}.`);
