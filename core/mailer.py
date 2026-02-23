import logging
import smtplib
from email.message import EmailMessage
import keyring

log = logging.getLogger("mailer")

SERVICE_NAME = "GASMonitorSMTP"

def save_smtp_secret(username: str, password: str):
    keyring.set_password(SERVICE_NAME, username, password)

def load_smtp_secret(username: str):
    try:
        return keyring.get_password(SERVICE_NAME, username)
    except Exception:
        return None

def send_email(host: str, port: int, username: str, password: str,
               use_tls: bool, sender: str, recipient: str,
               subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    log.info("Sending email to %s via %s:%s", recipient, host, port)
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.ehlo()
        if use_tls:
            s.starttls()
            s.ehlo()
        if username:
            s.login(username, password)
        s.send_message(msg)
