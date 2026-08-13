# notificacoes.py - Envio de e-mail transacional (Resend). Nunca deve quebrar o fluxo
# principal do usuario: se a chave nao estiver configurada ou o envio falhar, so' loga.

import logging
import os

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificacoes")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if not RESEND_API_KEY:
        logger.info("RESEND_API_KEY não configurada — e-mail não enviado (assunto: %s)", assunto)
        return

    try:
        resend.Emails.send(
            {
                "from": "CadaUm <contato@cadaum.com>",
                "to": [destinatario],
                "subject": assunto,
                "html": corpo_html,
            }
        )
    except Exception:
        logger.exception("Falha ao enviar e-mail pra %s", destinatario)
