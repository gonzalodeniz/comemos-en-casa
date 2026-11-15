"""Verifica las coincidencias de imágenes con ingredientes libres."""
from uuid import uuid4
from app.ingredient_images import imagen_ingrediente
from app.models import ShoppingProduct


def test_coincidencia_completa_prioriza_nombre_mas_largo():
    """Reconoce tildes y prioriza el producto específico sin coincidencias parciales."""
    categoria = uuid4()
    corto = ShoppingProduct(id=uuid4(), category_id=categoria, name="Pimentón", image_path="corto.png")
    largo = ShoppingProduct(id=uuid4(), category_id=categoria, name="Pimentón dulce", image_path="largo.png")
    assert str(largo.id) in imagen_ingrediente("Una pizca de PIMENTON dulce", [corto, largo])
    assert str(corto.id) in imagen_ingrediente("Una pizca de pimentón", [corto, largo])
    assert imagen_ingrediente("pimentonero", [corto]) is None
