# auth.py - Rotas de cadastro e login

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario, PerfilEnum
from Candidato import Candidato
from Empresa import Empresa
from notificacoes import enviar_email
from seguranca import gerar_hash_senha, verificar_senha, criar_token_acesso, gerar_token_redefinicao
from schemas import (
    CandidatoCadastro,
    EmpresaCadastro,
    Token,
    EsqueciSenhaEntrada,
    EsqueciSenhaResposta,
    RedefinirSenhaEntrada,
    RedefinirSenhaResposta,
)

roteador = APIRouter(prefix="/auth", tags=["Autenticação"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
TOKEN_REDEFINICAO_VALIDADE_HORAS = 1


def _verificar_email_disponivel(email: str, sessao: Session):
    if sessao.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado",
        )


def _validar_senha(senha: str):
    tem_letra = any(c.isalpha() for c in senha)
    tem_numero = any(c.isdigit() for c in senha)
    if len(senha) < 8 or not tem_letra or not tem_numero:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A senha precisa ter pelo menos 8 caracteres, com letras e números",
        )


@roteador.post("/cadastro/candidato", status_code=status.HTTP_201_CREATED)
def cadastrar_candidato(dados: CandidatoCadastro, sessao: Session = Depends(obter_sessao)):
    _verificar_email_disponivel(dados.email, sessao)
    _validar_senha(dados.senha)

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=PerfilEnum.candidato,
    )
    sessao.add(usuario)
    sessao.flush()  # gera o id do usuário antes de criar o candidato

    candidato = Candidato(
        usuario_id=usuario.id,
        cpf=dados.cpf,
        data_nascimento=dados.data_nascimento,
        cidade=dados.cidade,
        estado=dados.estado,
        telefone=dados.telefone,
    )
    sessao.add(candidato)
    sessao.commit()

    return {"mensagem": "Candidato cadastrado com sucesso", "usuario_id": usuario.id}


@roteador.post("/cadastro/empresa", status_code=status.HTTP_201_CREATED)
def cadastrar_empresa(dados: EmpresaCadastro, sessao: Session = Depends(obter_sessao)):
    _verificar_email_disponivel(dados.email, sessao)
    _validar_senha(dados.senha)

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=PerfilEnum.empresa,
    )
    sessao.add(usuario)
    sessao.flush()

    empresa = Empresa(
        usuario_id=usuario.id,
        cnpj=dados.cnpj,
        razao_social=dados.razao_social,
        setor=dados.setor,
        cidade=dados.cidade,
        estado=dados.estado,
    )
    sessao.add(empresa)
    sessao.commit()

    return {"mensagem": "Empresa cadastrada com sucesso", "usuario_id": usuario.id}


@roteador.post("/login", response_model=Token)
def login(
    formulario: OAuth2PasswordRequestForm = Depends(),
    sessao: Session = Depends(obter_sessao),
):
    usuario = sessao.query(Usuario).filter(Usuario.email == formulario.username).first()

    if not usuario or not verificar_senha(formulario.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")

    token = criar_token_acesso({"sub": usuario.email, "perfil": usuario.perfil.value})
    return Token(access_token=token, perfil=usuario.perfil.value)


_MENSAGEM_ESQUECI_SENHA = "Se esse e-mail estiver cadastrado, enviamos um link de redefinição para ele."


@roteador.post("/esqueci-senha", response_model=EsqueciSenhaResposta)
def esqueci_senha(dados: EsqueciSenhaEntrada, sessao: Session = Depends(obter_sessao)):
    """
    Gera um token de redefinição de senha e manda por e-mail um link para o usuário
    escolher uma senha nova. A resposta é sempre genérica, sem revelar se o e-mail
    existe na base (evita que alguém descubra quais e-mails têm conta).
    """
    usuario = sessao.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is not None:
        token = gerar_token_redefinicao()
        usuario.reset_token = token
        usuario.reset_token_expira = datetime.utcnow() + timedelta(hours=TOKEN_REDEFINICAO_VALIDADE_HORAS)
        sessao.commit()

        link = f"{FRONTEND_URL}/redefinir-senha?token={token}"
        enviar_email(
            destinatario=usuario.email,
            assunto="Redefinição de senha — CadaUm",
            corpo_html=(
                f"<p>Olá, {usuario.nome.split(' ')[0]}!</p>"
                "<p>Recebemos um pedido para redefinir a senha da sua conta no CadaUm.</p>"
                f'<p><a href="{link}">Clique aqui para escolher uma senha nova</a></p>'
                f"<p>Esse link expira em {TOKEN_REDEFINICAO_VALIDADE_HORAS} hora. "
                "Se você não pediu essa redefinição, pode ignorar este e-mail.</p>"
            ),
        )

    return EsqueciSenhaResposta(mensagem=_MENSAGEM_ESQUECI_SENHA)


@roteador.post("/redefinir-senha", response_model=RedefinirSenhaResposta)
def redefinir_senha(dados: RedefinirSenhaEntrada, sessao: Session = Depends(obter_sessao)):
    """Troca a senha do usuário dono do token, se ele existir e ainda for válido."""
    usuario = sessao.query(Usuario).filter(Usuario.reset_token == dados.token).first()
    if (
        usuario is None
        or usuario.reset_token_expira is None
        or usuario.reset_token_expira < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link inválido ou expirado. Solicite uma nova redefinição de senha.",
        )

    _validar_senha(dados.nova_senha)

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    usuario.reset_token = None
    usuario.reset_token_expira = None
    sessao.commit()

    return RedefinirSenhaResposta(mensagem="Senha redefinida com sucesso.")
