"""
Utilitário de carregamento versionado de prompts — SPEC-044.

Carrega system prompts de arquivos em prompts/ com versionamento.
Versão configurada via PROMPT_VERSION no .env (default: "v1").
"""

import os
import logging

logger = logging.getLogger(__name__)

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
_PROMPTS_DIR = os.path.abspath(_PROMPTS_DIR)
_DEFAULT_VERSION = "v1"


def _load_prompt_file(filename: str) -> str:
    """Carrega o conteúdo de um arquivo de prompt."""
    path = os.path.join(_PROMPTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de prompt não encontrado: {path}. "
            f"Verifique se PROMPT_VERSION está correta."
        )
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def carregar_prompt_extracao(version: str | None = None) -> str:
    """Carrega o system prompt de extração NL→JSON.

    Args:
        version: Versão do prompt (ex: "v1", "v2"). Default: PROMPT_VERSION env ou "v1".

    Returns:
        Conteúdo do prompt como string.
    """
    if version is None:
        version = os.getenv("PROMPT_VERSION", _DEFAULT_VERSION)
    filename = f"extraction_{version}.txt"
    prompt = _load_prompt_file(filename)
    logger.info("Prompt de extração carregado: %s", filename)
    return prompt


def carregar_prompt_geracao(version: str | None = None) -> str:
    """Carrega o system prompt de geração de planos via IA.

    Args:
        version: Versão do prompt (ex: "v1", "v2"). Default: PROMPT_VERSION env ou "v1".

    Returns:
        Conteúdo do prompt como string.
    """
    if version is None:
        version = os.getenv("PROMPT_VERSION", _DEFAULT_VERSION)
    filename = f"generation_{version}.txt"
    prompt = _load_prompt_file(filename)
    logger.info("Prompt de geração carregado: %s", filename)
    return prompt


def listar_versoes_disponiveis() -> dict[str, list[str]]:
    """Lista todas as versões de prompts disponíveis.

    Returns:
        Dict com chaves 'extraction' e 'generation', cada uma com lista de versões.
    """
    versions: dict[str, list[str]] = {"extraction": [], "generation": []}
    try:
        for filename in os.listdir(_PROMPTS_DIR):
            if filename.startswith("extraction_") and filename.endswith(".txt"):
                v = filename.replace("extraction_", "").replace(".txt", "")
                versions["extraction"].append(v)
            elif filename.startswith("generation_") and filename.endswith(".txt"):
                v = filename.replace("generation_", "").replace(".txt", "")
                versions["generation"].append(v)
    except FileNotFoundError:
        pass
    return versions
