"""
Router com os endpoints da API de Diet Plan Generator.
"""

import os
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import DietGenerateRequest, DietGenerateResponse
from app.services.diet_planner import gerar_plano_completo
from app.utils.pdf_generator import gerar_pdf

router = APIRouter(prefix="/api/diet", tags=["Dieta"])

# Cache simples para armazenar resultados e mapear IDs para arquivos
_resultados_cache: dict = {}


@router.post("/generate", response_model=DietGenerateResponse)
def generate_diet(
    request: DietGenerateRequest,
):
    """
    Gera 3 planos alimentares personalizados com base nos dados do paciente e rotinas.

    - Calcula TMB usando Mifflin-St Jeor
    - Calcula GET para cada rotina
    - Distribui macronutrientes
    - Sugere alimentos do banco de dados + preferidos do paciente
    - Gera PDF com os planos formatados
    """
    try:
        # 1. Gerar plano completo
        resultado = gerar_plano_completo(request)

        # 2. Gerar PDF (chamada síncrona)
        nome_pdf = gerar_pdf(resultado)

        # 3. Armazenar em cache (em produção usaríamos banco de dados)
        pdf_id = nome_pdf.replace(".pdf", "")
        _resultados_cache[pdf_id] = {
            "resultado": resultado,
            "pdf": nome_pdf,
        }

        # 4. Atualizar URL do PDF na resposta
        resultado.pdf_url = f"/api/diet/{pdf_id}/pdf"

        return resultado

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pdf_id}/pdf")
def download_pdf(pdf_id: str):
    """
    Download do PDF com os planos alimentares gerados.
    """
    # Validar pdf_id contra path traversal - regex rigorosa para UUID v4
    if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', pdf_id):
        raise HTTPException(status_code=400, detail="ID do PDF inválido")

    cache = _resultados_cache.get(pdf_id)
    if not cache:
        raise HTTPException(status_code=404, detail="PDF não encontrado ou expirado")

    pdf_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "outputs", cache["pdf"]
    )
    pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado no disco")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"plano_alimentar_{pdf_id[:8]}.pdf",
    )
