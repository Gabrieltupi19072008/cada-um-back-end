# seguranca.py - Funções de autenticação e JWT

import secrets
import string

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_padrao_troque_em_producao")
ALGORITMO = os.getenv("ALGORITMO", "HS256")
TOKEN_EXPIRA_MINUTOS = int(os.getenv("TOKEN_EXPIRA_MINUTOS", "60"))

contexto_senha = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Verifica se a senha digitada bate com o hash salvo."""
    return contexto_senha.verify(senha_plana, senha_hash)

def gerar_hash_senha(senha: str) -> str:
    """Gera o hash bcrypt de uma senha."""
    return contexto_senha.hash(senha)

def criar_token_acesso(dados: dict) -> str:
    """Cria um token JWT com os dados do usuário."""
    dados_copia = dados.copy()
    expiracao = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRA_MINUTOS)
    dados_copia.update({"exp": expiracao})
    token = jwt.encode(dados_copia, SECRET_KEY, algorithm=ALGORITMO)
    return token

def decodificar_token(token: str):
    """Decodifica e valida um token JWT."""
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        return dados
    except JWTError:
        return None


def gerar_senha_temporaria(tamanho: int = 10) -> str:
    """Gera uma senha aleatória temporária (usada no fluxo de 'esqueci minha senha')."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(tamanho))