"""Hook PreToolUse: protege caminhos sensíveis antes de qualquer edição (INVARIANTES O2 e O3).

Bloqueia segredos e dados locais. Para acesso, sessão, dependências e o próprio portão,
pede confirmação humana: o agente não consegue "consertar" o gate relaxando a regra.
"""
import json
import os
import re
import sys
from fnmatch import fnmatch

BLOQUEADOS = {
    ".env": "segredo", ".env.*": "segredo", "*/.env": "segredo", "*/.env.*": "segredo",
    "instance/*": "banco e dados locais", "*.db": "banco local", "*.sqlite*": "banco local",
}

PEDEM_APROVACAO = {
    "app/routes/acesso.py": "controle de acesso (O2)",
    "app/routes/auth.py": "login e sessão (O2)",
    "app/services/auth_service.py": "autenticação (O2)",
    "app/__init__.py": "SECRET_KEY e cookie de sessão (O2)",
    "requirements*.txt": "dependências (O3)",
    "pyproject.toml": "regras do gate (O3)",
    "gate.sh": "portão (O3)",
    ".github/workflows/*": "CI (O3)",
    ".claude/*": "hooks e permissões (O3)",
}


def _normalizar(caminho: str) -> str:
    """No Windows, converte o formato do Git Bash (/c/Users/...) para C:/Users/..."""
    msys = re.match(r"^/([a-zA-Z])/(.*)$", caminho)
    if os.name == "nt" and msys:
        return f"{msys.group(1)}:/{msys.group(2)}"
    return caminho


def caminho_relativo(dados: dict) -> str | None:
    """Caminho do arquivo alvo relativo à raiz do projeto, com "/"; None se não houver."""
    entrada = dados.get("tool_input") or {}
    alvo = entrada.get("file_path") or entrada.get("notebook_path")
    if not alvo:
        return None
    raiz = os.environ.get("CLAUDE_PROJECT_DIR") or dados.get("cwd") or os.getcwd()
    try:
        relativo = os.path.relpath(os.path.abspath(_normalizar(alvo)),
                                   os.path.abspath(_normalizar(raiz)))
    except ValueError:  # outro disco no Windows: fora do projeto
        return None
    relativo = relativo.replace("\\", "/")
    return None if relativo.startswith("../") else relativo


def decidir(relativo: str) -> tuple[str, str] | None:
    """Devolve ("deny" | "ask", motivo) ou None para liberar."""
    for padrao, motivo in BLOQUEADOS.items():
        if fnmatch(relativo, padrao):
            return "deny", f"{relativo} é {motivo}. O agente não edita este arquivo; peça ao humano."
    for padrao, motivo in PEDEM_APROVACAO.items():
        if fnmatch(relativo, padrao):
            return "ask", f"{relativo}: {motivo}. Exige aprovação humana (INVARIANTES.md)."
    return None


def main() -> None:
    try:
        dados = json.load(sys.stdin)
    except ValueError:
        return  # entrada inesperada: não trava o agente; o gate e o CI continuam valendo
    relativo = caminho_relativo(dados)
    decisao = decidir(relativo) if relativo else None
    if decisao:
        permissao, motivo = decisao
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": permissao,
            "permissionDecisionReason": motivo,
        }}))  # ensure_ascii padrão: acentos viram \uXXXX e sobrevivem ao console do Windows


if __name__ == "__main__":
    main()
