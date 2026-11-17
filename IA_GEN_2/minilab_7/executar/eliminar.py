"""Executa a eliminação da Parte 4 e imprime o que restou no banco.

A rotina está em src/eliminacao.py. Este script chama a função e mostra a
contagem e a resposta registrada em resultados/eliminacao.md.
"""

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.configuracao import ARQUIVO_ELIMINACAO
from src.eliminacao import eliminar
from src.roteiro import carregar


def principal() -> None:
    resultado = eliminar(carregar())
    print(ARQUIVO_ELIMINACAO.read_text(encoding="utf-8"))
    print("Tabelas do item 9:", ", ".join(resultado["tabelas_do_item_9"]) or "nenhuma")
    print("Nada restou." if resultado["nada_restou"] else "Ainda há registro do titular.")


if __name__ == "__main__":
    principal()
