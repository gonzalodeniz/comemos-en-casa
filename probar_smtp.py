#!/usr/bin/env python3
"""Envía un correo de prueba con los parámetros SMTP del .env del proyecto."""

import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


def cargar_env(ruta: Path) -> None:
    """Carga variables sencillas de .env sin mostrar sus valores sensibles."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el fichero {ruta}")
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("export "):
            linea = linea[7:].lstrip()
        clave, separador, valor = linea.partition("=")
        if not separador or not clave.strip():
            continue
        clave = clave.strip()
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in {"'", '"'}:
            valor = valor[1:-1]
        os.environ.setdefault(clave, valor)


def crear_parser() -> argparse.ArgumentParser:
    """Define el destino obligatorio y la ruta opcional al fichero .env."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destinatario", help="Única dirección que recibirá el mensaje de prueba")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).resolve().parent / ".env", help="Ruta al .env (por defecto, el de la raíz del proyecto)")
    return parser


def main() -> int:
    """Envía un único mensaje de prueba y comunica el resultado sin revelar secretos."""
    args = crear_parser().parse_args()
    try:
        cargar_env(args.env_file)
        host = os.getenv("EMAIL_SMTP_HOST", "").strip()
        sender = os.getenv("EMAIL_FROM", "").strip()
        if not host or not sender:
            raise ValueError("EMAIL_SMTP_HOST y EMAIL_FROM deben estar definidos en .env")
        try:
            port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        except ValueError as error:
            raise ValueError("EMAIL_SMTP_PORT debe ser un número entero") from error

        mensaje = EmailMessage()
        mensaje["Subject"] = "Prueba de correo SMTP — Comemos en casa"
        mensaje["From"] = sender
        mensaje["To"] = args.destinatario
        mensaje.set_content("Este es un correo de prueba para comprobar la configuración SMTP de Comemos en casa.")

        with smtplib.SMTP(host, port, timeout=15) as cliente:
            starttls = os.getenv("EMAIL_SMTP_STARTTLS", "true").strip().lower()
            if starttls not in {"0", "false", "no"}:
                cliente.starttls(context=ssl.create_default_context())
            usuario = os.getenv("EMAIL_SMTP_USERNAME", "")
            contrasena = os.getenv("EMAIL_SMTP_PASSWORD", "")
            if usuario:
                if not contrasena:
                    raise ValueError("EMAIL_SMTP_PASSWORD es obligatorio si se configura EMAIL_SMTP_USERNAME")
                cliente.login(usuario, contrasena)
            cliente.send_message(mensaje)
        print(f"Correo aceptado por el servidor SMTP y enviado a {args.destinatario}.")
        return 0
    except (OSError, ValueError, smtplib.SMTPException) as error:
        print(f"Error al enviar el correo SMTP: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
