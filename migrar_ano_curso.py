# migrar_ano_curso.py - Adiciona ano de inicio/conclusao e "em andamento" do curso
# principal em Candidato -- ficou faltando na consolidacao anterior (migrar_formacao_
# para_dados_pessoais.py so tinha copiado instituicao/curso, sem os anos).
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_ano_curso.py

from banco import engine
from sqlalchemy import text

COMANDOS_COLUNAS = [
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curso_ano_inicio INTEGER",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curso_ano_conclusao INTEGER",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curso_em_andamento BOOLEAN DEFAULT FALSE",
]

with engine.connect() as conexao:
    for comando in COMANDOS_COLUNAS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

    resultado = conexao.execute(
        text(
            """
            UPDATE candidatos AS c
            SET curso_ano_inicio = f.ano_inicio,
                curso_ano_conclusao = f.ano_conclusao,
                curso_em_andamento = f.em_andamento
            FROM (
                SELECT DISTINCT ON (candidato_id) candidato_id, curso, ano_inicio, ano_conclusao, em_andamento
                FROM formacoes
                ORDER BY candidato_id, ano_conclusao DESC NULLS LAST, id DESC
            ) AS f
            WHERE f.candidato_id = c.id
              AND c.curso = f.curso
              AND c.curso_ano_inicio IS NULL
              AND c.curso_ano_conclusao IS NULL
            """
        )
    )
    conexao.commit()
    print(f"Candidatos com ano/em_andamento migrados: {resultado.rowcount}")

print("Migração concluída.")
