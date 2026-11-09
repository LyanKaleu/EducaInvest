#!/usr/bin/env bash
# Hook Stop: o agente só encerra o turno com o gate verde.
# - Nada alterado (conversa pura): não roda nada, custo zero.
# - Só tests/ alterado (passo 1 do TDD, teste vermelho de propósito): lint + arquitetura.
# - Qualquer outra mudança: gate completo.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

alterados=$(git status --porcelain --untracked-files=all | cut -c4-)
[ -z "$alterados" ] && exit 0

modo=""
if ! echo "$alterados" | grep -qv '^tests/'; then
  modo="--sem-testes"
fi

if ! saida=$(bash gate.sh $modo 2>&1); then
  echo "$saida" >&2
  echo "O gate falhou. Corrija a causa antes de encerrar; não relaxe a regra." >&2
  exit 2
fi
exit 0
