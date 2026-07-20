# schemas.py - Modelos Pydantic usados nas rotas (entrada e saída de dados)

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

from Candidato import GrauTeaEnum
from Vaga import ModalidadeEnum, ContratoEnum
from Interesses import StatusInteresseEnum
from Usuario import PerfilEnum


class CandidatoCadastro(BaseModel):
    nome: str
    email: str
    senha: str
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, max_length=2)
    telefone: Optional[str] = None


class EmpresaCadastro(BaseModel):
    nome: str
    email: str
    senha: str
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, max_length=2)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: str


class EsqueciSenhaEntrada(BaseModel):
    email: str


class EsqueciSenhaResposta(BaseModel):
    encontrado: bool
    senha_temporaria: Optional[str] = None


class UsuarioResumo(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool

    model_config = {"from_attributes": True}


class CandidatoAtualizar(BaseModel):
    data_nascimento: Optional[date] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, max_length=2)
    telefone: Optional[str] = None
    linkedin: Optional[str] = None
    sobre_mim: Optional[str] = None
    grau_tea: Optional[GrauTeaEnum] = None
    necessidades_especiais: Optional[str] = None
    foto_url: Optional[str] = None


class FormacaoCriar(BaseModel):
    instituicao: str
    curso: str
    nivel: str
    ano_inicio: Optional[int] = None
    ano_conclusao: Optional[int] = None
    em_andamento: bool = False


class FormacaoResposta(BaseModel):
    id: int
    instituicao: str
    curso: str
    nivel: str
    ano_inicio: Optional[int] = None
    ano_conclusao: Optional[int] = None
    em_andamento: bool

    model_config = {"from_attributes": True}


class ExperienciaCriar(BaseModel):
    empresa: str
    cargo: str
    descricao: Optional[str] = None
    data_inicio: date
    data_fim: Optional[date] = None
    emprego_atual: bool = False


class ExperienciaResposta(BaseModel):
    id: int
    empresa: str
    cargo: str
    descricao: Optional[str] = None
    data_inicio: date
    data_fim: Optional[date] = None
    emprego_atual: bool

    model_config = {"from_attributes": True}


class HabilidadeCriar(BaseModel):
    nome: str
    nivel: str = "basico"


class HabilidadeResposta(BaseModel):
    id: int
    nome: str
    nivel: str

    model_config = {"from_attributes": True}


class CandidatoPerfil(BaseModel):
    id: int
    usuario: UsuarioResumo
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    telefone: Optional[str] = None
    linkedin: Optional[str] = None
    sobre_mim: Optional[str] = None
    grau_tea: Optional[GrauTeaEnum] = None
    necessidades_especiais: Optional[str] = None
    foto_url: Optional[str] = None
    formacoes: list[FormacaoResposta] = []
    experiencias: list[ExperienciaResposta] = []
    habilidades: list[HabilidadeResposta] = []

    model_config = {"from_attributes": True}


class CandidatoPublico(BaseModel):
    """Perfil do candidato como a empresa enxerga (sem CPF)."""

    id: int
    usuario: UsuarioResumo
    cidade: Optional[str] = None
    estado: Optional[str] = None
    linkedin: Optional[str] = None
    sobre_mim: Optional[str] = None
    grau_tea: Optional[GrauTeaEnum] = None
    necessidades_especiais: Optional[str] = None
    foto_url: Optional[str] = None
    formacoes: list[FormacaoResposta] = []
    experiencias: list[ExperienciaResposta] = []
    habilidades: list[HabilidadeResposta] = []

    model_config = {"from_attributes": True}


class EmpresaAtualizar(BaseModel):
    razao_social: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = Field(default=None, max_length=2)
    site: Optional[str] = None
    descricao: Optional[str] = None


class EmpresaPerfil(BaseModel):
    id: int
    usuario: UsuarioResumo
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    site: Optional[str] = None
    descricao: Optional[str] = None
    meta_cota: int
    aprovada: bool

    model_config = {"from_attributes": True}


class VagaCriar(BaseModel):
    titulo: str
    area: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    modalidade: ModalidadeEnum = ModalidadeEnum.presencial
    tipo_contrato: ContratoEnum = ContratoEnum.clt
    salario: Optional[float] = None
    descricao: Optional[str] = None
    adaptacoes: Optional[str] = None
    ativa: bool = True


class VagaResposta(BaseModel):
    id: int
    titulo: str
    area: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    modalidade: ModalidadeEnum
    tipo_contrato: ContratoEnum
    salario: Optional[float] = None
    descricao: Optional[str] = None
    adaptacoes: Optional[str] = None
    ativa: bool

    model_config = {"from_attributes": True}


class InteresseCriar(BaseModel):
    candidato_id: int
    vaga_id: Optional[int] = None
    mensagem: Optional[str] = None


class InteresseResposta(BaseModel):
    id: int
    candidato: CandidatoPublico
    vaga_id: Optional[int] = None
    mensagem: Optional[str] = None
    status: StatusInteresseEnum

    model_config = {"from_attributes": True}


class EmpresaResumo(BaseModel):
    id: int
    usuario: UsuarioResumo
    razao_social: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None

    model_config = {"from_attributes": True}


class VagaResumo(BaseModel):
    id: int
    titulo: str
    area: Optional[str] = None
    modalidade: ModalidadeEnum
    tipo_contrato: ContratoEnum

    model_config = {"from_attributes": True}


class InteresseParaCandidato(BaseModel):
    id: int
    empresa: EmpresaResumo
    vaga: Optional[VagaResumo] = None
    mensagem: Optional[str] = None
    status: StatusInteresseEnum

    model_config = {"from_attributes": True}


class InteresseResponder(BaseModel):
    status: StatusInteresseEnum


class UsuarioAdmin(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilEnum
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class EmpresaAdmin(BaseModel):
    id: int
    usuario: UsuarioResumo
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    setor: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    aprovada: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class CandidatoAdmin(BaseModel):
    id: int
    usuario: UsuarioResumo
    cidade: Optional[str] = None
    estado: Optional[str] = None
    grau_tea: Optional[GrauTeaEnum] = None
    aprovado: bool
    criado_em: datetime

    model_config = {"from_attributes": True}


class CotaResposta(BaseModel):
    meta_cota: int
    aceitos: int
    percentual: float


class CotaEmpresa(BaseModel):
    empresa_id: int
    razao_social: Optional[str] = None
    meta_cota: int
    aceitos: int
    percentual: float


class EstatisticasAdmin(BaseModel):
    total_candidatos: int
    total_empresas: int
    cota_media: float
    aprovacoes_pendentes: int


class VagaComEmpresa(BaseModel):
    id: int
    titulo: str
    area: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    modalidade: ModalidadeEnum
    tipo_contrato: ContratoEnum
    salario: Optional[float] = None
    descricao: Optional[str] = None
    adaptacoes: Optional[str] = None
    empresa: EmpresaResumo

    model_config = {"from_attributes": True}
