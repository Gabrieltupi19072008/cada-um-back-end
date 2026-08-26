# Interesse.py - Tabela que liga empresa ao candidato quando há interesse

from sqlalchemy import Column, Integer, Text, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from banco import Base
import enum


class StatusInteresseEnum(str, enum.Enum):
    pendente = "pendente"
    visualizado = "visualizado"
    selecionado = "selecionado"
    aceito = "aceito"
    recusado = "recusado"


class OrigemInteresseEnum(str, enum.Enum):
    empresa = "empresa"
    candidato = "candidato"


# Transicoes de status validas ao "responder" um interesse/candidatura -- compartilhada
# pelas rotas de empresa e de candidato, que espelham a mesma logica de decisao.
# Chave = status pra onde se quer ir; valor = de quais status atuais isso e' permitido.
TRANSICOES_STATUS_VALIDAS = {
    StatusInteresseEnum.selecionado: (StatusInteresseEnum.pendente, StatusInteresseEnum.visualizado),
    StatusInteresseEnum.aceito: (StatusInteresseEnum.selecionado,),
    StatusInteresseEnum.recusado: (
        StatusInteresseEnum.pendente,
        StatusInteresseEnum.visualizado,
        StatusInteresseEnum.selecionado,
    ),
}


class Interesse(Base):
    __tablename__ = "interesses"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    candidato_id = Column(Integer, ForeignKey("candidatos.id"), nullable=False)
    vaga_id = Column(Integer, ForeignKey("vagas.id"), nullable=True)
    mensagem = Column(Text)
    status = Column(Enum(StatusInteresseEnum), default=StatusInteresseEnum.pendente)
    origem = Column(
        Enum(OrigemInteresseEnum), default=OrigemInteresseEnum.empresa, nullable=False
    )  # "empresa" ou "candidato" — coluna física é VARCHAR(20), sem enum nativo no Postgres
    criado_em = Column(TIMESTAMP, server_default=func.now())

    # Relacionamentos
    empresa = relationship("Empresa", back_populates="interesses_enviados")
    candidato = relationship("Candidato", back_populates="interesses_recebidos")
    vaga = relationship("Vaga", back_populates="interesses")
    mensagens = relationship("MensagemChat", back_populates="interesse", cascade="all, delete")


class MensagemChat(Base):
    __tablename__ = "mensagens_chat"

    id = Column(Integer, primary_key=True, index=True)
    interesse_id = Column(Integer, ForeignKey("interesses.id"), nullable=False)
    remetente_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    corpo = Column(Text, nullable=False)
    criado_em = Column(TIMESTAMP, server_default=func.now())

    interesse = relationship("Interesse", back_populates="mensagens")
    remetente = relationship("Usuario")