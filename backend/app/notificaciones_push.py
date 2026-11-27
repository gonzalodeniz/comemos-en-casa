"""Envía recordatorios mediante el protocolo Web Push."""
import json
import os
from datetime import date

import requests
from pywebpush import webpush

# Limita la entrega tardía si el dispositivo no está disponible de inmediato.
VIGENCIA_PUSH_SEGUNDOS = 15 * 60


class SesionSinRedirecciones(requests.Session):
    """Impide que un servicio push redirija la petición a otro destino."""
    def post(self, url, **kwargs):
        """Envía la petición sin seguir redirecciones."""
        kwargs["allow_redirects"] = False
        return super().post(url, **kwargs)


def enviar_push(endpoint: str, p256dh: str, auth: str, titulo: str, mensaje: str) -> None:
    """Cifra y entrega una notificación al servicio del navegador."""
    clave = os.environ["PUSH_PRIVATE_KEY"]
    contacto = os.environ["PUSH_CONTACT"]
    datos = json.dumps({"titulo": titulo, "mensaje": mensaje}, ensure_ascii=False)
    with SesionSinRedirecciones() as sesion:
        webpush(subscription_info={"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}, data=datos, vapid_private_key=clave, vapid_claims={"sub": contacto}, timeout=10, ttl=VIGENCIA_PUSH_SEGUNDOS, requests_session=sesion)


def enviar_recordatorio_push(endpoint: str, p256dh: str, auth: str, mensaje: str, comida: str, fecha: date) -> None:
    """Prepara el contenido de un recordatorio de comida para Web Push."""
    enviar_push(endpoint, p256dh, auth, "Recordatorio de comida", f"{mensaje}\n{comida} · {fecha.isoformat()}")
