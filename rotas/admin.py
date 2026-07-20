# admin.py - Rotas administrativas (aprovar empresas/candidatos, estatísticas, relatório de cota)

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario, PerfilEnum
from Empresa import Empresa
from Candidato import Candidato
from Interesses import Interesse, StatusInteresseEnum
from dependencias import exigir_admin
from schemas import (
    UsuarioAdmin,
    EmpresaAdmin,
    CandidatoAdmin,
    CotaEmpresa,
    EstatisticasAdmin,
)

roteador = APIRouter(prefix="/admin", tags=["Admin"])


def _calcular_cota(empresa: Empresa, sessao: Session) -> CotaEmpresa:
    aceitos = (
        sessao.query(Interesse)
        .filter(Interesse.empresa_id == empresa.id, Interesse.status == StatusInteresseEnum.aceito)
        .count()
    )
    percentual = 0.0
    if empresa.meta_cota > 0:
        percentual = min(100.0, round(aceitos / empresa.meta_cota * 100, 1))

    return CotaEmpresa(
        empresa_id=empresa.id,
        razao_social=empresa.razao_social,
        meta_cota=empresa.meta_cota,
        aceitos=aceitos,
        percentual=percentual,
    )


@roteador.get("/empresas", response_model=list[EmpresaAdmin])
def listar_empresas(
    aprovada: Optional[bool] = None,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    consulta = sessao.query(Empresa)
    if aprovada is not None:
        consulta = consulta.filter(Empresa.aprovada == aprovada)
    return consulta.all()


@roteador.put("/empresas/{empresa_id}/aprovar", response_model=EmpresaAdmin)
def aprovar_empresa(
    empresa_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    empresa = sessao.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    empresa.aprovada = True
    sessao.commit()
    sessao.refresh(empresa)
    return empresa


@roteador.put("/empresas/{empresa_id}/reprovar", response_model=EmpresaAdmin)
def reprovar_empresa(
    empresa_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    empresa = sessao.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada")

    empresa.aprovada = False
    sessao.commit()
    sessao.refresh(empresa)
    return empresa


@roteador.get("/usuarios", response_model=list[UsuarioAdmin])
def listar_usuarios(
    perfil: Optional[PerfilEnum] = None,
    ativo: Optional[bool] = None,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    consulta = sessao.query(Usuario)
    if perfil is not None:
        consulta = consulta.filter(Usuario.perfil == perfil)
    if ativo is not None:
        consulta = consulta.filter(Usuario.ativo == ativo)
    return consulta.all()


@roteador.put("/usuarios/{usuario_id}/desativar", response_model=UsuarioAdmin)
def desativar_usuario(
    usuario_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    if usuario_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Você não pode desativar a própria conta")

    usuario = sessao.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.ativo = False
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


@roteador.put("/usuarios/{usuario_id}/ativar", response_model=UsuarioAdmin)
def ativar_usuario(
    usuario_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    usuario = sessao.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.ativo = True
    sessao.commit()
    sessao.refresh(usuario)
    return usuario


@roteador.get("/candidatos", response_model=list[CandidatoAdmin])
def listar_candidatos(
    aprovado: Optional[bool] = None,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    consulta = sessao.query(Candidato)
    if aprovado is not None:
        consulta = consulta.filter(Candidato.aprovado == aprovado)
    return consulta.all()


@roteador.put("/candidatos/{candidato_id}/aprovar", response_model=CandidatoAdmin)
def aprovar_candidato(
    candidato_id: int,
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    candidato = sessao.query(Candidato).filter(Candidato.id == candidato_id).first()
    if candidato is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")

    candidato.aprovado = True
    sessao.commit()
    sessao.refresh(candidato)
    return candidato


@roteador.get("/relatorio-cota", response_model=list[CotaEmpresa])
def relatorio_cota(
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    empresas = sessao.query(Empresa).filter(Empresa.aprovada.is_(True)).all()
    return [_calcular_cota(empresa, sessao) for empresa in empresas]


@roteador.get("/relatorio-cota/exportar")
def exportar_relatorio_cota(
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    empresas = sessao.query(Empresa).filter(Empresa.aprovada.is_(True)).all()
    cotas = [_calcular_cota(empresa, sessao) for empresa in empresas]

    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(["empresa_id", "razao_social", "meta_cota", "aceitos", "percentual"])
    for cota in cotas:
        escritor.writerow([cota.empresa_id, cota.razao_social, cota.meta_cota, cota.aceitos, cota.percentual])
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_cota.csv"},
    )


@roteador.get("/estatisticas", response_model=EstatisticasAdmin)
def estatisticas(
    admin: Usuario = Depends(exigir_admin),
    sessao: Session = Depends(obter_sessao),
):
    total_candidatos = sessao.query(Candidato).count()
    total_empresas = sessao.query(Empresa).count()

    empresas_aprovadas = sessao.query(Empresa).filter(Empresa.aprovada.is_(True)).all()
    cotas = [_calcular_cota(empresa, sessao) for empresa in empresas_aprovadas]
    cota_media = round(sum(c.percentual for c in cotas) / len(cotas), 1) if cotas else 0.0

    empresas_pendentes = sessao.query(Empresa).filter(Empresa.aprovada.is_(False)).count()
    candidatos_pendentes = sessao.query(Candidato).filter(Candidato.aprovado.is_(False)).count()

    return EstatisticasAdmin(
        total_candidatos=total_candidatos,
        total_empresas=total_empresas,
        cota_media=cota_media,
        aprovacoes_pendentes=empresas_pendentes + candidatos_pendentes,
    )
