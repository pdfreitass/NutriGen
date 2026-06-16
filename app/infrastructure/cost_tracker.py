"""
Rastreador de custos da API DeepSeek — SPEC-045.

Singleton thread-safe que acumula custo diário estimado com base
nos tokens consumidos. Bloqueia geração se MAX_DAILY_COST_BRL excedido.
"""

import threading
import time
from datetime import datetime, timezone


class CostTracker:
    """Rastreador de custo diário estimado da API DeepSeek."""

    # Preços DeepSeek (USD por 1M tokens) — ajustar conforme pricing atual
    _PRICE_INPUT_PER_1M = 0.14   # $0.14/1M tokens de input
    _PRICE_OUTPUT_PER_1M = 0.28  # $0.28/1M tokens de output

    # Taxa de câmbio fixa para BRL (simplificado)
    _USD_TO_BRL = 5.50

    def __init__(self) -> None:
        self._custo_acumulado: float = 0.0
        self._data_atual: str = ""
        self._lock = threading.Lock()
        self._max_daily_cost: float = 50.0  # default, sobrescrito por config

    def configurar_limite(self, limite_brl: float) -> None:
        """Configura o custo máximo diário em BRL."""
        self._max_daily_cost = limite_brl

    def _resetar_se_novo_dia(self) -> None:
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if hoje != self._data_atual:
            self._custo_acumulado = 0.0
            self._data_atual = hoje

    def registrar_tokens(self, tokens_in: int, tokens_out: int) -> None:
        """Registra tokens consumidos em uma chamada à API.

        Args:
            tokens_in: Tokens de input (prompt).
            tokens_out: Tokens de output (completion).
        """
        custo_usd = (
            (tokens_in / 1_000_000) * self._PRICE_INPUT_PER_1M
            + (tokens_out / 1_000_000) * self._PRICE_OUTPUT_PER_1M
        )
        custo_brl = custo_usd * self._USD_TO_BRL

        with self._lock:
            self._resetar_se_novo_dia()
            self._custo_acumulado += custo_brl

    def limite_excedido(self) -> bool:
        """True se o custo diário excedeu o limite configurado."""
        with self._lock:
            self._resetar_se_novo_dia()
            return self._custo_acumulado >= self._max_daily_cost

    def custo_atual(self) -> float:
        """Retorna o custo acumulado hoje em BRL."""
        with self._lock:
            self._resetar_se_novo_dia()
            return round(self._custo_acumulado, 4)

    def limite_diario(self) -> float:
        """Retorna o limite diário configurado."""
        return self._max_daily_cost


# Singleton
cost_tracker = CostTracker()
