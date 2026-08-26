# migrar_status_selecionado.py - Adiciona o valor "selecionado" ao ENUM nativo do Postgres
# statusinteresseenum, e cria a tabela de mensagens do chat entre empresa e candidato.
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_status_selecionado.py

from banco import engine
from sqlalchemy import text

# ALTER TYPE ... ADD VALUE nao pode ser usado na mesma transacao em que o valor e'
# adicionado -- por isso cada comando roda e commita separado, antes de qualquer
# outra coisa tentar gravar 'selecionado'.
with engine.connect() as conexao:
    conexao.execute(text("ALTER TYPE statusinteresseenum ADD VALUE IF NOT EXISTS 'selecionado'"))
    conexao.commit()
    print("OK: ALTER TYPE statusinteresseenum ADD VALUE IF NOT EXISTS 'selecionado'")

COMANDOS_TABELA = [
    """
    CREATE TABLE IF NOT EXISTS mensagens_chat (
        id SERIAL PRIMARY KEY,
        interesse_id INTEGER NOT NULL REFERENCES interesses(id) ON DELETE CASCADE,
        remetente_usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        corpo TEXT NOT NULL,
        criado_em TIMESTAMP DEFAULT now()
    )
    """,
]

with engine.connect() as conexao:
    for comando in COMANDOS_TABELA:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK: tabela mensagens_chat")

print("Migração concluída.")
