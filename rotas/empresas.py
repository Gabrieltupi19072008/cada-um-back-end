# empresas.py - Rotas de perfil da empresa, vagas, busca de candidatos e envio de interesse

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario
from Empresa import Empresa
from Candidato import Candidato, GrauTeaEnum
from Experiencia import Experiencia
from Habilidade import Habilidade
from Vaga import Vaga
from Interesses import Interesse, StatusInteresseEnum
from dependencias import exigir_empresa
from schemas import (
    EmpresaAtualizar,
    EmpresaPerfil,
    VagaCriar,
    VagaResposta,
    CandidatoPublico,
    InteresseCriar,
    InteresseResposta,
    CotaResposta,
)

roteador = APIRouter(prefix="/empresas", tags=["Empresas"])


def _obter_empresa_do_usuario(usuario: Usuario, sessao: Session) -> Empresa:
    empresa = sessao.query(Empresa).filter(Empresa.usuario_id == usuario.id).first()
    if empresa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de empresa não encontrado")
    return empresa


def _exigir_empresa_aprovada(empresa: Empresa) -> Empresa:
    if not empresa.aprovada:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa ainda não aprovada pelo administrador",
        )
    return empresa


@roteador.get("/me", response_model=EmpresaPerfil)
def obter_meu_perfil(
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    return _obter_empresa_do_usuario(usuario, sessao)


@roteador.put("/me", response_model=EmpresaPerfil)
def atualizar_meu_perfil(
    dados: EmpresaAtualizar,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(empresa, campo, valor)

    sessao.commit()
    sessao.refresh(empresa)
    return empresa


@roteador.get("/me/vagas", response_model=list[VagaResposta])
def listar_minhas_vagas(
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    return sessao.query(Vaga).filter(Vaga.empresa_id == empresa.id).all()


@roteador.post("/me/vagas", response_model=VagaResposta, status_code=status.HTTP_201_CREATED)
def criar_vaga(
    dados: VagaCriar,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    _exigir_empresa_aprovada(empresa)

    vaga = Vaga(empresa_id=empresa.id, **dados.model_dump())
    sessao.add(vaga)
    sessao.commit()
    sessao.refresh(vaga)
    return vaga


@roteador.put("/me/vagas/{vaga_id}", response_model=VagaResposta)
def atualizar_vaga(
    vaga_id: int,
    dados: VagaCriar,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    vaga = sessao.query(Vaga).filter(Vaga.id == vaga_id, Vaga.empresa_id == empresa.id).first()
    if vaga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    for campo, valor in dados.model_dump().items():
        setattr(vaga, campo, valor)

    sessao.commit()
    sessao.refresh(vaga)
    return vaga


@roteador.delete("/me/vagas/{vaga_id}", status_code=status.HTTP_204_NO_CONTENT)
def encerrar_vaga(
    vaga_id: int,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    """Encerra a vaga (não apaga, só marca como inativa, pois pode ter interesses ligados a ela)."""
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    vaga = sessao.query(Vaga).filter(Vaga.id == vaga_id, Vaga.empresa_id == empresa.id).first()
    if vaga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    vaga.ativa = False
    sessao.commit()


@roteador.get("/candidatos", response_model=list[CandidatoPublico])
def buscar_candidatos(
    cidade: Optional[str] = None,
    estado: Optional[str] = None,
    grau_tea: Optional[GrauTeaEnum] = None,
    area: Optional[str] = None,
    habilidade: Optional[str] = None,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    _exigir_empresa_aprovada(empresa)

    consulta = sessao.query(Candidato).filter(Candidato.aprovado.is_(True))
    if cidade:
        consulta = consulta.filter(Candidato.cidade == cidade)
    if estado:
        consulta = consulta.filter(Candidato.estado == estado)
    if grau_tea:
        consulta = consulta.filter(Candidato.grau_tea == grau_tea)
    if area:
        consulta = consulta.join(Candidato.experiencias).filter(Experiencia.cargo.ilike(f"%{area}%"))
    if habilidade:
        consulta = consulta.join(Candidato.habilidades).filter(Habilidade.nome.ilike(f"%{habilidade}%"))

    return consulta.distinct().all()


@roteador.get("/candidatos/{candidato_id}", response_model=CandidatoPublico)
def obter_candidato(
    candidato_id: int,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    _exigir_empresa_aprovada(empresa)

    candidato = (
        sessao.query(Candidato)
        .filter(Candidato.id == candidato_id, Candidato.aprovado.is_(True))
        .first()
    )
    if candidato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")
    return candidato


@roteador.post("/me/interesses", response_model=InteresseResposta, status_code=status.HTTP_201_CREATED)
def enviar_interesse(
    dados: InteresseCriar,
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    _exigir_empresa_aprovada(empresa)

    candidato = sessao.query(Candidato).filter(Candidato.id == dados.candidato_id).first()
    if candidato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

    if dados.vaga_id is not None:
        vaga = sessao.query(Vaga).filter(Vaga.id == dados.vaga_id, Vaga.empresa_id == empresa.id).first()
        if vaga is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    interesse = Interesse(
        empresa_id=empresa.id,
        candidato_id=dados.candidato_id,
        vaga_id=dados.vaga_id,
        mensagem=dados.mensagem,
    )
    sessao.add(interesse)
    sessao.commit()
    sessao.refresh(interesse)
    return interesse


@roteador.get("/me/interesses", response_model=list[InteresseResposta])
def listar_meus_interesses(
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    empresa = _obter_empresa_do_usuario(usuario, sessao)
    return sessao.query(Interesse).filter(Interesse.empresa_id == empresa.id).all()


@roteador.get("/me/cota", response_model=CotaResposta)
def obter_minha_cota(
    usuario: Usuario = Depends(exigir_empresa),
    sessao: Session = Depends(obter_sessao),
):
    """Cota = quantos interesses 'aceitos' a empresa já teve frente à meta que ela mesma definiu (meta_cota)."""
    empresa = _obter_empresa_do_usuario(usuario, sessao)

    aceitos = (
        sessao.query(Interesse)
        .filter(Interesse.empresa_id == empresa.id, Interesse.status == StatusInteresseEnum.aceito)
        .count()
    )

    percentual = 0.0
    if empresa.meta_cota > 0:
        percentual = min(100.0, round(aceitos / empresa.meta_cota * 100, 1))

    return CotaResposta(meta_cota=empresa.meta_cota, aceitos=aceitos, percentual=percentual)
