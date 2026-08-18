# notificacoes.py - Envio de e-mail transacional (Gmail SMTP, com Resend como alternativa).
# Nunca deve quebrar o fluxo principal do usuario: se nada estiver configurado ou o envio
# falhar, so' loga.

import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturoExpirado
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificacoes")

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Nem o smtplib nem o SDK do Resend expõem um jeito confiável de garantir que a chamada
# nunca trave a thread do worker do FastAPI indefinidamente. Executamos o envio num executor
# à parte e aplicamos um timeout de parede aqui — se estourar, loga e segue, sem travar o request.
_executor_email = ThreadPoolExecutor(max_workers=4, thread_name_prefix="enviar_email")


def _enviar_via_gmail(destinatario: str, assunto: str, corpo_html: str) -> None:
    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = assunto
    mensagem["From"] = f"CadaUm <{GMAIL_USER}>"
    mensagem["To"] = destinatario
    mensagem.attach(MIMEText(corpo_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as servidor:
        servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        servidor.sendmail(GMAIL_USER, [destinatario], mensagem.as_string())


def _enviar_via_resend(destinatario: str, assunto: str, corpo_html: str) -> None:
    resend.Emails.send(
        {
            "from": "CadaUm <contato@cadaum.com>",
            "to": [destinatario],
            "subject": assunto,
            "html": corpo_html,
        }
    )


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        _enviar = lambda: _enviar_via_gmail(destinatario, assunto, corpo_html)
    elif RESEND_API_KEY:
        _enviar = lambda: _enviar_via_resend(destinatario, assunto, corpo_html)
    else:
        logger.info("Nenhum provedor de e-mail configurado — e-mail não enviado (assunto: %s)", assunto)
        return

    try:
        futuro = _executor_email.submit(_enviar)
        futuro.result(timeout=8)
    except FuturoExpirado:
        logger.error("Timeout ao enviar e-mail pra %s (assunto: %s)", destinatario, assunto)
    except Exception:
        logger.exception("Falha ao enviar e-mail pra %s", destinatario)
