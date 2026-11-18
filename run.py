"""Ponto de entrada: inicia o servidor de desenvolvimento com `python run.py`.

Em produção, use a fábrica diretamente (ex.: `gunicorn "app:create_app()"`)
com a variável de ambiente SECRET_KEY definida.
"""

from app import create_app

if __name__ == "__main__":
    # DEBUG permite rodar sem SECRET_KEY (gera uma aleatória). Só para
    # desenvolvimento. NUNCA passe host="0.0.0.0" aqui: o depurador do Werkzeug
    # deixa quem acessa a página de erro executar código no servidor. Para
    # expor o app, use um servidor WSGI.
    create_app({"DEBUG": True}).run(debug=True)
