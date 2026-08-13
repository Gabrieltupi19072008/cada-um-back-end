# migrar_perfil_v2.py - Adiciona colunas do perfil expandido, privacidade e origem do interesse.
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez (IF NOT EXISTS).
# Uso: python migrar_perfil_v2.py

from banco import engine
from sqlalchemy import text

COMANDOS = [
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS escolaridade VARCHAR(50)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS cursos_profissionalizantes TEXT",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS bairros_aceitos VARCHAR(255)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS tipos_vinculo VARCHAR(60)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS visivel_para_empresas BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE interesses ADD COLUMN IF NOT EXISTS origem VARCHAR(20) NOT NULL DEFAULT 'empresa'",
]

with engine.connect() as conexao:
    for comando in COMANDOS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

print("Migração concluída.")
