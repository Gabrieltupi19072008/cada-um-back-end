# Empresa.py - Tabela das empresas cadastradas na plataforma

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base


class Empresa(Base):
    __tablename__ = "empresas"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=False)
    cnpj = Column(String(18), unique=True)
    razao_social = Column(String(200))
    setor = Column(String(100))
    cidade = Column(String(100))
    estado = Column(String(2))
    site = Column(String(200))
    descricao = Column(Text)
    meta_cota = Column(Integer, default=0)
    aprovada = Column(Boolean, default=False)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="empresa")
    vagas = relationship("Vaga", back_populates="empresa", cascade="all, delete")
    interesses_enviados = relationship("Interesse", back_populates="empresa", cascade="all, delete")