"""
Script de análise de feedback — SPEC-044.

Lê os feedbacks do banco, agrupa por motivo negativo, extrai
exemplos e gera um relatório Markdown para revisão manual dos prompts.

Uso:
    python scripts/analisar_feedback.py
    python scripts/analisar_feedback.py --dias 30
"""

import argparse
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Adicionar raiz do projeto ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.banco_dados import SessionFactory
from app.models.database.feedback import Feedback


def analisar(dias: int = 30) -> str:
    """Analisa feedbacks recentes e retorna relatório Markdown."""
    agora = datetime.now(timezone.utc)
    data_corte = agora - timedelta(days=dias)

    with SessionFactory() as session:
        feedbacks = (
            session.query(Feedback)
            .filter(Feedback.criado_em >= data_corte)
            .order_by(Feedback.criado_em.desc())
            .all()
        )

    if not feedbacks:
        return f"## Análise de Feedback — Últimos {dias} dias\n\nNenhum feedback encontrado no período.\n"

    total = len(feedbacks)
    positivos = sum(1 for f in feedbacks if f.positivo)
    negativos = total - positivos
    pct_positivo = (positivos / total * 100) if total > 0 else 0

    # Agrupar motivos negativos
    motivos_negativos = Counter(
        f.motivo for f in feedbacks if not f.positivo and f.motivo
    )

    # Agrupar por eixo (plano_idx)
    por_eixo = Counter(f.plano_idx for f in feedbacks)

    # Exemplos de feedbacks negativos com comentário
    exemplos_negativos = [
        f for f in feedbacks
        if not f.positivo and f.comentario
    ][:10]

    lines = [
        f"## Análise de Feedback — Últimos {dias} dias",
        f"",
        f"**Data de geração:** {agora.strftime('%d/%m/%Y %H:%M')}",
        f"",
        f"### Resumo Geral",
        f"",
        f"| Métrica | Valor |",
        f"|---------|:----:|",
        f"| Total de feedbacks | {total} |",
        f"| 👍 Positivos | {positivos} ({pct_positivo:.1f}%) |",
        f"| 👎 Negativos | {negativos} ({100 - pct_positivo:.1f}%) |",
        f"",
        f"### Por Eixo (índice do plano)",
        f"",
        f"| Plano | Feedbacks |",
        f"|-------|:---------:|",
    ]

    eixo_labels = {0: "Tradicional Brasileiro", 1: "Funcional & Nutrientes", 2: "Prático & Rápido"}
    for idx in range(3):
        lines.append(f"| {eixo_labels[idx]} (idx={idx}) | {por_eixo.get(idx, 0)} |")

    lines.extend([
        "",
        "### Motivos de Insatisfação",
        "",
        "| Motivo | Ocorrências | % |",
        "|--------|:-----------:|:--:|",
    ])

    for motivo, count in motivos_negativos.most_common():
        pct = (count / negativos * 100) if negativos > 0 else 0
        lines.append(f"| {motivo} | {count} | {pct:.1f}% |")

    if exemplos_negativos:
        lines.extend([
            "",
            "### Exemplos de Comentários Negativos",
            "",
        ])
        for i, fb in enumerate(exemplos_negativos, 1):
            data_str = fb.criado_em.strftime("%d/%m/%Y")
            lines.append(f"{i}. [{data_str}] Plano {fb.plano_idx + 1} — **{fb.motivo}**: _{fb.comentario}_")

    lines.extend([
        "",
        "---",
        "",
        "### Ações Recomendadas",
        "",
        "1. Revisar os motivos mais frequentes acima",
        "2. Ajustar o prompt correspondente em `prompts/extraction_vX.txt` ou `prompts/generation_vX.txt`",
        "3. Criar nova versão (ex: `v2`) e atualizar `PROMPT_VERSION` no `.env`",
        "4. Testar com exemplos reais antes de deploy",
        "",
        f"> Relatório gerado automaticamente por `scripts/analisar_feedback.py`",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analisa feedbacks e gera relatório Markdown"
    )
    parser.add_argument(
        "--dias", type=int, default=30,
        help="Número de dias para analisar (default: 30)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Caminho para salvar relatório (default: stdout)"
    )
    args = parser.parse_args()

    try:
        relatorio = analisar(dias=args.dias)
    except Exception as e:
        print(f"Erro ao analisar feedbacks: {e}", file=sys.stderr)
        print("Verifique se o banco de dados está acessível.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"Relatório salvo em: {args.output}")
    else:
        print(relatorio)


if __name__ == "__main__":
    main()
