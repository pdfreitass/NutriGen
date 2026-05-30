"""
Cliente HTTP tipado para a API DeepSeek.

Implementa comunicação com a API DeepSeek (OpenAI-compatible) com:
- Timeout configurável por chamada
- Retry com backoff exponencial
- Validação de resposta JSON
- Logs de latência e consumo de tokens
- Tratamento de erros com exceções customizadas

Uso:
    from app.infrastructure.deepseek_client import DeepSeekClient

    client = DeepSeekClient()
    response = client.chat_completion(
        messages=[...],
        temperature=0.7,
        response_format={"type": "json_object"},
        timeout=30,
    )
"""

import json
import logging
import time

import httpx

from app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_MAX_RETRIES,
)
from app.exceptions import (
    DeepSeekInvalidResponseError,
    DeepSeekTimeoutError,
    DeepSeekUnavailableError,
)

logger = logging.getLogger(__name__)

_RETRY_BACKOFF = [2.0, 4.0]  # segundos entre retries


class DeepSeekClient:
    """Cliente stateless para a API DeepSeek (OpenAI-compatible)."""

    def __init__(self) -> None:
        self._base_url = DEEPSEEK_BASE_URL.rstrip("/")
        self._api_key = DEEPSEEK_API_KEY
        self._model = DEEPSEEK_MODEL
        self._max_retries = DEEPSEEK_MAX_RETRIES

    # ─── Método principal ─────────────────────────

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        response_format: dict | None = None,
        timeout: int = 30,
        max_tokens: int | None = None,
    ) -> dict:
        """
        Envia uma requisição de chat completion para a API DeepSeek.

        Args:
            messages: Lista de mensagens no formato OpenAI.
            temperature: Nível de aleatoriedade (0.0 a 1.0).
            response_format: Formato da resposta (ex: {"type": "json_object"}).
            timeout: Timeout em segundos para esta chamada.
            max_tokens: Limite de tokens na resposta (opcional).

        Returns:
            Dict com a resposta completa da API (inclui choices, usage, etc.).

        Raises:
            DeepSeekTimeoutError: Timeout excedido.
            DeepSeekUnavailableError: API offline ou erro 5xx após retries.
            DeepSeekInvalidResponseError: Resposta não é JSON válido.
        """
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }

        if response_format:
            payload["response_format"] = response_format

        if max_tokens:
            payload["max_tokens"] = max_tokens

        return self._request_with_retry(
            method="POST",
            url=url,
            headers=headers,
            payload=payload,
            timeout=timeout,
        )

    # ─── Retry logic ──────────────────────────────

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict,
        payload: dict,
        timeout: int,
    ) -> dict:
        """Executa requisição HTTP com retry e backoff exponencial."""
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                start_time = time.monotonic()
                result = self._do_request(method, url, headers, payload, timeout)
                latency = time.monotonic() - start_time

                self._log_success(latency, result, attempt)
                return result

            except DeepSeekTimeoutError as e:
                last_error = e
                logger.warning(
                    "DeepSeek timeout (tentativa %d/%d)",
                    attempt + 1,
                    self._max_retries + 1,
                )
                if attempt < self._max_retries:
                    self._sleep(attempt)

            except DeepSeekUnavailableError as e:
                last_error = e
                logger.warning(
                    "DeepSeek indisponível (tentativa %d/%d): %s",
                    attempt + 1,
                    self._max_retries + 1,
                    e,
                )
                if attempt < self._max_retries:
                    self._sleep(attempt)

            except DeepSeekInvalidResponseError:
                # JSON inválido → não faz retry (problema não é de rede)
                raise

        # Esgotou retries
        if isinstance(last_error, DeepSeekTimeoutError):
            raise DeepSeekTimeoutError(
                f"API DeepSeek excedeu timeout de {timeout}s em "
                f"{self._max_retries + 1} tentativas."
            )
        raise DeepSeekUnavailableError(
            f"API DeepSeek indisponível após {self._max_retries + 1} tentativas."
        )

    def _do_request(
        self,
        method: str,
        url: str,
        headers: dict,
        payload: dict,
        timeout: int,
    ) -> dict:
        """Executa uma única requisição HTTP e processa a resposta."""
        with httpx.Client(timeout=timeout) as client:
            try:
                response = client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload,
                )
            except httpx.TimeoutException:
                raise DeepSeekTimeoutError(
                    f"Timeout ao chamar DeepSeek ({timeout}s)"
                )
            except httpx.NetworkError as e:
                raise DeepSeekUnavailableError(
                    f"Erro de rede ao chamar DeepSeek: {e}"
                )

            # Erros HTTP
            if response.status_code == 401:
                raise DeepSeekUnavailableError(
                    "API Key da DeepSeek inválida. Verifique DEEPSEEK_API_KEY."
                )
            if response.status_code == 429:
                raise DeepSeekUnavailableError(
                    "Rate limit da DeepSeek excedido."
                )
            if response.status_code >= 500:
                raise DeepSeekUnavailableError(
                    f"Erro interno da DeepSeek (HTTP {response.status_code})"
                )

            # Parse JSON
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError):
                raw = response.text[:500]
                raise DeepSeekInvalidResponseError(
                    f"DeepSeek retornou resposta não-JSON: {raw}"
                )

            # Verificar estrutura esperada
            if not data.get("choices"):
                raise DeepSeekInvalidResponseError(
                    f"Resposta da DeepSeek sem campo 'choices': {json.dumps(data)[:500]}"
                )

            return data

    # ─── Helpers ──────────────────────────────────

    @staticmethod
    def _sleep(attempt: int) -> None:
        """Espera com backoff antes do próximo retry."""
        delay = _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]
        time.sleep(delay)

    @staticmethod
    def _log_success(latency: float, response: dict, attempt: int) -> None:
        """Loga latência e tokens consumidos."""
        usage = response.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        logger.info(
            "DeepSeek OK | tentativa=%d | latência=%.2fs | "
            "tokens_in=%d | tokens_out=%d | total=%d",
            attempt + 1,
            latency,
            tokens_in,
            tokens_out,
            tokens_in + tokens_out,
        )

    # ─── Métodos de conveniência ──────────────────

    def extract_content(self, response: dict) -> str:
        """Extrai o conteúdo textual da resposta da API."""
        return response["choices"][0]["message"]["content"]

    def extract_json(self, response: dict) -> dict:
        """
        Extrai e faz parse do JSON do conteúdo da resposta.

        Raises:
            DeepSeekInvalidResponseError: Se o conteúdo não for JSON válido.
        """
        content = self.extract_content(response)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise DeepSeekInvalidResponseError(
                f"Conteúdo da resposta não é JSON válido: {e}. "
                f"Conteúdo: {content[:300]}"
            )
