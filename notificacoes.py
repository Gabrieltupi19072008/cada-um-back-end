# notificacoes.py - Envio de e-mail transacional.
#
# Provedor principal: Brevo, via API HTTPS (nao SMTP). O Render (e varios outros PaaS
# gratuitos) bloqueia conexoes de saida em portas de SMTP (25/465/587) pra evitar abuso --
# confirmado em producao (erro "Network is unreachable" tentando Gmail SMTP nas portas 465 e
# 587). A API do Brevo roda sobre HTTPS normal (porta 443), que nunca e' bloqueada. O Brevo
# tambem permite verificar um UNICO endereco de e-mail remetente (em vez de exigir um dominio
# proprio verificado via DNS, como o Resend exige) -- por isso da' pra usar um Gmail comum como
# remetente.
#
# Gmail SMTP e Resend continuam disponiveis como fallback (uteis fora do Render, ou se o Brevo
# nao estiver configurado), mas SMTP direto NAO funciona nesse hosting -- ver acima.
#
# Nunca deve quebrar o fluxo principal do usuario: se nada estiver configurado ou o envio
# falhar, so' loga.

import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("notificacoes")

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_REMETENTE_EMAIL = os.getenv("BREVO_REMETENTE_EMAIL", "")
BREVO_REMETENTE_NOME = os.getenv("BREVO_REMETENTE_NOME", "CadaUm")

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# O envio roda num executor a parte e a chamada NAO espera o resultado (fire-and-forget):
# a latencia de um provedor de e-mail (ou de uma porta SMTP lenta/bloqueada) nunca deve virar
# latencia da requisicao HTTP do usuario. Os proprios timeouts do smtplib/socket (abaixo)
# limitam quanto tempo a thread de fundo fica presa numa tentativa.
_executor_email = ThreadPoolExecutor(max_workers=4, thread_name_prefix="enviar_email")


def _enviar_via_brevo(destinatario: str, assunto: str, corpo_html: str) -> None:
    resposta = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "sender": {"name": BREVO_REMETENTE_NOME, "email": BREVO_REMETENTE_EMAIL},
            "to": [{"email": destinatario}],
            "subject": assunto,
            "htmlContent": corpo_html,
        },
        timeout=8,
    )
    resposta.raise_for_status()


def _montar_mensagem_gmail(destinatario: str, assunto: str, corpo_html: str) -> MIMEMultipart:
    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = assunto
    mensagem["From"] = f"CadaUm <{GMAIL_USER}>"
    mensagem["To"] = destinatario
    mensagem.attach(MIMEText(corpo_html, "html"))
    return mensagem


def _enviar_via_gmail(destinatario: str, assunto: str, corpo_html: str) -> None:
    mensagem = _montar_mensagem_gmail(destinatario, assunto, corpo_html)
    # Algumas redes de hospedagem bloqueiam a porta 465 (SSL implicito) mas liberam a 587
    # (STARTTLS) ou vice-versa -- tenta as duas antes de desistir.
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as servidor:
            servidor.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            servidor.sendmail(GMAIL_USER, [destinatario], mensagem.as_string())
        return
    except (TimeoutError, OSError):
        logger.warning("Porta 465 falhou/travou pro Gmail, tentando porta 587 (STARTTLS)")

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=8) as servidor:
        servidor.starttls()
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


def _registrar_resultado(destinatario: str, assunto: str, futuro) -> None:
    erro = futuro.exception()
    if erro is not None:
        logger.error("Falha ao enviar e-mail pra %s (assunto: %s): %s", destinatario, assunto, erro)
    else:
        logger.info("E-mail enviado com sucesso pra %s (assunto: %s)", destinatario, assunto)


def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> None:
    if BREVO_API_KEY and BREVO_REMETENTE_EMAIL:
        _enviar = lambda: _enviar_via_brevo(destinatario, assunto, corpo_html)
    elif GMAIL_USER and GMAIL_APP_PASSWORD:
        _enviar = lambda: _enviar_via_gmail(destinatario, assunto, corpo_html)
    elif RESEND_API_KEY:
        _enviar = lambda: _enviar_via_resend(destinatario, assunto, corpo_html)
    else:
        logger.info("Nenhum provedor de e-mail configurado — e-mail não enviado (assunto: %s)", assunto)
        return

    futuro = _executor_email.submit(_enviar)
    futuro.add_done_callback(lambda f: _registrar_resultado(destinatario, assunto, f))
