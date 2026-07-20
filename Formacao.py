# Formacao.py - Tabela de formações escolares do candidato

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from banco import Base


class Formacao(Base):
    __tablename__ = "formacoes"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=False)
    instituicao = Column(String(150), nullable=False)
    curso = Column(String(150), nullable=False)
    nivel = Column(String(50), nullable=False)
    ano_inicio = Column(Integer)
    ano_conclusao = Column(Integer)
    em_andamento = Column(Boolean, default=False)

    # Relacionamento
    candidato = relationship("Candidato", back_populates="formacoes")