#!/usr/bin/env bash
# Roda protege.py com o Python do projeto (venv) se existir; senão, o do sistema.
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
for py in .venv/Scripts/python.exe .venv/bin/python; do
  if [ -x "$py" ]; then exec "$py" .claude/hooks/protege.py; fi
done
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then exec "$py" .claude/hooks/protege.py; fi
done
exit 0
