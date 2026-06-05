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

from fastapi import APIRouter, Header, HTTPException, Query, Request
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
from app.models.esquemas import DietGenerateRequestV2, DietGenerateResponseV2
from app.use_cases.gerar_planos import GerarPlanosUseCase
from app.services.servico_autenticacao import verificar_token_jwt
from app.infrastructure.repositorio_sessao import sessao_repo

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
def generate_diet(
    request: DietGenerateRequestV2,
    authorization: str = Header(None),
):
    """Gera 3 planos alimentares personalizados com dados do formulário + rotina.

    Fluxo:
    1. Recebe dados estruturados (sexo, idade, peso, altura, atividade)
    2. Recebe texto livre com rotina, objetivos, preferências
    3. Extrai preferências/restrições do texto via IA
    4. Calcula TMB, GET e distribuição de macros
    5. Gera 3 planos distintos via IA
    6. Valida e corrige automaticamente
    7. Gera PDF consolidado
    8. Se autenticado, persiste no histórico (SPEC-040)
    """
    # Sanitizar texto
    texto = _sanitizar_texto(request.texto)

    if len(texto) < 10:
        raise HTTPException(
            status_code=400,
            detail="Descreva sua rotina, objetivos e preferências (mínimo 10 caracteres).",
        )

    # Extrair usuario_id se autenticado (SPEC-040)
    usuario_id = _get_usuario_id(authorization)

    # Executar caso de uso com dados estruturados + texto
    try:
        resultado = _use_case.executar_com_dados(
            sexo=request.sexo,
            idade=request.idade,
            peso_kg=request.peso_kg,
            altura_cm=request.altura_cm,
            nivel_atividade=request.nivel_atividade,
            texto=texto,
            usuario_id=usuario_id,
        )
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


# ═══════════════════════════════════════════════════════════
# Helpers de autenticação (SPEC-040)
# ═══════════════════════════════════════════════════════════

def _get_usuario_id(authorization: str = Header(None)) -> int | None:
    """Extrai usuario_id do header Authorization: Bearer <JWT>."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    user_id = verificar_token_jwt(token)
    return int(user_id) if user_id else None


def _requer_autenticacao(usuario_id: int | None) -> int:
    """Garante que o usuário está autenticado. Levanta 401 se não."""
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")
    return usuario_id


# ═══════════════════════════════════════════════════════════
# GET /api/diet/history (SPEC-040)
# ═══════════════════════════════════════════════════════════

@router.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    usuario_id: int | None = Header(None, alias="X-User-Id"),
    authorization: str = Header(None),
):
    """Retorna histórico paginado de gerações do usuário autenticado."""
    # Autenticar via JWT
    uid = _get_usuario_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")

    items, total = sessao_repo.listar_historico(uid, page=page, limit=limit)
    pages = max(1, (total + limit - 1) // limit)

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
    }


# ═══════════════════════════════════════════════════════════
# DELETE /api/diet/{sessao_id} (SPEC-040 — LGPD)
# ═══════════════════════════════════════════════════════════

@router.delete("/{sessao_id:int}")
def delete_sessao(
    sessao_id: int,
    authorization: str = Header(None),
):
    """Exclui uma sessão de geração e todos os dados associados."""
    uid = _get_usuario_id(authorization)
    if uid is None:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")

    excluido = sessao_repo.excluir_sessao(sessao_id, uid)
    if not excluido:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    return {"mensagem": "Sessão excluída com sucesso."}
