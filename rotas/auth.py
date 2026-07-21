# auth.py - Rotas de cadastro e login

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario, PerfilEnum
from Candidato import Candidato
from Empresa import Empresa
from seguranca import gerar_hash_senha, verificar_senha, criar_token_acesso, gerar_senha_temporaria
from schemas import (
    CandidatoCadastro,
    EmpresaCadastro,
    Token,
    EsqueciSenhaEntrada,
    EsqueciSenhaResposta,
)

roteador = APIRouter(prefix="/auth", tags=["Autenticação"])


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


@roteador.post("/esqueci-senha", response_model=EsqueciSenhaResposta)
def esqueci_senha(dados: EsqueciSenhaEntrada, sessao: Session = Depends(obter_sessao)):
    """
    Gera uma senha temporária nova para o e-mail informado, se ele existir.
    NOTA: ainda não há envio de e-mail configurado — a senha volta na própria resposta
    para fins de desenvolvimento. Trocar por envio real de e-mail (e resposta genérica,
    sem revelar se o e-mail existe) antes de colocar em produção.
    """
    usuario = sessao.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is None:
        return EsqueciSenhaResposta(encontrado=False)

    senha_nova = gerar_senha_temporaria()
    usuario.senha_hash = gerar_hash_senha(senha_nova)
    sessao.commit()

    return EsqueciSenhaResposta(encontrado=True, senha_temporaria=senha_nova)
