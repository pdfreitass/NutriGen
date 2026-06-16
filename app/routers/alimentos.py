"""
Router para o catálogo de alimentos — SPEC-063.

Disponibiliza o catálogo de alimentos para o frontend.
"""

from fastapi import APIRouter

from app.infrastructure.catalogo_alimentos import food_catalog

router = APIRouter(prefix="/api/foods", tags=["Alimentos"])


@router.get("/catalog")
def get_food_catalog():
    """Retorna o catálogo completo de alimentos organizado por categorias.

    Usado pelo frontend para renderizar a tela de seleção de alimentos (SPEC-061).
    """
    categorias = []
    for cat_nome in food_catalog.categorias_disponiveis():
        alimentos = food_catalog.buscar_por_categoria(cat_nome)
        categorias.append({
            "nome": cat_nome,
            "alimentos": [
                {
                    "nome": a.nome,
                    "proteina_g": a.proteina_g,
                    "carboidrato_g": a.carboidrato_g,
                    "gordura_g": a.gordura_g,
                    "calorias_kcal": a.calorias_kcal,
                }
                for a in alimentos
            ],
        })

    return {"categorias": categorias, "total": len(food_catalog.listar_todos())}
