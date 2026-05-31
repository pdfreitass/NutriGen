"""
Serviço de geração de 3 planos alimentares via IA — SPEC-004.

Envia os dados estruturados do usuário + metas nutricionais para a API
DeepSeek e recebe 3 planos completos em JSON, cada um em um eixo de
diferenciação distinto.

Fluxo:
1. Expande restrições genéricas para listas concretas via FoodCatalog
2. Monta catálogo de alimentos contextualizado (~3000 tokens)
3. Constrói system prompt (inglês) + user prompt (dados em português)
4. Chama DeepSeek com timeout 90s, retry 2x, temp 0.7
5. Parseia JSON de resposta em PlanosGerados
6. Valida: exatamente 3 planos, eixos corretos, alimentos no catálogo
7. Loga latência e tokens consumidos
"""

import json
import logging
import time
from typing import Any

from app.configuracao import GENERATION_TIMEOUT
from app.excecoes import DeepSeekInvalidResponseError
from app.infrastructure.cliente_deepseek import DeepSeekClient
from app.infrastructure.catalogo_alimentos import food_catalog
from app.models.esquemas import (
    ItemGerado,
    MetasNutricionais,
    PerfilExtraido,
    PlanoGerado,
    PlanosGerados,
    RefeicaoGerada,
)

logger = logging.getLogger(__name__)

# ─── System Prompt de Geração (inglês — LL-007) ──────────

_GENERATION_SYSTEM_PROMPT = """You are a professional nutritionist specialized in creating personalized meal plans. Generate EXACTLY 3 distinct meal plans for the user profile described below.

CRITICAL RULES — VIOLATION MEANS REJECTION:

1. Generate EXACTLY 3 plans. No more, no less.

2. THE 3 PLANS MUST USE THESE FIXED THEMATIC AXES:
   - Plan 1 — "Tradicional Brasileiro": Brazilian home-style cooking. Rice, beans, classic proteins (chicken, beef, eggs), simple salads. Affordable, familiar ingredients. AVOID quinoa, tofu, almond milk, peanut butter, whey protein.
   - Plan 2 — "Funcional & Nutrientes": Nutrient-dense whole foods. Quinoa, sweet potato, nuts, varied vegetables, lean proteins. Focus on antioxidants and micronutrient variety. AVOID white rice, french bread, fatty red meat.
   - Plan 3 — "Prático & Rápido": Quick-prep meals (< 15 min). Sandwiches, bowls, eggs, shakes, canned tuna. Ideal for busy routines. AVOID recipes requiring > 20 min of cooking or multiple pots.

3. Plans MUST be structurally different. At least 40% of foods must differ between any two plans.

4. RESTRICTIONS — ZERO TOLERANCE:
   The user has dietary restrictions. NONE of the forbidden foods listed below may appear in ANY plan. Not even in trace amounts. Not even as substitutes. ZERO TOLERANCE.

5. MACRO TARGETS:
   Each plan's total macros should be within ±10% of the targets provided. Prioritize hitting protein and total calories.

6. MEAL STRUCTURE PER PLAN:
   - 4 to 6 meals: Breakfast, Lunch, Afternoon Snack, Dinner (add Morning Snack and/or Evening Snack if needed).
   - 1 to 5 foods per meal.
   - Quantities between 30g and 500g per food item.
   - Include suggested times for each meal.

7. FOOD DATABASE:
   Use ONLY foods from the catalog provided below. DO NOT invent, suggest, or create any food not in this list. If the catalog does not have a food you want, choose the closest available alternative.

8. RESPONSE FORMAT:
   Return ONLY a valid JSON object with exactly the structure shown. No markdown, no code blocks, no extra text."""

# ─── Template do User Prompt ─────────────────────────────

_USER_PROMPT_TEMPLATE = """USER PROFILE:
- Sex: {sexo}
- Age: {idade} years
- Weight: {peso} kg
- Height: {altura} cm
- Activity level: {nivel_atividade}
- Goal: {objetivo}

CALCULATED NUTRITIONAL TARGETS (aim for ±10%):
- BMR: {tmb} kcal/day
- TDEE: {get_calorico} kcal/day
- Protein: {proteina_g}g | Carbs: {carboidrato_g}g | Fat: {gordura_g}g

PREFERRED FOODS (user likes): {preferencias}

FORBIDDEN FOODS — ZERO TOLERANCE: {restricoes}

SPECIAL CONDITIONS DETECTED: {condicoes}

USER'S ORIGINAL DESCRIPTION: "{texto_original}"

AVAILABLE FOOD CATALOG (name | protein | carbs | fat | kcal per 100g):
{food_catalog_text}"""

