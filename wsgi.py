# wsgi.py - Ponte entre o FastAPI (ASGI) e o PythonAnywhere, que exige WSGI no plano grátis.
# No painel do PythonAnywhere (aba "Web"), aponte o arquivo WSGI para importar
# "application" daqui em vez de usar o template padrão deles.

from a2wsgi import ASGIMiddleware
from main import app as aplicativo_asgi

application = ASGIMiddleware(aplicativo_asgi)
