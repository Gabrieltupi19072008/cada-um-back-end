# main.py - Arquivo principal do servidor FastAPI

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rotas import auth, candidatos, empresas, admin

load_dotenv()

app = FastAPI(
    title="CadaUm API",
    description="Plataforma de currículos para pessoas com TEA",
    version="1.0.0",
)

# Permite requisições do frontend. ORIGENS_PERMITIDAS no .env aceita várias
# URLs separadas por vírgula (ex: produção + localhost ao mesmo tempo).
origens = os.getenv("ORIGENS_PERMITIDAS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origem.strip() for origem in origens],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.roteador)
app.include_router(candidatos.roteador)
app.include_router(empresas.roteador)
app.include_router(admin.roteador)


@app.get("/")
def raiz():
    return {"mensagem": "API CadaUm funcionando!", "versao": "1.0.0"}