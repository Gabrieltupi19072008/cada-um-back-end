from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NOME = os.getenv("DB_NOME", "conectatea")
DB_USUARIO = os.getenv("DB_USUARIO", "root")
DB_SENHA = os.getenv("DB_SENHA", "")

URL_BANCO = f"mysql+pymysql://{DB_USUARIO}:{DB_SENHA}@{DB_HOST}:{DB_PORT}/{DB_NOME}?charset=utf8mb4"

engine = create_engine(URL_BANCO, echo=False)
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def obter_sessao():
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()