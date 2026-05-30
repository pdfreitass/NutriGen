"""
Serviço de extração NL→JSON — SPEC-003.

Converte o texto livre do usuário em um PerfilExtraido estruturado
usando a API DeepSeek com validações pós-extração.

Etapas:
1. Envia texto do usuário para DeepSeek com system prompt de extração
2. Parseia a resposta JSON em PerfilExtraido
3. Valida campos obrigatórios (RN-030, RN-040)
4. Aplica defaults: nivel_atividade (RN-031), objetivo (RN-032)
5. Valida intervalos fisiológicos (RN-041)
6. Loga latência e tokens consumidos
"""

import json
import logging
import time
from typing import Any

from app.config import EXTRACTION_TIMEOUT
from app.exceptions import (
    CamposObrigatoriosAusentesError,
    DeepSeekInvalidResponseError,
    ValorFisiologicoInvalidoError,
)
from app.infrastructure.deepseek_client import DeepSeekClient
from app.models.schemas import PerfilExtraido, Perfil, RotinaExtraida

logger = logging.getLogger(__name__)

# ─── System Prompt de Extração (inglês — LL-007) ────

_EXTRACTION_SYSTEM_PROMPT = """You are a nutritional information extractor. Convert the user's description into a structured JSON object with the fields below.

Rules:
1. Extract ONLY what is explicitly stated in the text. Do NOT invent values.
2. If a required field (sexo, idade, peso_kg, altura_cm) is not in the text, set it to null.
3. For 'nivel_atividade', classify as:
   - "sedentario" (does not exercise or less than 2x/week)
   - "moderado" (exercises 2-4x/week)
   - "ativo" (exercises 5-7x/week)
   If unclear, set to null.
4. For 'objetivo', classify as:
   - "perda_de_peso" (wants to lose weight, cut, get lean)
   - "manutencao" (wants to maintain, health, well-being)
   - "ganho_de_massa" (wants to gain weight, hypertrophy, bulk)
   If unclear, set to null.
5. Foods the user says they LIKE go in 'preferencias'.
6. Foods the user says they DON'T EAT / HATE / ARE ALLERGIC TO go in 'restricoes'.
7. Detect special conditions and mark in 'condicoes': "gravidez", "diabetes",
   "hipertensao", "vegano", "vegetariano", "intolerancia_lactose", etc.
8. Put any other relevant observations in 'extra'.
9. Return ONLY valid JSON. No markdown, no code blocks, no extra text."""

# Campos obrigatórios para prosseguir com a geração (RN-040)
_CAMPOS_OBRIGATORIOS = ["sexo", "idade", "peso_kg", "altura_cm"]

# Intervalos fisiológicos (RN-041)
_INTERVALOS_FISIOLOGICOS = {
    "idade": (1, 120),
    "peso_kg": (20, 500),
    "altura_cm": (50, 280),
}

# Mapeamento LLM → snake_case para nivel_atividade
_NIVEL_ATIVIDADE_VALIDOS = {"sedentario", "moderado", "ativo"}

# Mapeamento LLM → snake_case para objetivo
_OBJETIVO_VALIDOS = {"perda_de_peso", "manutencao", "ganho_de_massa"}

# Condições especiais detectáveis (RF-015)
_CONDICOES_CONHECIDAS = {
    "gravidez", "diabetes", "hipertensao", "vegano", "vegetariano",
    "intolerancia_lactose", "alergia_amendoim", "alergia_frutos_mar",
    "celiaco", "hipotireoidismo", "colesterol_alto",
}


