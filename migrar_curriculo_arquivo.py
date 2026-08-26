# migrar_curriculo_arquivo.py - Adiciona colunas pro candidato anexar o proprio
# curriculo pronto (PDF/Word), como alternativa a preencher tudo manualmente.
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_curriculo_arquivo.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curriculo_arquivo TEXT",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curriculo_nome_arquivo VARCHAR(255)",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
