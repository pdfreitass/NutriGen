"""
Módulo de geração de PDF com os planos alimentares usando ReportLab.
"""

import os
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors

from app.models.schemas import DietGenerateResponse

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "outputs")
OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)


def _garantir_pasta_outputs():
    """Garante que a pasta de outputs existe."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _estilos():
    """Retorna estilos personalizados para o PDF."""
    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloCapa",
        parent=estilos["Title"],
        fontSize=28,
        leading=34,
        spaceAfter=20,
        textColor=HexColor("#2E7D32"),
        alignment=1,
    ))

    estilos.add(ParagraphStyle(
        name="SubtituloCapa",
        parent=estilos["Normal"],
        fontSize=16,
        leading=22,
        spaceAfter=10,
        textColor=HexColor("#558B2F"),
        alignment=1,
    ))

    estilos.add(ParagraphStyle(
        name="NomeRotina",
        parent=estilos["Heading2"],
        fontSize=16,
        leading=20,
        spaceBefore=15,
        spaceAfter=8,
        textColor=HexColor("#1B5E20"),
    ))

    estilos.add(ParagraphStyle(
        name="Refeicao",
        parent=estilos["Heading3"],
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=HexColor("#33691E"),
    ))

    estilos.add(ParagraphStyle(
        name="InfoTexto",
        parent=estilos["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
    ))

    return estilos


def _criar_tabela_macros(macros: dict) -> Table:
    """Cria tabela de macronutrientes."""
    dados = [
        ["Macronutriente", "Gramas", "kcal"],
        ["Proteína", f"{macros['proteina_g']}g", f"{macros['proteina_g'] * 4:.0f} kcal"],
        ["Carboidrato", f"{macros['carboidrato_g']}g", f"{macros['carboidrato_g'] * 4:.0f} kcal"],
        ["Gordura", f"{macros['gordura_g']}g", f"{macros['gordura_g'] * 9:.0f} kcal"],
    ]

    tabela = Table(dados, colWidths=[120, 100, 100])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E7D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#A5D6A7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#E8F5E9"), colors.white]),
    ]))

    return tabela


def _criar_tabela_alimentos(alimentos: list) -> Table:
    """Cria tabela de alimentos de uma refeição."""
    dados = [
        ["Alimento", "Qtde (g)", "Prot (g)", "Carb (g)", "Gord (g)", "kcal"],
    ]
    for ali in alimentos:
        dados.append([
            ali["nome"],
            f"{ali['quantidade_g']:.0f}",
            f"{ali['proteina_g']:.1f}",
            f"{ali['carboidrato_g']:.1f}",
            f"{ali['gordura_g']:.1f}",
            f"{ali['calorias_kcal']:.0f}",
        ])

    tabela = Table(dados, colWidths=[120, 60, 60, 60, 60, 60])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#558B2F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#C5E1A5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F1F8E9"), colors.white]),
    ]))

    return tabela


def gerar_pdf(resultado: DietGenerateResponse) -> str:
    """
    Gera o PDF com os planos alimentares.

    Args:
        resultado: DietGenerateResponse com dados do paciente e planos

    Returns:
        Caminho relativo do arquivo PDF gerado
    """
    _garantir_pasta_outputs()
    estilos = _estilos()

    nome_arquivo = f"{uuid.uuid4()}.pdf"
    caminho_pdf = os.path.join(OUTPUT_DIR, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    elementos = []
    paciente = resultado.paciente
    data_atual = datetime.now().strftime("%d/%m/%Y")

    # === CAPA ===
    elementos.append(Spacer(1, 80))
    elementos.append(Paragraph("Diet Plan Generator", estilos["TituloCapa"]))
    elementos.append(Paragraph("Plano Alimentar Personalizado", estilos["SubtituloCapa"]))
    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph(f"<b>Paciente:</b> {paciente.nome}", estilos["InfoTexto"]))
    elementos.append(Paragraph(f"<b>Sexo:</b> {paciente.sexo}", estilos["InfoTexto"]))
    elementos.append(Paragraph(f"<b>Idade:</b> {paciente.idade} anos", estilos["InfoTexto"]))
    elementos.append(Paragraph(f"<b>Peso:</b> {paciente.peso_kg} kg", estilos["InfoTexto"]))
    elementos.append(Paragraph(f"<b>Altura:</b> {paciente.altura_cm} cm", estilos["InfoTexto"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph(f"<b>TMB (Mifflin-St Jeor):</b> {resultado.tmb} kcal/dia", estilos["InfoTexto"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Data: {data_atual}", estilos["InfoTexto"]))

    # === PLANOS ===
    for i, plano in enumerate(resultado.planos, 1):
        elementos.append(PageBreak())

        # Cabeçalho do plano
        elementos.append(Paragraph(f"Plano {i}: {plano.nome}", estilos["NomeRotina"]))
        elementos.append(Paragraph(
            f"<b>Nível de Atividade:</b> {plano.nivel_atividade} | "
            f"<b>GET:</b> {plano.get_calorico} kcal/dia",
            estilos["InfoTexto"],
        ))
        elementos.append(Spacer(1, 10))

        # Tabela de macros
        elementos.append(Paragraph("<b>Distribuição de Macronutrientes</b>", estilos["Refeicao"]))
        elementos.append(_criar_tabela_macros(plano.macros.model_dump()))
        elementos.append(Spacer(1, 15))

        # Refeições
        for refeicao in plano.refeicoes:
            elementos.append(Paragraph(refeicao.nome, estilos["Refeicao"]))
            if refeicao.alimentos:
                alimentos_dict = [
                    a.model_dump() for a in refeicao.alimentos
                ]
                elementos.append(_criar_tabela_alimentos(alimentos_dict))
            else:
                elementos.append(Paragraph(
                    "<i>Nenhum alimento sugerido para esta refeição.</i>",
                    estilos["InfoTexto"],
                ))
            elementos.append(Spacer(1, 8))

    # Gerar PDF
    doc.build(elementos)

    return nome_arquivo
