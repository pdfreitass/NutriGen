"""
Módulo de integração com a API ViaCEP para busca automática de endereço.
"""

import httpx
from typing import Optional, Dict


def buscar_endereco_por_cep(cep: str) -> Optional[Dict[str, str]]:
    """
    Busca endereço na API ViaCEP.

    Args:
        cep: CEP com 8 dígitos (apenas números)

    Returns:
        Dict com logradouro, bairro, cidade, estado ou None se CEP inválido
    """
    url = f"https://viacep.com.br/ws/{cep}/json/"

    with httpx.Client() as client:
        try:
            response = client.get(url, timeout=10.0)
            response.raise_for_status()
            dados = response.json()

            # ViaCEP retorna {"erro": true} para CEPs inválidos
            if "erro" in dados and dados["erro"]:
                return None

            return {
                "cep": cep,
                "logradouro": dados.get("logradouro", ""),
                "bairro": dados.get("bairro", ""),
                "cidade": dados.get("localidade", ""),
                "estado": dados.get("uf", ""),
            }

        except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
            return None
