# Vaga.py - Tabela de vagas publicadas pelas empresas

from sqlalchemy import Column, Integer, String, Boolean, Text, DECIMAL, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base
import enum


class ModalidadeEnum(str, enum.Enum):
    presencial = "presencial"
    hibrido = "hibrido"
    remoto = "remoto"


class ContratoEnum(str, enum.Enum):
    clt = "clt"
    pj = "pj"
    estagio = "estagio"
    temporario = "temporario"


class Vaga(Base):
    __tablename__ = "vagas"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    titulo = Column(String(200), nullable=False)
    area = Column(String(100))
    cidade = Column(String(100))
    estado = Column(String(2))
    modalidade = Column(Enum(ModalidadeEnum), default=ModalidadeEnum.presencial)
    tipo_contrato = Column(Enum(ContratoEnum), default=ContratoEnum.clt)
    salario = Column(DECIMAL(10, 2))
    descricao = Column(Text)
    adaptacoes = Column(Text)
    ativa = Column(Boolean, default=True)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos
    empresa = relationship("Empresa", back_populates="vagas")
    interesses = relationship("Interesse", back_populates="vaga")