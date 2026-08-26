# mensagens.py - Chat simples ligado a um Interesse (empresa <-> candidato), liberado
# só enquanto o status estiver "selecionado". Rota generica -- nao exige perfil
# especifico, ja que tanto a empresa quanto o candidato de um Interesse precisam
# ler/mandar mensagem nele.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from banco import obter_sessao
from Usuario import Usuario
from Interesses import Interesse, MensagemChat, StatusInteresseEnum
from dependencias import obter_usuario_atual
from notificacoes import enviar_email
from schemas import MensagemCriar, MensagemResposta

roteador = APIRouter(prefix="/interesses", tags=["Mensagens"])


def _obter_interesse_do_usuario(interesse_id: int, usuario: Usuario, sessao: Session) -> Interesse:
    interesse = sessao.query(Interesse).filter(Interesse.id == interesse_id).first()
    if interesse is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interesse não encontrado")

    e_a_empresa = interesse.empresa.usuario_id == usuario.id
    e_o_candidato = interesse.candidato.usuario_id == usuario.id
    if not e_a_empresa and not e_o_candidato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interesse não encontrado")

    return interesse


def _montar_resposta(mensagem: MensagemChat, usuario_atual: Usuario) -> MensagemResposta:
    remetente = mensagem.remetente
    return MensagemResposta(
        id=mensagem.id,
        corpo=mensagem.corpo,
        criado_em=mensagem.criado_em,
        remetente_nome=remetente.nome,
        remetente_foto_url=remetente.foto_url,
        de_mim=remetente.id == usuario_atual.id,
    )


@roteador.get("/{interesse_id}/mensagens", response_model=list[MensagemResposta])
def listar_mensagens(
    interesse_id: int,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    interesse = _obter_interesse_do_usuario(interesse_id, usuario, sessao)
    mensagens = (
        sessao.query(MensagemChat)
        .filter(MensagemChat.interesse_id == interesse.id)
        .order_by(MensagemChat.criado_em.asc())
        .all()
    )
    return [_montar_resposta(mensagem, usuario) for mensagem in mensagens]


@roteador.post("/{interesse_id}/mensagens", response_model=MensagemResposta, status_code=status.HTTP_201_CREATED)
def enviar_mensagem(
    interesse_id: int,
    dados: MensagemCriar,
    usuario: Usuario = Depends(obter_usuario_atual),
    sessao: Session = Depends(obter_sessao),
):
    interesse = _obter_interesse_do_usuario(interesse_id, usuario, sessao)

    if interesse.status != StatusInteresseEnum.selecionado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O chat só fica aberto enquanto a candidatura está 'selecionada'",
        )

    mensagem = MensagemChat(interesse_id=interesse.id, remetente_usuario_id=usuario.id, corpo=dados.corpo)
    sessao.add(mensagem)
    sessao.commit()
    sessao.refresh(mensagem)

    e_a_empresa = interesse.empresa.usuario_id == usuario.id
    destinatario = interesse.candidato.usuario if e_a_empresa else interesse.empresa.usuario
    enviar_email(
        destinatario=destinatario.email,
        assunto="Nova mensagem — CadaUm",
        corpo_html=(
            f"<p>Olá, {destinatario.nome.split(' ')[0]}!</p>"
            f"<p><b>{usuario.nome}</b> te mandou uma mensagem no CadaUm. Entre na plataforma pra ver e responder.</p>"
        ),
    )

    return _montar_resposta(mensagem, usuario)
