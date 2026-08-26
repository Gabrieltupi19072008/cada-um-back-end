# usuarios.py - Rotas genericas de usuario (perfil basico e foto), validas pra
# qualquer perfil (candidato, empresa ou admin) -- todos tem uma linha em "usuarios".

import base64
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario
from dependencias import obter_usuario_atual
from schemas import UsuarioMe, FotoAtualizar

roteador = APIRouter(prefix="/usuarios", tags=["Usuarios"])

_PADRAO_DATA_URI = re.compile(r"^data:image/(png|jpeg|jpg|webp);base64,")
_TAMANHO_MAXIMO_BYTES = 2 * 1024 * 1024  # 2 MB


@roteador.get("/me", response_model=UsuarioMe)
def obter_meu_usuario(usuario: Usuario = Depends(obter_usuario_atual)):
    return usuario


@roteador.put("/me/foto", response_model=UsuarioMe)
def atualizar_minha_foto(
    dados: FotoAtualizar,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    if not _PADRAO_DATA_URI.match(dados.foto_base64):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagem inválido. Use PNG, JPEG ou WEBP.",
        )

    parte_base64 = dados.foto_base64.split(",", 1)[1]
    try:
        bruto = base64.b64decode(parte_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Imagem corrompida")

    if len(bruto) > _TAMANHO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Imagem muito grande (máximo 2 MB). Tente uma foto menor.",
        )

    usuario.foto_url = dados.foto_base64
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


@roteador.delete("/me/foto", response_model=UsuarioMe)
def remover_minha_foto(
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    usuario.foto_url = None
    sessao.commit()
    sessao.refresh(usuario)
    return usuario
