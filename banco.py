from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# URL completa de conexão (Postgres/Supabase). Copie do painel do Supabase em
# Project Settings > Database > Connection string (modo "Transaction pooler").
URL_BANCO = os.getenv("DATABASE_URL", "postgresql+pg8000://postgres:postgres@localhost:5432/conectatea")

engine = create_engine(URL_BANCO, echo=False, pool_pre_ping=True)
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def obter_sessao():
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()