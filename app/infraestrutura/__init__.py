"""Camada de infraestrutura — clientes externos, banco de dados, catálogos."""

from app.infraestrutura.cliente_deepseek import DeepSeekClient
from app.infraestrutura.catalogo_alimentos import FoodCatalog, food_catalog

__all__ = ["DeepSeekClient", "FoodCatalog", "food_catalog"]
