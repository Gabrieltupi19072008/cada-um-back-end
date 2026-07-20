# Candidato.py - Tabela dos candidatos com TEA

from sqlalchemy import Column, Integer, String, Boolean, Text, Date, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base
import enum

class GrauTeaEnum(str, enum.Enum):
    leve = "leve"
    moderado = "moderado"
    severo = "severo"


class Candidato(Base):
    __tablename__ = "candidatos"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    cpf = Column(String(14), unique=True)
    data_nascimento = Column(Date)
    cidade = Column(String(100))
    estado = Column(String(2))
    telefone = Column(String(20))
    linkedin = Column(String(200))
    sobre_mim = Column(Text)
    grau_tea = Column(Enum(GrauTeaEnum))
    necessidades_especiais = Column(Text)
    foto_url = Column(String(255))
    aprovado = Column(Boolean, default=False)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="candidato")
    formacoes = relationship("Formacao", back_populates="candidato", cascade="all, delete")
    experiencias = relationship("Experiencia", back_populates="candidato", cascade="all, delete")
    habilidades = relationship("Habilidade", back_populates="candidato", cascade="all, delete")
    interesses_recebidos = relationship("Interesse", back_populates="candidato", cascade="all, delete")