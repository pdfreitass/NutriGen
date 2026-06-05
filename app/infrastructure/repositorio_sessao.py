"""
Repositório para SessaoGeracao e PlanoAlimentar — SPEC-040.

Fornece queries para listagem paginada de histórico e exclusão
de sessões com cascade delete (LGPD).
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from app.banco_dados import SessionFactory, engine

logger = logging.getLogger(__name__)

# SQL bruto para queries performáticas (evita overhead do ORM para listagem)
_LISTAR_SESSOES_SQL = """
    SELECT TOP :limit
        sg.id, sg.data_geracao, sg.objetivo, sg.get_calorico, sg.tmb,
        sg.pdf_uuid, sg.data_expiracao_pdf
    FROM sessoes_geracao sg
    WHERE sg.usuario_id = :usuario_id
      AND sg.data_geracao > :data_corte
    ORDER BY sg.data_geracao DESC
    OFFSET :offset ROWS
"""

_CONTAR_SESSOES_SQL = """
    SELECT COUNT(*) as total
    FROM sessoes_geracao
    WHERE usuario_id = :usuario_id
      AND data_geracao > :data_corte
"""

_LISTAR_PLANOS_RESUMO_SQL = """
    SELECT pa.sessao_id, pa.nome, pa.eixo, pa.get_calorico
    FROM planos_alimentares pa
    WHERE pa.sessao_id IN :sessao_ids
    ORDER BY pa.sessao_id, pa.ordem
"""

_DELETE_SESSAO_SQL = """
    DELETE FROM sessoes_geracao WHERE id = :sessao_id AND usuario_id = :usuario_id
"""


class SessaoGeracaoRepository:
    """Repositório para histórico de gerações do usuário."""

    # Constantes de retenção (RN-130, RN-131)
    RETENCAO_PLANOS_DIAS = 30
    RETENCAO_PDF_DIAS = 7

    def listar_historico(
        self, usuario_id: int, page: int = 1, limit: int = 10
    ) -> tuple[list[dict], int]:
        """Retorna lista paginada de sessões do usuário.

        Args:
            usuario_id: ID do usuário autenticado.
            page: Página (1-based).
            limit: Itens por página (max 50).

        Returns:
            Tuple (items, total) onde items é lista de dicts com dados da sessão.
        """
        limit = min(limit, 50)
        offset = (page - 1) * limit
        data_corte = datetime.now(timezone.utc) - timedelta(days=self.RETENCAO_PLANOS_DIAS)

        with SessionFactory() as session:
            # Contar total
            result = session.execute(
                text(_CONTAR_SESSOES_SQL),
                {"usuario_id": usuario_id, "data_corte": data_corte},
            )
            total = result.scalar() or 0

            # Listar sessões
            result = session.execute(
                text(_LISTAR_SESSOES_SQL),
                {
                    "usuario_id": usuario_id,
                    "data_corte": data_corte,
                    "limit": limit,
                    "offset": offset,
                },
            )
            rows = result.fetchall()

            if not rows:
                return [], total

            # Montar items
            agora = datetime.now(timezone.utc)
            items = []
            for row in rows:
                pdf_disponivel = False
                pdf_url = None
                if row.pdf_uuid and row.data_expiracao_pdf:
                    if row.data_expiracao_pdf.replace(tzinfo=timezone.utc) > agora:
                        pdf_disponivel = True
                        pdf_url = f"/api/diet/{row.pdf_uuid}/pdf"

                items.append({
                    "sessao_id": row.id,
                    "data_geracao": row.data_geracao.isoformat() if row.data_geracao else None,
                    "objetivo": row.objetivo or "manutencao",
                    "get_calorico": row.get_calorico or 0,
                    "tmb": row.tmb or 0,
                    "pdf_disponivel": pdf_disponivel,
                    "pdf_url": pdf_url,
                })

            # Buscar resumo dos planos para todas as sessões
            sessao_ids = tuple(item["sessao_id"] for item in items)
            if sessao_ids:
                result = session.execute(
                    text(_LISTAR_PLANOS_RESUMO_SQL),
                    {"sessao_ids": sessao_ids},
                )
                planos_rows = result.fetchall()

                # Agrupar planos por sessao_id
                planos_por_sessao: dict[int, list[dict]] = {}
                for pr in planos_rows:
                    if pr.sessao_id not in planos_por_sessao:
                        planos_por_sessao[pr.sessao_id] = []
                    planos_por_sessao[pr.sessao_id].append({
                        "nome": pr.nome,
                        "eixo": pr.eixo,
                        "calorias_estimadas": pr.get_calorico or 0,
                    })

                for item in items:
                    item["resumo"] = {
                        "planos": planos_por_sessao.get(item["sessao_id"], [])
                    }

            return items, total

    def excluir_sessao(self, sessao_id: int, usuario_id: int) -> bool:
        """Exclui uma sessão e todos os dados associados (cascade).

        Args:
            sessao_id: ID da sessão.
            usuario_id: ID do dono (verificação de propriedade).

        Returns:
            True se excluiu, False se não encontrada ou não pertence ao usuário.
        """
        with SessionFactory() as session:
            result = session.execute(
                text(_DELETE_SESSAO_SQL),
                {"sessao_id": sessao_id, "usuario_id": usuario_id},
            )
            session.commit()
            return result.rowcount > 0


# Singleton
sessao_repo = SessaoGeracaoRepository()
