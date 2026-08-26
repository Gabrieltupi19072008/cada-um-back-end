# migrar_foto_usuario.py - Adiciona a coluna de foto de perfil em Usuario (compartilhada
# por candidato, empresa e admin -- todos tem uma linha em "usuarios").
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_foto_usuario.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS foto_url TEXT",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
