"""
Router com os endpoints da API de geração de planos — SPEC-007.

Endpoint principal:
- POST /api/diet/generate — aceita texto livre, retorna 3 planos + PDF

Download de PDF (mantido da versão anterior):
- GET /api/diet/{pdf_id}/pdf
"""

import re
import html
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from app.excecoes import (
    CamposObrigatoriosAusentesError,
    DeepSeekInvalidResponseError,
    DeepSeekTimeoutError,
    DeepSeekUnavailableError,
    GETForaDoIntervaloSeguroError,
    PlanValidationError,
    ValorFisiologicoInvalidoError,
)
from app.models.esquemas import TextGenerateRequest, DietGenerateResponseV2
from app.use_cases.gerar_planos import GerarPlanosUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diet", tags=["Dieta"])

# Cache simples para mapear request_id → nome do arquivo PDF
_pdf_cache: dict[str, str] = {}

# Singleton do caso de uso
_use_case = GerarPlanosUseCase()


# ─── Sanitização de input ──────────────────────────────────

def _sanitizar_texto(texto: str) -> str:
    """Remove tags HTML e caracteres de controle perigosos do input.

    Mantém quebras de linha (\n, \r) e tabs (\t) para preservar
    a formatação do texto do usuário.

    Args:
        texto: Texto bruto do usuário.

    Returns:
        Texto sanitizado.
    """
    # 1. Decodifica entidades HTML
    texto = html.unescape(texto)

    # 2. Remove tags HTML
    texto = re.sub(r"<[^>]*>", "", texto)

    # 3. Remove caracteres de controle, exceto \n, \r, \t
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)

    # 4. Normaliza espaços múltiplos
    texto = re.sub(r"[ \t]+", " ", texto)

    # 5. Normaliza quebras de linha (máximo 2 consecutivas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


# ═══════════════════════════════════════════════════════════
# POST /api/diet/generate
# ═══════════════════════════════════════════════════════════

@router.post("/generate", response_model=DietGenerateResponseV2)
def generate_diet(request: TextGenerateRequest):
    """Gera 3 planos alimentares personalizados a partir de texto livre.

    Fluxo (SPEC-006 + SPEC-007):
    1. Sanitiza o texto de entrada
    2. Extrai perfil do usuário via IA (DeepSeek)
    3. Calcula TMB, GET e distribuição de macros
    4. Gera 3 planos distintos via IA
    5. Valida e corrige automaticamente
    6. Gera PDF consolidado
    7. Retorna planos + URL do PDF

    Args:
        request: TextGenerateRequest com campo 'texto' (20-2000 caracteres).

    Returns:
        DietGenerateResponseV2 com paciente, TMB, GET, 3 planos, pdf_url.
    """
    # 1. Sanitizar input
    texto = _sanitizar_texto(request.texto)

    # 2. Validar comprimento pós-sanitização
    if len(texto) < 20:
        raise HTTPException(
            status_code=400,
            detail=(
                "O texto é muito curto após sanitização (mínimo 20 caracteres). "
                "Inclua mais detalhes como idade, peso, altura, sexo e rotina."
            ),
        )
    if len(texto) > 2000:
        raise HTTPException(
            status_code=400,
            detail="O texto excede o limite de 2000 caracteres.",
        )

    # 3. Executar caso de uso
    try:
        resultado = _use_case.executar(texto)
    except CamposObrigatoriosAusentesError as e:
        campos = ", ".join(e.campos_faltantes)
        raise HTTPException(
            status_code=400,
            detail=(
                f"Não consegui identificar: {campos}. "
                f"Tente incluir no texto: 'tenho Xkg, Ycm, Z anos, [masculino/feminino]'."
            ),
        )
    except ValorFisiologicoInvalidoError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except GETForaDoIntervaloSeguroError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except DeepSeekTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Tempo limite excedido ao gerar planos. Tente um texto mais curto.",
        )
    except DeepSeekUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="Nossa IA está temporariamente indisponível. Tente novamente em alguns minutos.",
        )
    except (DeepSeekInvalidResponseError, PlanValidationError):
        raise HTTPException(
            status_code=502,
            detail=(
                "Não foi possível gerar planos válidos. "
                "Tente descrever sua rotina com outras palavras."
            ),
        )
    except Exception:
        logger.exception("Erro inesperado na geração de planos")
        raise HTTPException(
            status_code=500,
            detail="Erro interno. Nossa equipe foi notificada. Tente novamente.",
        )

    # 4. Salvar mapping para download do PDF
    pdf_url = resultado.get("pdf_url")
    if pdf_url:
        # Extrair o nome do arquivo da URL
        pdf_id = pdf_url.split("/")[-1].replace(".pdf", "")
        _pdf_cache[pdf_id] = pdf_url.split("/")[-1]
        resultado["pdf_url"] = f"/api/diet/{pdf_id}/pdf"
    else:
        resultado["pdf_url"] = None

    return resultado


# ═══════════════════════════════════════════════════════════
# GET /api/diet/{pdf_id}/pdf
# ═══════════════════════════════════════════════════════════

@router.get("/{pdf_id}/pdf")
def download_pdf(pdf_id: str):
    """Download do PDF consolidado com os 3 planos alimentares.

    Args:
        pdf_id: UUID do PDF gerado (sem extensão).

    Returns:
        FileResponse com o arquivo PDF.
    """
    import os

    # Validar pdf_id contra path traversal
    if not re.match(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
        pdf_id,
    ):
        raise HTTPException(status_code=400, detail="ID do PDF inválido")

    nome_arquivo = _pdf_cache.get(pdf_id)
    if not nome_arquivo:
        raise HTTPException(status_code=404, detail="PDF não encontrado ou expirado")

    pdf_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "outputs", nome_arquivo
    )
    pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado no disco")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"plano_alimentar_{pdf_id[:8]}.pdf",
    )
