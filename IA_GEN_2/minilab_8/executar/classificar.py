import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.configuracao import (
    NOME_CLASSIFICADOR,
    PASTA_DADOS,
    PASTA_RESULTADOS,
    RAIZ,
)

# Categorias lidas no Playground na Parte 3, na mesma ordem de dados/mensagens.json.
CATEGORIAS_PLAYGROUND = [
    "INCIDENTE",
    "REQUISICAO",
    "DUVIDA",
    "REQUISICAO",
    "INCIDENTE",
]


def ler_categoria(texto: str) -> tuple[str, str]:
    # O prompt do classificador põe só a categoria na primeira linha, para a API ler sem ambiguidade.
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    if not linhas:
        return "", ""
    categoria = linhas[0].strip("*.").split()[0].upper()
    justificativa = " ".join(linhas[1:])
    return categoria, justificativa


def classificar_pela_api(mensagem: str) -> str:
    # A chamada passa por cliente_api.py, o cliente da Seção 7.2, e não pelo Playground.
    comando = [
        sys.executable,
        str(RAIZ / "exemplos" / "cliente_api.py"),
        "rodar",
        NOME_CLASSIFICADOR,
        mensagem,
    ]
    concluido = subprocess.run(comando, check=True, capture_output=True, text=True, cwd=RAIZ)
    return concluido.stdout.strip()


def principal() -> None:
    mensagens = json.loads((PASTA_DADOS / "mensagens.json").read_text())
    if len(mensagens) != len(CATEGORIAS_PLAYGROUND):
        raise SystemExit("A bateria e as categorias do Playground não têm o mesmo tamanho.")

    linhas_tabela = []
    blocos = []
    for indice, item in enumerate(mensagens, start=1):
        resposta = classificar_pela_api(item["texto"])
        categoria_api, justificativa = ler_categoria(resposta)
        categoria_playground = CATEGORIAS_PLAYGROUND[indice - 1]
        coincidiram = categoria_api == categoria_playground
        veredito = "sim" if coincidiram else "não"
        linhas_tabela.append(
            f"| {indice} | {item['texto']} | {categoria_playground} | {categoria_api} | {veredito} |"
        )
        blocos.append(
            "\n".join(
                [
                    f"### {indice}",
                    "",
                    item["texto"],
                    "",
                    f"Playground: {categoria_playground}. API: {categoria_api}.",
                    f"Justificativa da API: {justificativa or 'sem segunda linha.'}",
                    f"Categoria esperada em dados/mensagens.json: {item['categoria_esperada']}.",
                ]
            )
        )
        print(f"{indice} playground={categoria_playground} api={categoria_api} {veredito}")

    tabela = "\n".join(
        [
            "# Comparação entre Playground e API",
            "",
            "As cinco mensagens de `dados/mensagens.json` foram enviadas por `exemplos/cliente_api.py` ao fluxo Classificador TI MTI. A categoria da API é a primeira linha da resposta. A do Playground é a da Parte 3, em `resultados/bateria_classificador.md`.",
            "",
            "| n | Mensagem | Playground | API | Coincidiram |",
            "| --- | --- | --- | --- | --- |",
            *linhas_tabela,
            "",
            *blocos,
            "",
        ]
    )
    destino = PASTA_RESULTADOS / "comparacao_api.md"
    destino.write_text(tabela)
    print(destino)


if __name__ == "__main__":
    principal()
