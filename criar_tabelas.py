# criar_tabelas.py - Cria todas as tabelas no banco configurado no .env (rodar uma vez)
# Uso: python criar_tabelas.py

from banco import Base, engine

# Precisa importar todos os models para o SQLAlchemy conhecer as tabelas
import Usuario
import Candidato
import Empresa
import Formacao
import Experiencia
import Habilidade
import Vaga
import Interesses

Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso.")
