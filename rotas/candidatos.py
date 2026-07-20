# candidatos.py - Rotas de perfil do candidato (dados, formação, experiência, habilidades)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from typing import Optional

from banco import obter_sessao
from Usuario import Usuario
from Candidato import Candidato
from Formacao import Formacao
from Experiencia import Experiencia
from Habilidade import Habilidade
from Interesses import Interesse, StatusInteresseEnum
from Vaga import Vaga, ModalidadeEnum
from Empresa import Empresa
from dependencias import exigir_candidato
from schemas import (
    CandidatoAtualizar,
    CandidatoPerfil,
    FormacaoCriar,
    FormacaoResposta,
    ExperienciaCriar,
    ExperienciaResposta,
    HabilidadeCriar,
    HabilidadeResposta,
    InteresseParaCandidato,
    InteresseResponder,
    VagaComEmpresa,
)

roteador = APIRouter(prefix="/candidatos", tags=["Candidatos"])


def _obter_candidato_do_usuario(usuario: Usuario, sessao: Session) -> Candidato:
    candidato = sessao.query(Candidato).filter(Candidato.usuario_id == usuario.id).first()
    if candidato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de candidato não encontrado")
    return candidato


@roteador.get("/me", response_model=CandidatoPerfil)
def obter_meu_perfil(
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    return _obter_candidato_do_usuario(usuario, sessao)


@roteador.put("/me", response_model=CandidatoPerfil)
def atualizar_meu_perfil(
    dados: CandidatoAtualizar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(candidato, campo, valor)

    sessao.commit()
    sessao.refresh(candidato)
    return candidato


@roteador.post("/me/formacoes", response_model=FormacaoResposta, status_code=status.HTTP_201_CREATED)
def adicionar_formacao(
    dados: FormacaoCriar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)

    formacao = Formacao(candidato_id=candidato.id, **dados.model_dump())
    sessao.add(formacao)
    sessao.commit()
    sessao.refresh(formacao)
    return formacao


@roteador.put("/me/formacoes/{formacao_id}", response_model=FormacaoResposta)
def atualizar_formacao(
    formacao_id: int,
    dados: FormacaoCriar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    formacao = (
        sessao.query(Formacao)
        .filter(Formacao.id == formacao_id, Formacao.candidato_id == candidato.id)
        .first()
    )
    if formacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formação não encontrada")

    for campo, valor in dados.model_dump().items():
        setattr(formacao, campo, valor)

    sessao.commit()
    sessao.refresh(formacao)
    return formacao


@roteador.delete("/me/formacoes/{formacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_formacao(
    formacao_id: int,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    formacao = (
        sessao.query(Formacao)
        .filter(Formacao.id == formacao_id, Formacao.candidato_id == candidato.id)
        .first()
    )
    if formacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formação não encontrada")

    sessao.delete(formacao)
    sessao.commit()


@roteador.post("/me/experiencias", response_model=ExperienciaResposta, status_code=status.HTTP_201_CREATED)
def adicionar_experiencia(
    dados: ExperienciaCriar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)

    experiencia = Experiencia(candidato_id=candidato.id, **dados.model_dump())
    sessao.add(experiencia)
    sessao.commit()
    sessao.refresh(experiencia)
    return experiencia


@roteador.put("/me/experiencias/{experiencia_id}", response_model=ExperienciaResposta)
def atualizar_experiencia(
    experiencia_id: int,
    dados: ExperienciaCriar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    experiencia = (
        sessao.query(Experiencia)
        .filter(Experiencia.id == experiencia_id, Experiencia.candidato_id == candidato.id)
        .first()
    )
    if experiencia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiência não encontrada")

    for campo, valor in dados.model_dump().items():
        setattr(experiencia, campo, valor)

    sessao.commit()
    sessao.refresh(experiencia)
    return experiencia


@roteador.delete("/me/experiencias/{experiencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_experiencia(
    experiencia_id: int,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    experiencia = (
        sessao.query(Experiencia)
        .filter(Experiencia.id == experiencia_id, Experiencia.candidato_id == candidato.id)
        .first()
    )
    if experiencia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiência não encontrada")

    sessao.delete(experiencia)
    sessao.commit()


@roteador.post("/me/habilidades", response_model=HabilidadeResposta, status_code=status.HTTP_201_CREATED)
def adicionar_habilidade(
    dados: HabilidadeCriar,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)

    habilidade = Habilidade(candidato_id=candidato.id, **dados.model_dump())
    sessao.add(habilidade)
    sessao.commit()
    sessao.refresh(habilidade)
    return habilidade


@roteador.delete("/me/habilidades/{habilidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_habilidade(
    habilidade_id: int,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    habilidade = (
        sessao.query(Habilidade)
        .filter(Habilidade.id == habilidade_id, Habilidade.candidato_id == candidato.id)
        .first()
    )
    if habilidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habilidade não encontrada")

    sessao.delete(habilidade)
    sessao.commit()


@roteador.get("/me/interesses", response_model=list[InteresseParaCandidato])
def listar_meus_interesses(
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    interesses = sessao.query(Interesse).filter(Interesse.candidato_id == candidato.id).all()

    # Marca como "visualizado" os interesses que ainda estavam pendentes
    houve_alteracao = False
    for interesse in interesses:
        if interesse.status == StatusInteresseEnum.pendente:
            interesse.status = StatusInteresseEnum.visualizado
            houve_alteracao = True
    if houve_alteracao:
        sessao.commit()

    return interesses


@roteador.put("/me/interesses/{interesse_id}", response_model=InteresseParaCandidato)
def responder_interesse(
    interesse_id: int,
    dados: InteresseResponder,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    candidato = _obter_candidato_do_usuario(usuario, sessao)
    interesse = (
        sessao.query(Interesse)
        .filter(Interesse.id == interesse_id, Interesse.candidato_id == candidato.id)
        .first()
    )
    if interesse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interesse não encontrado")

    if dados.status not in (StatusInteresseEnum.aceito, StatusInteresseEnum.recusado):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resposta deve ser 'aceito' ou 'recusado'",
        )

    if interesse.status in (StatusInteresseEnum.aceito, StatusInteresseEnum.recusado):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este interesse já foi respondido")

    interesse.status = dados.status
    sessao.commit()
    sessao.refresh(interesse)
    return interesse


@roteador.get("/vagas", response_model=list[VagaComEmpresa])
def listar_vagas_disponiveis(
    cidade: Optional[str] = None,
    modalidade: Optional[ModalidadeEnum] = None,
    usuario: Usuario = Depends(exigir_candidato),
    sessao: Session = Depends(obter_sessao),
):
    consulta = (
        sessao.query(Vaga)
        .join(Vaga.empresa)
        .filter(Vaga.ativa.is_(True), Empresa.aprovada.is_(True))
    )
    if cidade:
        consulta = consulta.filter(Vaga.cidade == cidade)
    if modalidade:
        consulta = consulta.filter(Vaga.modalidade == modalidade)

    return consulta.all()
