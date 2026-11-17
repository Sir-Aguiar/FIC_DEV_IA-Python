"""Inspeciona as memórias do atendimento e imprime o veredito da Parte 3.

A varredura e o critério de necessidade ficam em src/memorias.py. Este script
chama a função e mostra a tabela gravada em resultados/tabela_necessidade.md.
"""

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.configuracao import ARQUIVO_TABELA_NECESSIDADE
from src.memorias import inspecionar
from src.roteiro import carregar


def principal() -> None:
    resultado = inspecionar(carregar())
    print(ARQUIVO_TABELA_NECESSIDADE.read_text(encoding="utf-8"))
    excedentes = sum(1 for item in resultado["memorias"] if not item["necessaria"])
    print(
        f"{len(resultado['memorias'])} memória(s) em agno_memories, "
        f"{excedentes} excede(m) a finalidade."
    )


if __name__ == "__main__":
    principal()
