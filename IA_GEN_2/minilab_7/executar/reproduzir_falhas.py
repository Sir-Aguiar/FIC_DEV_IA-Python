"""Reproduz o vazamento da Seção 5.1 e imprime o que o segundo cidadão recebeu.

A comparação está em src/falhas.py. Este script chama a função e mostra o
registro gravado em resultados/vazamento.md.
"""

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.configuracao import ARQUIVO_VAZAMENTO
from src.falhas import reproduzir


def principal() -> None:
    resultado = reproduzir()
    print(ARQUIVO_VAZAMENTO.read_text(encoding="utf-8"))
    print(
        "Isolado vazou?" ,
        "sim" if resultado["isolado"]["vazou"] else "não",
        "· guichê vazou?",
        "sim" if resultado["guiche"]["vazou"] else "não",
    )


if __name__ == "__main__":
    principal()
