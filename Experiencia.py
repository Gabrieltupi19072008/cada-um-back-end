# Experiencia.py - Tabela de experiências profissionais do candidato

from sqlalchemy import Column, Integer, String, Boolean, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from banco import Base


class Experiencia(Base):
    __tablename__ = "experiencias"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=False)
    empresa = Column(String(150), nullable=False)
    cargo = Column(String(150), nullable=False)
    descricao = Column(Text)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    emprego_atual = Column(Boolean, default=False)

    # Relacionamento
    candidato = relationship("Candidato", back_populates="experiencias")