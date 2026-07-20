# testar_conexao.py - Testa se o Python conecta ao banco

from banco import engine
from sqlalchemy import text

try:
    with engine.connect() as conexao:
        resultado = conexao.execute(text("SELECT 'Conexão funcionando!' as mensagem"))
        for linha in resultado:
            print(linha[0])
except Exception as erro:
    print(f"Erro na conexão: {erro}")