# migrar_reset_senha.py - Adiciona as colunas de token de redefinição de senha.
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez (IF NOT EXISTS).
# Uso: python migrar_reset_senha.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64) UNIQUE",
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_token_expira TIMESTAMP",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