class ExtractorService:
    """Serviço de extração de perfil nutricional a partir de texto livre.

    Usa a API DeepSeek para converter linguagem natural em JSON estruturado
    e aplica validações de negócio pós-extração.

    Uso:
        service = ExtractorService()
        perfil = service.extrair("Tenho 28 anos, 72kg, faço musculação 4x/semana...")
    """

    def __init__(self) -> None:
        self._client = DeepSeekClient()

    # ─── Método principal ─────────────────────────

    def extrair(self, texto: str) -> PerfilExtraido:
        """Extrai perfil nutricional estruturado do texto livre do usuário.

        Args:
            texto: Texto original do usuário em português.

        Returns:
            PerfilExtraido com dados demográficos, rotina, preferências e restrições.

        Raises:
            CamposObrigatoriosAusentesError: Se campos obrigatórios estiverem ausentes.
            ValorFisiologicoInvalidoError: Se valores fora dos intervalos fisiológicos.
            DeepSeekInvalidResponseError: Se a IA retornar JSON inválido.
        """
        if not texto or not texto.strip():
            raise CamposObrigatoriosAusentesError(
                campos_faltantes=_CAMPOS_OBRIGATORIOS,
                mensagem="Nenhum texto fornecido para extração.",
            )

        # 1. Chamar API DeepSeek
        start_time = time.monotonic()
        messages = [
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": texto.strip()},
        ]

        try:
            response = self._client.chat_completion(
                messages=messages,
                temperature=0.3,  # Extração deve ser determinística
                response_format={"type": "json_object"},
                timeout=EXTRACTION_TIMEOUT,
            )
        except Exception as e:
            latency = time.monotonic() - start_time
            logger.error("Falha na extração NL→JSON | latência=%.2fs | erro=%s", latency, e)
            raise

        latency = time.monotonic() - start_time

        # 2. Extrair JSON da resposta
        try:
            dados_brutos = self._client.extract_json(response)
        except DeepSeekInvalidResponseError:
            logger.error("JSON inválido na resposta de extração")
            raise

        # 3. Log de latência e tokens
        usage = response.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        logger.info(
            "Extração NL→JSON OK | latência=%.2fs | tokens_in=%d | tokens_out=%d | total=%d",
            latency, tokens_in, tokens_out, tokens_in + tokens_out,
        )

        # 4. Parse para PerfilExtraido
        perfil_extraido = self._parse_resposta(dados_brutos)

        # 5. Validações pós-extração
        self._validar_campos_obrigatorios(perfil_extraido)
        self._validar_intervalos_fisiologicos(perfil_extraido)
        self._aplicar_defaults(perfil_extraido)
        self._normalizar_condicoes(perfil_extraido)

        return perfil_extraido

    # ─── Parsing ──────────────────────────────────

    def _parse_resposta(self, dados: dict[str, Any]) -> PerfilExtraido:
        """Converte o JSON bruto da IA em PerfilExtraido, com tolerância a formato.

        O LLM pode retornar o objeto diretamente ou aninhado em chaves como
        'perfil', 'rotina', etc. Aceitamos ambos os formatos.
        """
        # Normalizar: se o JSON veio com chave única, extrair
        if isinstance(dados, dict) and "perfil" not in dados:
            # Pode estar envelopado em chave extra (ex: {"resultado": {...}})
            possible_keys = ["resultado", "profile", "data", "extracted"]
            for key in possible_keys:
                if key in dados and isinstance(dados[key], dict):
                    dados = dados[key]
                    break

        perfil_data = dados.get("perfil", {})
        rotina_data = dados.get("rotina", {})
        preferencias = dados.get("preferencias", [])
        restricoes = dados.get("restricoes", [])
        condicoes = dados.get("condicoes", [])
        extra = dados.get("extra", {})

        # Garantir que listas são de strings
        preferencias = self._normalizar_lista(preferencias)
        restricoes = self._normalizar_lista(restricoes)
        condicoes = self._normalizar_lista(condicoes)

        # Garantir que extra é dict
        if not isinstance(extra, dict):
            extra = {}

        # Construir Perfil
        perfil = Perfil(
            sexo=self._validar_sexo(perfil_data.get("sexo")),
            idade=self._parse_int(perfil_data.get("idade")),
            peso_kg=self._parse_float(perfil_data.get("peso_kg")),
            altura_cm=self._parse_float(perfil_data.get("altura_cm")),
        )

        # Construir Rotina
        rotina = RotinaExtraida(
            nivel_atividade=self._validar_nivel_atividade(
                rotina_data.get("nivel_atividade")
            ),
            objetivo=self._validar_objetivo(rotina_data.get("objetivo")),
            detalhes=self._parse_str(rotina_data.get("detalhes")),
        )

        return PerfilExtraido(
            perfil=perfil,
            rotina=rotina,
            preferencias=preferencias,
            restricoes=restricoes,
            condicoes=condicoes,
            extra=extra,
        )

    # ─── Validações pós-extração ──────────────────

    def _validar_campos_obrigatorios(self, perfil: PerfilExtraido) -> None:
        """RN-030, RN-040: Verifica se sexo, idade, peso e altura estão presentes."""
        faltantes: list[str] = []

        if perfil.perfil.sexo is None:
            faltantes.append("sexo")
        if perfil.perfil.idade is None:
            faltantes.append("idade")
        if perfil.perfil.peso_kg is None:
            faltantes.append("peso")
        if perfil.perfil.altura_cm is None:
            faltantes.append("altura")

        if faltantes:
            raise CamposObrigatoriosAusentesError(campos_faltantes=faltantes)

    def _validar_intervalos_fisiologicos(self, perfil: PerfilExtraido) -> None:
        """RN-041: Valida que idade, peso e altura estão nos intervalos plausíveis."""
        p = perfil.perfil

        if p.idade is not None:
            minimo, maximo = _INTERVALOS_FISIOLOGICOS["idade"]
            if p.idade < minimo or p.idade > maximo:
                raise ValorFisiologicoInvalidoError(
                    f"Idade '{p.idade}' fora do intervalo esperado ({minimo}-{maximo} anos)."
                )

        if p.peso_kg is not None:
            minimo, maximo = _INTERVALOS_FISIOLOGICOS["peso_kg"]
            if p.peso_kg < minimo or p.peso_kg > maximo:
                raise ValorFisiologicoInvalidoError(
                    f"Peso '{p.peso_kg}' fora do intervalo esperado ({minimo}-{maximo} kg)."
                )

        if p.altura_cm is not None:
            minimo, maximo = _INTERVALOS_FISIOLOGICOS["altura_cm"]
            if p.altura_cm < minimo or p.altura_cm > maximo:
                raise ValorFisiologicoInvalidoError(
                    f"Altura '{p.altura_cm}' fora do intervalo esperado ({minimo}-{maximo} cm)."
                )

    def _aplicar_defaults(self, perfil: PerfilExtraido) -> None:
        """Aplica valores padrão para campos não detectados.

        RN-031: Se nivel_atividade for null → assume "sedentario".
        RN-032: Se objetivo for null → calcula IMC e infere objetivo.
        """
        # RN-031: Default nivel_atividade
        if perfil.rotina.nivel_atividade is None:
            perfil.rotina.nivel_atividade = "sedentario"
            logger.info("RN-031: nivel_atividade não detectado → default 'sedentario'")

        # RN-032: Inferir objetivo pelo IMC
        if perfil.rotina.objetivo is None:
            objetivo_inferido = self._inferir_objetivo_por_imc(perfil)
            perfil.rotina.objetivo = objetivo_inferido
            logger.info(
                "RN-032: objetivo não detectado → inferido '%s' pelo IMC",
                objetivo_inferido,
            )

    def _normalizar_condicoes(self, perfil: PerfilExtraido) -> None:
        """Normaliza condições especiais: lowercase, remove duplicatas, filtra conhecidas."""
        condicoes_normalizadas: list[str] = []
        seen: set[str] = set()

        for cond in perfil.condicoes:
            cond_lower = cond.strip().lower()
            if cond_lower and cond_lower not in seen:
                seen.add(cond_lower)
                # Incluir mesmo se não for conhecida (pode ser relevante)
                condicoes_normalizadas.append(cond_lower)

        perfil.condicoes = condicoes_normalizadas

    # ─── Inferência de objetivo (RN-032) ───────────

    def _inferir_objetivo_por_imc(self, perfil: PerfilExtraido) -> str:
        """Calcula IMC e infere objetivo conforme RN-032.

        IMC < 18.5  → ganho_de_massa
        IMC 18.5-24.9 → manutencao
        IMC 25-29.9 → perda_de_peso
        IMC >= 30   → perda_de_peso
        """
        p = perfil.perfil
        if p.peso_kg is None or p.altura_cm is None:
            return "manutencao"  # fallback seguro

        altura_m = p.altura_cm / 100.0
        imc = p.peso_kg / (altura_m ** 2)

        if imc < 18.5:
            return "ganho_de_massa"
        elif imc < 25.0:
            return "manutencao"
        else:
            return "perda_de_peso"

    # ─── Helpers de parsing tipado ─────────────────

    @staticmethod
    def _validar_sexo(valor: Any) -> str | None:
        """Valida e normaliza sexo para 'masculino' ou 'feminino'."""
        if valor is None:
            return None
        if isinstance(valor, str):
            v = valor.strip().lower()
            if v in ("masculino", "male", "m", "homem"):
                return "masculino"
            if v in ("feminino", "female", "f", "mulher"):
                return "feminino"
        # Se for outro valor, retorna None para ser detectado como ausente
        logger.warning("Sexo não reconhecido: '%s' → tratado como None", valor)
        return None

    @staticmethod
    def _validar_nivel_atividade(valor: Any) -> str | None:
        """Valida e normaliza nivel_atividade."""
        if valor is None:
            return None
        if isinstance(valor, str):
            v = valor.strip().lower()
            # Mapeamento de variantes comuns
            mapa = {
                "sedentario": "sedentario",
                "sedentário": "sedentario",
                "sedentary": "sedentario",
                "moderado": "moderado",
                "moderate": "moderado",
                "ativo": "ativo",
                "active": "ativo",
                "atleta": "ativo",
                "leve": "sedentario",
                "light": "sedentario",
            }
            if v in mapa:
                return mapa[v]
            if v in _NIVEL_ATIVIDADE_VALIDOS:
                return v
        return None

    @staticmethod
    def _validar_objetivo(valor: Any) -> str | None:
        """Valida e normaliza objetivo."""
        if valor is None:
            return None
        if isinstance(valor, str):
            v = valor.strip().lower()
            mapa = {
                "emagrecer": "perda_de_peso",
                "perder peso": "perda_de_peso",
                "perda de peso": "perda_de_peso",
                "perda_de_peso": "perda_de_peso",
                "lose weight": "perda_de_peso",
                "cut": "perda_de_peso",
                "secar": "perda_de_peso",
                "definir": "perda_de_peso",
                "definição": "perda_de_peso",
                "manter": "manutencao",
                "manutenção": "manutencao",
                "manutencao": "manutencao",
                "maintain": "manutencao",
                "maintenance": "manutencao",
                "saude": "manutencao",
                "saúde": "manutencao",
                "bem-estar": "manutencao",
                "ganhar massa": "ganho_de_massa",
                "ganho de massa": "ganho_de_massa",
                "ganho_de_massa": "ganho_de_massa",
                "hipertrofia": "ganho_de_massa",
                "hypertrophy": "ganho_de_massa",
                "bulk": "ganho_de_massa",
                "crescer": "ganho_de_massa",
                "volume": "ganho_de_massa",
            }
            if v in mapa:
                return mapa[v]
            if v in _OBJETIVO_VALIDOS:
                return v
        return None

    @staticmethod
    def _parse_int(valor: Any) -> int | None:
        """Converte valor para int, com tolerância a float e string."""
        if valor is None:
            return None
        try:
            return int(valor)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_float(valor: Any) -> float | None:
        """Converte valor para float, com tolerância a int e string."""
        if valor is None:
            return None
        try:
            return float(valor)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_str(valor: Any) -> str | None:
        """Converte valor para str, retornando None se vazio."""
        if valor is None:
            return None
        s = str(valor).strip()
        return s if s else None

    @staticmethod
    def _normalizar_lista(valor: Any) -> list[str]:
        """Garante que o valor é uma lista de strings não-vazias."""
        if not isinstance(valor, list):
            return []
        result: list[str] = []
        for item in valor:
            if isinstance(item, str) and item.strip():
                result.append(item.strip())
        return result
