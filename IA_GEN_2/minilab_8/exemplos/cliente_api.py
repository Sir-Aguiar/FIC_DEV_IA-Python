import sys
from pathlib import Path

# O comando é executado como arquivo; a raiz do minilab precisa entrar no caminho.
RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.cliente import apagar, importar, listar, rodar


def principal() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python exemplos/cliente_api.py listar|importar|rodar|apagar")

    comando = sys.argv[1]
    if comando == "listar":
        for fluxo in listar():
            print(f"{fluxo.get('name')} ({fluxo.get('id')})")
        return

    if comando == "importar":
        criado = importar(Path(sys.argv[2]))
        print(f"importado: {criado.get('name')} ({criado.get('id')})")
        return

    if comando == "rodar":
        # A saída é só o texto da mensagem, para o classificar.py ler a primeira linha.
        print(rodar(sys.argv[2], sys.argv[3]))
        return

    if comando == "apagar":
        removido = apagar(sys.argv[2])
        print(f"apagado: {removido.get('name', sys.argv[2])}")
        return

    raise SystemExit(f"Comando desconhecido: {comando}")


if __name__ == "__main__":
    principal()
