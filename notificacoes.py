# notificacoes.py - Envio de e-mail transacional (Resend). Nunca deve quebrar o fluxo
# principal do usuario: se a chave nao estiver configurada ou o envio falhar, so' loga.

import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturoExpirado

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificacoes")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# O SDK resend==2.5.1 não expõe timeout por chamada (usa `requests` internamente sem
# configurar um limite). Um endpoint travado do Resend poderia travar a thread do worker
# do FastAPI indefinidamente. Executamos a chamada num executor à parte e aplicamos um
# timeout de parede aqui — se estourar, loga e segue, sem travar o request.
_executor_email = ThreadPoolExecutor(max_workers=4, thread_name_prefix="enviar_email")


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if not RESEND_API_KEY:
        logger.info("RESEND_API_KEY não configurada — e-mail não enviado (assunto: %s)", assunto)
        return

    def _enviar():
        resend.Emails.send(
            {
                "from": "CadaUm <contato@cadaum.com>",
                "to": [destinatario],
                "subject": assunto,
                "html": corpo_html,
            }
        )

    try:
        futuro = _executor_email.submit(_enviar)
        futuro.result(timeout=8)
    except FuturoExpirado:
        logger.error("Timeout ao enviar e-mail pra %s (assunto: %s)", destinatario, assunto)
    except Exception:
        logger.exception("Falha ao enviar e-mail pra %s", destinatario)
