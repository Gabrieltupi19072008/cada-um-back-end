# Habilidade.py - Tabela de habilidades do candidato

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from banco import Base


class Habilidade(Base):
    __tablename__ = "habilidades"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    nivel = Column(String(20), default="basico")

    # Relacionamento
    candidato = relationship("Candidato", back_populates="habilidades")