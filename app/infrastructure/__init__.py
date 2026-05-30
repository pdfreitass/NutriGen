"""Camada de infraestrutura — clientes externos, banco de dados, catálogos."""

from app.infrastructure.deepseek_client import DeepSeekClient
from app.infrastructure.food_catalog import FoodCatalog, food_catalog

__all__ = ["DeepSeekClient", "FoodCatalog", "food_catalog"]
