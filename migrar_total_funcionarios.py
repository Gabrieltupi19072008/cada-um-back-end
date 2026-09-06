# migrar_total_funcionarios.py - Adiciona a coluna total_funcionarios em Empresa,
# usada pra calcular a cota legal de PcD (Art. 93 da Lei nº 8.213/91).
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_total_funcionarios.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE empresas ADD COLUMN IF NOT EXISTS total_funcionarios INTEGER",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
