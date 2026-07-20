# Interesse.py - Tabela que liga empresa ao candidato quando há interesse

from sqlalchemy import Column, Integer, Text, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base
import enum


class StatusInteresseEnum(str, enum.Enum):
    pendente = "pendente"
    visualizado = "visualizado"
    aceito = "aceito"
    recusado = "recusado"


class Interesse(Base):
    __tablename__ = "interesses"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=False)
    vaga_id = Column(Integer, ForeignKey("vagas.id"), nullable=True)
    mensagem = Column(Text)
    status = Column(Enum(StatusInteresseEnum), default=StatusInteresseEnum.pendente)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos
    empresa = relationship("Empresa", back_populates="interesses_enviados")
    candidato = relationship("Candidato", back_populates="interesses_recebidos")
    vaga = relationship("Vaga", back_populates="interesses")