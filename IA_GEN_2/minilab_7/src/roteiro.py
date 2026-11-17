"""Carrega o roteiro da Parte 1 e confere o gabarito de cada verificação.

A conferência olha o texto em minúsculas e ignora asteriscos de markdown. O
acerto depende do trecho pedido em deve_conter, não da formatação da resposta.
"""

import json

from src.configuracao import ARQUIVO_ROTEIRO


def carregar(caminho=ARQUIVO_ROTEIRO) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def conferir(conteudo: str, verificacao: dict) -> bool:
    """True quando a resposta contém cada trecho exigido pelo turno."""

    texto = str(conteudo).lower().replace("*", "")
    return all(trecho.lower() in texto for trecho in verificacao["deve_conter"])
