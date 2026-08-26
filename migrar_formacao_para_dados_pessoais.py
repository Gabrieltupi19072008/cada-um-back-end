# migrar_formacao_para_dados_pessoais.py - Consolida a formacao (antes uma aba/tabela
# separada, com varias entradas por candidato) em dois campos novos direto em Candidato:
# instituicao_ensino e curso, ao lado de escolaridade. Copia os dados ja existentes na
# tabela "formacoes" antes de o codigo parar de usa-la (a tabela em si nao e apagada).
# Roda uma vez contra o banco configurado no .env. E' seguro rodar mais de uma vez.
# Uso: python migrar_formacao_para_dados_pessoais.py

from banco import engine
from sqlalchemy import text

COMANDOS_COLUNAS = [
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS instituicao_ensino VARCHAR(150)",
    "ALTER TABLE candidatos ADD COLUMN IF NOT EXISTS curso VARCHAR(150)",
]

with engine.connect() as conexao:
    for comando in COMANDOS_COLUNAS:
        conexao.execute(text(comando))
        conexao.commit()
        print("OK:", comando)

    # Para cada candidato com formacao cadastrada e que ainda nao tem curso/instituicao
    # preenchidos, copia a formacao mais recente (maior ano_conclusao, NULLs por ultimo).
    resultado = conexao.execute(
        text(
            """
            UPDATE candidatos AS c
            SET instituicao_ensino = f.instituicao,
                curso = f.curso
            FROM (
                SELECT DISTINCT ON (candidato_id) candidato_id, instituicao, curso
                FROM formacoes
                ORDER BY candidato_id, ano_conclusao DESC NULLS LAST, id DESC
            ) AS f
            WHERE f.candidato_id = c.id
              AND c.curso IS NULL
              AND c.instituicao_ensino IS NULL
            """
        )
    )
    conexao.commit()
    print(f"Candidatos migrados de 'formacoes' para os campos novos: {resultado.rowcount}")

print("Migração concluída.")
