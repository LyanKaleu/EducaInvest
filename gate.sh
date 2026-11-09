#!/usr/bin/env bash
# Portão único: o MESMO script roda no Stop hook do Claude Code e no CI.
# Ordem do mais barato ao mais caro. Sucesso: uma linha. Falha: só o essencial.
#
# Uso: bash gate.sh               lint + arquitetura + testes
#      bash gate.sh --sem-testes  lint + arquitetura (passo 1 do TDD: testes ainda vermelhos)
set -uo pipefail
cd "$(dirname "$0")"

PY=python
for candidato in .venv/Scripts/python.exe .venv/bin/python; do
  if [ -x "$candidato" ]; then PY=$candidato; break; fi
done

passo() {
  local nome=$1; shift
  local saida
  if ! saida=$("$@" 2>&1); then
    echo "GATE FALHOU em: $nome"
    echo "$saida" | tail -n 30
    exit 1
  fi
}

passo "lint (ruff)" "$PY" -m ruff check --quiet .
passo "arquitetura (import-linter)" "$PY" -c "from importlinter.cli import lint_imports_command; lint_imports_command()"
if [ "${1:-}" = "--sem-testes" ]; then
  echo "gate ok: lint, arquitetura (testes pulados)"
  exit 0
fi
passo "testes (pytest)" "$PY" -m pytest -q -p no:cacheprovider
echo "gate ok: lint, arquitetura, testes"
