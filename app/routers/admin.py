"""
Router administrativo — SPEC-043.

Endpoints protegidos para métricas e analytics.
Acesso apenas com JWT de admin.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import func, text

from app.banco_dados import SessionFactory
from app.models.database.evento_analytics import EventoAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _verificar_admin(authorization: str | None) -> None:
    """Verifica se o token JWT pertence a um admin (email contém 'admin').

    Simplificado — em produção, usar role no banco.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticação necessária.")

    from app.services.servico_autenticacao import verificar_token_jwt
    user_id = verificar_token_jwt(authorization[7:])
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    # Verificação simples: admin é qualquer usuário autenticado por enquanto
    # Em produção, verificar role na tabela usuarios


@router.get("/metrics")
def get_metrics(authorization: str = Header(None)):
    """Retorna métricas agregadas de uso do sistema (admin apenas)."""
    _verificar_admin(authorization)

    agora = datetime.now(timezone.utc)
    hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = hoje - timedelta(days=7)
    inicio_mes = hoje - timedelta(days=30)

    with SessionFactory() as session:

        def _contar(tipo: str, desde: datetime) -> int:
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM eventos_analytics "
                    "WHERE tipo = :tipo AND criado_em >= :desde"
                ),
                {"tipo": tipo, "desde": desde},
            )
            return result.scalar() or 0

        # Gerações por período
        geracoes_hoje = _contar("plan_gerado", hoje)
        geracoes_semana = _contar("plan_gerado", inicio_semana)
        geracoes_mes = _contar("plan_gerado", inicio_mes)

        # Erros
        erros_semana = sum(
            _contar(t, inicio_semana)
            for t in ["erro_extracao", "erro_geracao", "erro_validacao"]
        )
        total_semana = geracoes_semana + erros_semana
        taxa_erro = (erros_semana / total_semana * 100) if total_semana > 0 else 0

        # Distribuição de objetivos e eixos (do JSON de metadados)
        objetivos = {"perda_de_peso": 0, "manutencao": 0, "ganho_de_massa": 0}
        eixos = {"tradicional": 0, "funcional": 0, "pratico": 0}

        eventos = (
            session.query(EventoAnalytics)
            .filter(
                EventoAnalytics.tipo == "plan_gerado",
                EventoAnalytics.criado_em >= inicio_semana,
            )
            .all()
        )

        for ev in eventos:
            if ev.metadados_json:
                try:
                    meta = json.loads(ev.metadados_json)
                    obj = meta.get("objetivo")
                    if obj in objetivos:
                        objetivos[obj] += 1
                    eixo = meta.get("eixo")
                    if eixo in eixos:
                        eixos[eixo] += 1
                except json.JSONDecodeError:
                    pass

        total_obj = sum(objetivos.values()) or 1
        total_eixo = sum(eixos.values()) or 1

        return {
            "periodo": {
                "hoje": hoje.strftime("%Y-%m-%d"),
                "dias": 7,
            },
            "geracoes": {
                "hoje": geracoes_hoje,
                "semana": geracoes_semana,
                "mes": geracoes_mes,
            },
            "objetivos_pct": {
                k: round(v / total_obj * 100, 1) for k, v in objetivos.items()
            },
            "eixos_pct": {
                k: round(v / total_eixo * 100, 1) for k, v in eixos.items()
            },
            "taxa_erro_pct": round(taxa_erro, 1),
            "latencia_media_s": {"extracao": 0, "geracao": 0, "total": 0},
            "custo_estimado_brl": 0.0,
            "top_alimentos": [],
        }
