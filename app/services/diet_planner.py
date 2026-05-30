"""
Módulo orquestrador que coordena o fluxo completo de geração do plano alimentar.
"""

from app.models.schemas import (
    DietGenerateRequest,
    DietGenerateResponse,
    PlanoAlimentar,
    MacrosGramas,
    AlimentoPlano,
    Refeicao,
)
from app.services.tmb_calculator import calcular_tmb, calcular_get
from app.services.macro_distributor import distribuir_macros
from app.services.food_suggester import sugerir_alimentos


def gerar_plano_completo(request: DietGenerateRequest) -> DietGenerateResponse:
    """
    Orquestra a geração completa do plano alimentar.

    Fluxo:
    1. Calcula TMB do paciente
    2. Para cada rotina:
       a. Calcula GET
       b. Distribui macros
       c. Sugere alimentos
       d. Monta refeições
    3. Retorna resposta com todos os planos

    Args:
        request: DietGenerateRequest com dados do paciente e rotinas

    Returns:
        DietGenerateResponse com TMB, planos e URL do PDF
    """
    paciente = request.paciente

    # 1. Calcular TMB
    tmb = calcular_tmb(
        sexo=paciente.sexo,
        peso_kg=paciente.peso_kg,
        altura_cm=paciente.altura_cm,
        idade=paciente.idade,
    )

    planos = []

    # 2. Processar cada rotina
    for rotina in request.rotinas:
        # a. Calcular GET
        get = calcular_get(tmb, rotina.nivel_atividade)

        # b. Distribuir macros
        macros_personalizados = None
        if rotina.macros_personalizados:
            macros_personalizados = {
                "proteina_pct": rotina.macros_personalizados.proteina_pct,
                "carboidrato_pct": rotina.macros_personalizados.carboidrato_pct,
                "gordura_pct": rotina.macros_personalizados.gordura_pct,
            }

        macros_gramas = distribuir_macros(
            get_calorico=get,
            objetivo=rotina.objetivo,
            macros_personalizados=macros_personalizados,
        )

        # c. Sugerir alimentos e montar refeições
        refeicoes_data = sugerir_alimentos(
            alimentos_preferidos=rotina.alimentos_preferidos,
            macros_necessarios=macros_gramas,
        )

        # d. Converter para modelos Pydantic
        refeicoes = []
        for ref_data in refeicoes_data:
            alimentos = [
                AlimentoPlano(
                    nome=ali["nome"],
                    quantidade_g=ali["quantidade_g"],
                    proteina_g=ali["proteina_g"],
                    carboidrato_g=ali["carboidrato_g"],
                    gordura_g=ali["gordura_g"],
                    calorias_kcal=ali["calorias_kcal"],
                )
                for ali in ref_data["alimentos"]
            ]
            refeicoes.append(Refeicao(nome=ref_data["nome"], alimentos=alimentos))

        plano = PlanoAlimentar(
            nome=rotina.nome,
            nivel_atividade=rotina.nivel_atividade,
            objetivo=rotina.objetivo,
            get_calorico=get,
            macros=MacrosGramas(**macros_gramas),
            refeicoes=refeicoes,
        )
        planos.append(plano)

    # O pdf_url será preenchido depois pelo router
    return DietGenerateResponse(
        paciente=paciente,
        tmb=tmb,
        planos=planos,
        pdf_url="",
    )
