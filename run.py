"""Ponto de entrada: inicia o servidor de desenvolvimento com `python run.py`.

Em produção, use a fábrica diretamente (ex.: `gunicorn "app:create_app()"`)
com a variável de ambiente SECRET_KEY definida.
"""
from app import create_app

if __name__ == "__main__":
    # DEBUG permite rodar sem SECRET_KEY (gera uma aleatória). Só para desenvolvimento.
    create_app({"DEBUG": True}).run(debug=True)
