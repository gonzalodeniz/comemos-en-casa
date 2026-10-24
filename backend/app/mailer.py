"""Envía mensajes de recuperación mediante SMTP.

Valida la configuración al enviar y admite TLS y autenticación opcionales; los errores quedan a cargo del llamador.
"""

import os
import smtplib
import ssl
from email.message import EmailMessage


def send_password_reset_email(recipient: str, reset_url: str) -> None:
    host = os.getenv("EMAIL_SMTP_HOST", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    if not host or not sender:
        raise RuntimeError("SMTP host and sender must be configured")

    try:
        port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    except ValueError as error:
        raise RuntimeError("SMTP port must be an integer") from error

    message = EmailMessage()
    message["Subject"] = "Password reset request"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "A password reset was requested for your account. "
        f"Use this link within 30 minutes: {reset_url}\n"
        "If you did not request this change, you can ignore this message."
    )

    with smtplib.SMTP(host, port, timeout=10) as client:
        if os.getenv("EMAIL_SMTP_STARTTLS", "true").lower() not in {"0", "false", "no"}:
            client.starttls(context=ssl.create_default_context())
        username = os.getenv("EMAIL_SMTP_USERNAME", "")
        password = os.getenv("EMAIL_SMTP_PASSWORD", "")
        if username:
            if not password:
                raise RuntimeError("SMTP password is required when a username is configured")
            client.login(username, password)
        client.send_message(message)
