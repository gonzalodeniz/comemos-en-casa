"""Comprueba la preparación del envío Web Push sin acceso a la red."""
import json
from datetime import date

from app import notificaciones_push


def test_envio_push_incluye_mensaje_comida_y_fecha(monkeypatch):
    """Entrega los datos cifrables y la identidad VAPID a la biblioteca."""
    monkeypatch.setenv("PUSH_PRIVATE_KEY", "clave-privada")
    monkeypatch.setenv("PUSH_CONTACT", "mailto:admin@example.test")
    enviados = []
    monkeypatch.setattr(notificaciones_push, "webpush", lambda **kwargs: enviados.append(kwargs))
    notificaciones_push.enviar_recordatorio_push("https://fcm.googleapis.com/fcm/send/uno", "clave", "secreto", "Sacar pollo", "Pollo", date(2026, 11, 2))
    assert enviados[0]["subscription_info"] == {"endpoint": "https://fcm.googleapis.com/fcm/send/uno", "keys": {"p256dh": "clave", "auth": "secreto"}}
    assert json.loads(enviados[0]["data"]) == {"titulo": "Recordatorio de comida", "mensaje": "Sacar pollo\nPollo · 2026-11-02"}
    assert enviados[0]["vapid_private_key"] == "clave-privada"
    assert enviados[0]["vapid_claims"] == {"sub": "mailto:admin@example.test"}


def test_envio_push_cifra_el_contenido_y_no_sigue_redirecciones(monkeypatch):
    """Comprueba el cifrado real sin transmitir la petición a un servicio remoto."""
    import base64
    import os
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    def codificar(valor):
        """Codifica datos binarios con el formato URL de las claves Web Push."""
        return base64.urlsafe_b64encode(valor).rstrip(b"=").decode()

    servidor = ec.generate_private_key(ec.SECP256R1())
    navegador = ec.generate_private_key(ec.SECP256R1())
    monkeypatch.setenv("PUSH_PRIVATE_KEY", codificar(servidor.private_numbers().private_value.to_bytes(32, "big")))
    monkeypatch.setenv("PUSH_CONTACT", "mailto:admin@example.test")
    peticiones = []

    def capturar(_sesion, url, **opciones):
        """Captura la petición HTTP sin realizar ninguna conexión."""
        peticiones.append((url, opciones))
        class Respuesta:
            """Simula una entrega aceptada por el servicio push."""
            status_code = 201
            text = ""
            headers = {}
            ok = True
        return Respuesta()

    monkeypatch.setattr("requests.Session.post", capturar)
    clave = codificar(navegador.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint))
    notificaciones_push.enviar_recordatorio_push("https://fcm.googleapis.com/fcm/send/uno", clave, codificar(os.urandom(16)), "Sacar pollo", "Pollo", date(2026, 11, 2))
    _, opciones = peticiones[0]
    assert opciones["allow_redirects"] is False
    assert opciones["headers"]["content-encoding"] == "aes128gcm"
    assert "vapid" in opciones["headers"]["authorization"].lower()
    assert b"Sacar pollo" not in opciones["data"]
