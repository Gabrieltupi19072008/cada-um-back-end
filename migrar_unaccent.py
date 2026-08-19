# migrar_unaccent.py - Habilita a extensao unaccent do Postgres, usada pra buscar
# candidatos ignorando acentos (ex: "Maceio" encontra candidato com cidade "Maceió").
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez (IF NOT EXISTS).
# Uso: python migrar_unaccent.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "CREATE EXTENSION IF NOT EXISTS unaccent",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