# ─── Limites ────────────────────────────────────────────

_MAX_CATALOG_TOKENS = 3000  # limite de tokens para o catálogo no prompt
_CHARS_PER_TOKEN_ESTIMATE = 4  # estimativa conservadora


class PlanGeneratorService:
    """Serviço de geração de planos alimentares via IA (DeepSeek).

    Recebe o perfil extraído do usuário e as metas nutricionais calculadas,
    monta prompts otimizados e retorna 3 planos validados.

    Uso:
        service = PlanGeneratorService()
        planos = service.gerar(perfil, metas, texto_original="...")
    """

    def __init__(self) -> None:
        self._client = DeepSeekClient()

    # ─── Método principal ─────────────────────────

    def gerar(
        self,
        perfil: PerfilExtraido,
        metas: MetasNutricionais,
        texto_original: str = "",
    ) -> PlanosGerados:
        """Gera 3 planos alimentares distintos via API DeepSeek.

        Args:
            perfil: PerfilExtraido com dados demográficos, rotina, preferências e restrições.
            metas: MetasNutricionais com TMB, GET e macros calculados.
            texto_original: Texto original do usuário (para contexto adicional).

        Returns:
            PlanosGerados com exatamente 3 PlanosGerados validados.

        Raises:
            DeepSeekInvalidResponseError: Se a IA retornar JSON inválido ou != 3 planos.
            DeepSeekTimeoutError: Se a API exceder o timeout.
            DeepSeekUnavailableError: Se a API estiver offline.
        """
        # 1. Expandir restrições genéricas para listas concretas (LL-004)
        restricoes_expandidas = self._expandir_restricoes(perfil.restricoes)

        # 2. Montar catálogo de alimentos contextualizado
        catalogo_texto = self._build_food_catalog_context(
            restricoes_expandidas, perfil.condicoes
        )

        # 3. Montar system prompt com restrições expandidas
        system_prompt = self._build_system_prompt(restricoes_expandidas)

        # 4. Montar user prompt com dados do perfil + metas + catálogo
        user_prompt = self._build_user_prompt(
            perfil, metas, restricoes_expandidas, catalogo_texto, texto_original
        )

        # 5. Chamar API DeepSeek
        start_time = time.monotonic()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self._client.chat_completion(
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"},
                timeout=GENERATION_TIMEOUT,
            )
        except Exception as e:
            latency = time.monotonic() - start_time
            logger.error(
                "Falha na geração de planos | latência=%.2fs | erro=%s", latency, e
            )
            raise

        latency = time.monotonic() - start_time

        # 6. Extrair e parsear JSON
        try:
            dados_brutos = self._client.extract_json(response)
        except DeepSeekInvalidResponseError:
            logger.error("JSON inválido na resposta de geração de planos")
            raise

        # 7. Log de latência e tokens
        usage = response.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        logger.info(
            "Geração de planos OK | latência=%.2fs | tokens_in=%d | tokens_out=%d | total=%d",
            latency, tokens_in, tokens_out, tokens_in + tokens_out,
        )

        # 8. Parse para PlanosGerados com validação
        planos = self._parse_e_validar(dados_brutos)

        # 9. Validar alimentos contra o catálogo (pós-validação leve)
        self._validar_alimentos_no_catalogo(planos)

        return planos

    # ─── Expansão de restrições ──────────────────

    def _expandir_restricoes(self, restricoes: list[str]) -> list[str]:
        """Expande restrições genéricas para listas concretas de alimentos.

        Usa FoodCatalog.expandir_restricao() que mapeia termos como
        "peixe", "laticínios", "vegano" para listas de alimentos proibidos.

        Remove duplicatas e ordena alfabeticamente para consistência.

        Args:
            restricoes: Lista de restrições em linguagem natural.

        Returns:
            Lista plana e sem duplicatas de nomes de alimentos proibidos.
        """
        proibidos: set[str] = set()

        for restricao in restricoes:
            expandidos = food_catalog.expandir_restricao(restricao)
            for nome in expandidos:
                proibidos.add(nome)

        return sorted(proibidos)

    # ─── Construção do catálogo contextualizado ──

    def _build_food_catalog_context(
        self,
        restricoes_expandidas: list[str],
        condicoes: list[str],
    ) -> str:
        """Monta representação textual compacta do catálogo de alimentos.

        Remove alimentos explicitamente proibidos e categorias excluídas
        por condições especiais (ex: vegano → sem Carnes e Peixes).

        Limita a ~3000 tokens estimados para não sobrecarregar o prompt.

        Args:
            restricoes_expandidas: Lista de nomes de alimentos proibidos.
            condicoes: Condições especiais detectadas (ex: ["vegano"]).

        Returns:
            String formatada com o catálogo relevante.
        """
        proibidos = set(r.lower() for r in restricoes_expandidas)

        # Categorias a excluir por condições especiais
        categorias_excluidas: set[str] = set()
        if "vegano" in condicoes:
            categorias_excluidas.update(["Carnes e Peixes", "Laticínios"])
        if "vegetariano" in condicoes or "ovolactovegetariano" in condicoes:
            categorias_excluidas.add("Carnes e Peixes")
        if "intolerancia_lactose" in condicoes:
            categorias_excluidas.add("Laticínios")

        linhas: list[str] = []
        total_chars = 0

        for categoria in food_catalog.categorias_disponiveis():
            if categoria in categorias_excluidas:
                continue

            alimentos = food_catalog.buscar_por_categoria(categoria)
            alimentos_filtrados = [
                a for a in alimentos if a.nome.lower() not in proibidos
            ]

            if not alimentos_filtrados:
                continue

            # Cada linha: "nome | proteina | carbo | gordura | kcal"
            for alimento in alimentos_filtrados:
                linha = (
                    f"{alimento.nome} | "
                    f"P:{alimento.proteina_g}g | "
                    f"C:{alimento.carboidrato_g}g | "
                    f"F:{alimento.gordura_g}g | "
                    f"{alimento.calorias_kcal}kcal"
                )
                total_chars += len(linha) + 1  # +1 for newline
                linhas.append(linha)

        # Limitar a ~3000 tokens (estimativa: 1 token ≈ 4 chars)
        max_chars = _MAX_CATALOG_TOKENS * _CHARS_PER_TOKEN_ESTIMATE
        if total_chars > max_chars:
            # Truncar: remover itens do final até caber
            while total_chars > max_chars and linhas:
                removido = linhas.pop()
                total_chars -= len(removido) + 1
            logger.warning(
                "Catálogo truncado para caber em ~%d tokens. %d itens removidos.",
                _MAX_CATALOG_TOKENS,
                len(food_catalog.listar_todos()) - len(linhas),
            )

        return "\n".join(linhas)

    # ─── Construção dos prompts ──────────────────

    def _build_system_prompt(self, restricoes_expandidas: list[str]) -> str:
        """Constrói o system prompt final com a lista de restrições expandida.

        As restrições são inseridas DIRETAMENTE no system prompt ANTES das
        preferências (LL-003 — ordem importa para o modelo dar mais peso).
        """
        if restricoes_expandidas:
            restricoes_texto = "FORBIDDEN FOODS (DO NOT USE IN ANY PLAN):\n"
            restricoes_texto += "\n".join(f"  - {r}" for r in restricoes_expandidas)
            restricoes_texto += "\n\nNONE of these foods may appear. ZERO TOLERANCE."
        else:
            restricoes_texto = "No specific food restrictions."

        # Insere a lista de restrições logo após a regra #4
        prompt = _GENERATION_SYSTEM_PROMPT.replace(
            "NONE of the forbidden foods listed below may appear in ANY plan. "
            "Not even in trace amounts. Not even as substitutes. ZERO TOLERANCE.",
            restricoes_texto,
        )

        return prompt

    def _build_user_prompt(
        self,
        perfil: PerfilExtraido,
        metas: MetasNutricionais,
        restricoes_expandidas: list[str],
        catalogo_texto: str,
        texto_original: str,
    ) -> str:
        """Constrói o user prompt com todos os dados do usuário e catálogo."""
        p = perfil.perfil
        r = perfil.rotina

        # Labels amigáveis
        sexo = p.sexo or "não informado"
        idade = p.idade if p.idade is not None else "não informada"
        peso = f"{p.peso_kg:.1f}" if p.peso_kg is not None else "não informado"
        altura = f"{p.altura_cm:.0f}" if p.altura_cm is not None else "não informada"
        nivel = r.nivel_atividade or "sedentario"
        objetivo = r.objetivo or "manutencao"

        # Preferências como string
        if perfil.preferencias:
            preferencias = ", ".join(perfil.preferencias)
        else:
            preferencias = "nenhuma preferência específica"

        # Restrições expandidas como string
        if restricoes_expandidas:
            restricoes = ", ".join(restricoes_expandidas)
        else:
            restricoes = "nenhuma restrição"

        # Condições especiais
        condicoes = ", ".join(perfil.condicoes) if perfil.condicoes else "nenhuma"

        # Texto original truncado (segurança)
        texto = texto_original[:2000] if texto_original else ""

        return _USER_PROMPT_TEMPLATE.format(
            sexo=sexo,
            idade=idade,
            peso=peso,
            altura=altura,
            nivel_atividade=nivel,
            objetivo=objetivo,
            tmb=f"{metas.tmb:.0f}",
            get_calorico=f"{metas.get_calorico:.0f}",
            proteina_g=f"{metas.proteina_g:.1f}",
            carboidrato_g=f"{metas.carboidrato_g:.1f}",
            gordura_g=f"{metas.gordura_g:.1f}",
            preferencias=preferencias,
            restricoes=restricoes,
            condicoes=condicoes,
            texto_original=texto,
            food_catalog_text=catalogo_texto,
        )

    # ─── Parsing e validação ─────────────────────

    def _parse_e_validar(self, dados_brutos: dict[str, Any]) -> PlanosGerados:
        """Converte o JSON bruto da IA em PlanosGerados com validação.

        Trata variações comuns no formato de resposta da LLM:
        - Resposta envelopada em chave extra (ex: {"result": {...}})
        - Campo 'planos' vs 'plans' vs array direto
        - Campos ausentes preenchidos com defaults

        Raises:
            DeepSeekInvalidResponseError: Se não houver exatamente 3 planos.
        """
        # Normalizar: extrair de envelope se necessário
        if isinstance(dados_brutos, dict):
            if "planos" not in dados_brutos:
                # Tentar chaves alternativas
                for key in ("plans", "result", "data", "response"):
                    if key in dados_brutos and isinstance(dados_brutos[key], dict):
                        inner = dados_brutos[key]
                        if "planos" in inner or "plans" in inner:
                            dados_brutos = inner
                            break

        # Extrair a lista de planos
        planos_raw = dados_brutos.get("planos") or dados_brutos.get("plans") or []

        # Se ainda não for lista, pode ser que a resposta seja o array diretamente
        if not isinstance(planos_raw, list):
            if isinstance(dados_brutos, list):
                planos_raw = dados_brutos
            else:
                raise DeepSeekInvalidResponseError(
                    f"Resposta da IA não contém array 'planos'. "
                    f"Recebido: {json.dumps(dados_brutos)[:300]}"
                )

        # Validar quantidade
        if len(planos_raw) != 3:
            raise DeepSeekInvalidResponseError(
                f"A IA gerou {len(planos_raw)} planos em vez de exatamente 3. "
                f"Rejeitando resposta completa."
            )

        # Parsear cada plano
        planos = []
        eixos_esperados = ["tradicional", "funcional", "pratico"]
        eixos_vistos: set[str] = set()

        for i, plano_raw in enumerate(planos_raw):
            try:
                plano = self._parse_plano(plano_raw, i)
                planos.append(plano)
                eixos_vistos.add(plano.eixo)
            except Exception as e:
                raise DeepSeekInvalidResponseError(
                    f"Erro ao parsear plano {i + 1}: {e}"
                )

        # Validar que os 3 eixos estão presentes
        for eixo in eixos_esperados:
            if eixo not in eixos_vistos:
                logger.warning(
                    "Eixo '%s' não encontrado nos planos gerados. Eixos presentes: %s",
                    eixo, eixos_vistos,
                )

        return PlanosGerados(planos=planos)

    def _parse_plano(self, dados: dict[str, Any], indice: int) -> PlanoGerado:
        """Parseia um plano individual com tolerância a campos ausentes."""
        # Eixo: tentar detectar do nome ou usar valor do campo
        nome = dados.get("nome", f"Plano {indice + 1}")
        eixo = dados.get("eixo", "")

        # Inferir eixo pelo nome se ausente
        if not eixo or eixo not in ("tradicional", "funcional", "pratico"):
            eixo = self._inferir_eixo(nome, indice)

        descricao = dados.get("descricao", "")
        if not descricao or len(descricao) < 10:
            descricao = f"Plano {nome} — gerado automaticamente."

        objetivo = dados.get("objetivo", "manutencao")
        calorias = float(dados.get("calorias_estimadas", 0))

        # Parsear refeições
        refeicoes_raw = dados.get("refeicoes") or dados.get("meals") or dados.get("meal_plan") or []
        if not isinstance(refeicoes_raw, list):
            refeicoes_raw = []

        refeicoes = []
        for ref_raw in refeicoes_raw:
            try:
                refeicao = self._parse_refeicao(ref_raw)
                refeicoes.append(refeicao)
            except Exception as e:
                logger.warning("Erro ao parsear refeição no plano '%s': %s", nome, e)
                continue

        if len(refeicoes) < 3:
            logger.warning(
                "Plano '%s' tem apenas %d refeições (mínimo 3).",
                nome, len(refeicoes),
            )

        return PlanoGerado(
            nome=str(nome),
            descricao=str(descricao),
            eixo=eixo,  # type: ignore[arg-type]
            objetivo=str(objetivo),
            calorias_estimadas=calorias,
            refeicoes=refeicoes,
        )

    def _parse_refeicao(self, dados: dict[str, Any]) -> RefeicaoGerada:
        """Parseia uma refeição individual."""
        nome = dados.get("nome", "Refeição")
        horario = dados.get("horario")

        alimentos_raw = dados.get("alimentos") or dados.get("foods") or dados.get("items") or []
        if not isinstance(alimentos_raw, list):
            alimentos_raw = []

        alimentos = []
        for item_raw in alimentos_raw:
            try:
                qtd = float(item_raw.get("quantidade_g", 0) or 0)
                # Clampar quantidade: mínimo 10g, máximo 1000g
                qtd = max(10.0, min(qtd, 1000.0))
                alimento = ItemGerado(
                    nome=str(item_raw.get("nome", "")),
                    quantidade_g=qtd,
                    proteina_g=float(item_raw.get("proteina_g", 0) or 0),
                    carboidrato_g=float(item_raw.get("carboidrato_g", 0) or 0),
                    gordura_g=float(item_raw.get("gordura_g", 0) or 0),
                    calorias_kcal=float(item_raw.get("calorias_kcal", 0) or 0),
                )
                alimentos.append(alimento)
            except (ValueError, TypeError) as e:
                logger.warning("Erro ao parsear alimento '%s': %s", item_raw.get("nome", "?"), e)
                continue

        return RefeicaoGerada(
            nome=str(nome),
            horario=str(horario) if horario else None,
            alimentos=alimentos,
        )

    # ─── Validação pós-parse ─────────────────────

    def _validar_alimentos_no_catalogo(self, planos: PlanosGerados) -> None:
        """Verifica se os alimentos gerados existem no catálogo.

        Apenas loga warnings (não rejeita) — a validação pesada é feita
        pelo PlanValidator na SPEC-005. Aqui é uma verificação leve.

        Args:
            planos: PlanosGerados a serem verificados.
        """
        alimentos_invalidos: list[tuple[str, str]] = []

        for plano in planos.planos:
            for refeicao in plano.refeicoes:
                for alimento in refeicao.alimentos:
                    encontrado = food_catalog.buscar_por_nome(alimento.nome)
                    if not encontrado:
                        alimentos_invalidos.append((plano.nome, alimento.nome))

        if alimentos_invalidos:
            for plano_nome, alimento_nome in alimentos_invalidos:
                logger.warning(
                    "Alimento '%s' no plano '%s' não encontrado no catálogo. "
                    "Será tratado pelo PlanValidator.",
                    alimento_nome, plano_nome,
                )

    # ─── Helpers ──────────────────────────────────

    @staticmethod
    def _inferir_eixo(nome: str, indice: int) -> str:
        """Infere o eixo de diferenciação pelo nome do plano ou índice."""
        nome_lower = nome.lower()

        if any(p in nome_lower for p in ("tradicional", "brasileiro", "arroz", "feijão")):
            return "tradicional"
        if any(p in nome_lower for p in ("funcional", "nutriente", "nutritivo", "quinoa")):
            return "funcional"
        if any(p in nome_lower for p in ("prático", "pratico", "rápido", "rapido", "corrido")):
            return "pratico"

        # Fallback por índice
        eixos = ["tradicional", "funcional", "pratico"]
        return eixos[min(indice, len(eixos) - 1)]


# ─── Singleton ─────────────────────────────────────────

plan_generator = PlanGeneratorService()
