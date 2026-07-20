from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base
import enum

# Define os perfis possíveis
class PerfilEnum(str, enum.Enum):
    candidato = "candidato"
    empresa = "empresa"
    admin = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"  # nome da tabela no MySQL

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilEnum), nullable=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos com outras tabelas
    candidato = relationship("Candidato", back_populates="usuario", uselist=False)
    empresa = relationship("Empresa", back_populates="usuario", uselist=False)