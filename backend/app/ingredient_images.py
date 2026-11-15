"""Resuelve imágenes de catálogo para líneas de ingredientes de texto libre."""
import hashlib
import re
import unicodedata

from app.models import ShoppingProduct


def normalizar(texto: str) -> str:
    """Normaliza mayúsculas y signos diacríticos para comparar palabras."""
    return "".join(caracter for caracter in unicodedata.normalize("NFD", texto.casefold()) if unicodedata.category(caracter) != "Mn")


def imagen_ingrediente(texto: str, productos: list[ShoppingProduct]) -> str | None:
    """Devuelve la imagen del nombre coincidente más largo, si tiene imagen."""
    linea = normalizar(texto)
    coincidencias = [producto for producto in productos if producto.name.strip() and re.search(r"(?<!\w)" + re.escape(normalizar(producto.name.strip())) + r"(?!\w)", linea)]
    if not coincidencias:
        return None
    producto = sorted(coincidencias, key=lambda item: (-len(normalizar(item.name.strip())), normalizar(item.name), str(item.id)))[0]
    if not producto.image_path:
        return None
    version = hashlib.sha256(producto.image_path.encode()).hexdigest()
    return f"/shopping-categories/{producto.category_id}/products/{producto.id}/image?v={version}"
