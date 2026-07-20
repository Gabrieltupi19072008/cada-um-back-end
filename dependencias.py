# dependencias.py - Dependências reutilizáveis do FastAPI

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from banco import obter_sessao
from Usuario import Usuario
from seguranca import decodificar_token

oauth2_esquema = OAuth2PasswordBearer(tokenUrl="/auth/login")


def obter_usuario_atual(
    token: str = Depends(oauth2_esquema),
    sessao: Session = Depends(obter_sessao)
) -> Usuario:
    """Retorna o usuário logado a partir do token JWT."""
    excecao = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    dados = decodificar_token(token)
    if dados is None:
        raise excecao
    email = dados.get("sub")
    if email is None:
        raise excecao
    usuario = sessao.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.ativo:
        raise excecao
    return usuario


def exigir_perfil(perfil: str):
    """Cria uma dependência que exige um perfil específico."""
    def verificar(usuario: Usuario = Depends(obter_usuario_atual)):
        if usuario.perfil != perfil:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito a perfil: {perfil}"
            )
        return usuario
    return verificar

exigir_candidato = exigir_perfil("candidato")
exigir_empresa = exigir_perfil("empresa")
exigir_admin = exigir_perfil("admin")