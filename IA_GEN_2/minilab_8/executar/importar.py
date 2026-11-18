import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.cliente import importar
from src.configuracao import PASTA_FLUXOS


def principal() -> None:
    # Parte 5: cada JSON da pasta do setor é enviado ao servidor, sem escolher um a um.
    for caminho in sorted(PASTA_FLUXOS.glob("*.json")):
        criado = importar(caminho)
        print(f"importado: {criado.get('name')} ({criado.get('id')})")


if __name__ == "__main__":
    principal()
