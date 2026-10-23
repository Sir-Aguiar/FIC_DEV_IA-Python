# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: Extração de PDF com rastreabilidade de página
# Seção 3 – Extração de Texto com Rastreabilidade
# Requisitos: pip install pymupdf
# Execução: python exemplo01.py edital_exemplo.pdf
# ============================================================
"""Extrai o texto de um PDF preservando a origem de cada trecho.

Este exemplo não usa API alguma e, portanto, não consome créditos. Ele
existe para deixar claro que a rastreabilidade do assistente começa
aqui: se a página de origem não for registrada na extração, nenhuma
etapa posterior conseguirá recuperá-la.
"""

import sys
from typing import Dict, List

import pymupdf


def extrair_paginas(caminho_pdf: str) -> List[Dict]:
    """Extrai o texto de cada página, descartando páginas sem texto."""
    documento = pymupdf.open(caminho_pdf)
    paginas = []

    for indice in range(len(documento)):
        texto = documento[indice].get_text().strip()
        if texto:
            paginas.append(
                {
                    "pagina": indice + 1,
                    "texto": texto,
                    "caracteres": len(texto),
                }
            )

    total_paginas = len(documento)
    documento.close()

    if not paginas:
        raise ValueError(
            f"Nenhum texto extraído de {caminho_pdf}. "
            "O arquivo provavelmente é digitalizado (imagem) e exige OCR — "
            "ver Aula 06."
        )

    if len(paginas) < total_paginas:
        vazias = total_paginas - len(paginas)
        print(f"[aviso] {vazias} página(s) sem texto foram ignoradas.")

    return paginas


def dividir_em_trechos(
    paginas: List[Dict],
    tamanho: int = 600,
    sobreposicao: int = 100,
) -> List[Dict]:
    """Divide cada página em trechos, mantendo a referência de origem.

    A divisão nunca atravessa a fronteira entre páginas. Isso custa
    alguns trechos a mais, mas garante que todo trecho indexado tenha
    uma única página de origem — condição para citar a fonte sem
    ambiguidade.
    """
    trechos = []
    contador = 0

    for pagina_info in paginas:
        texto = pagina_info["texto"]
        pagina = pagina_info["pagina"]
        inicio = 0

        while inicio < len(texto):
            fim = min(inicio + tamanho, len(texto))

            # Preferir o fim de uma sentença, desde que ele esteja na
            # segunda metade do trecho (evita fatias muito curtas).
            if fim < len(texto):
                ponto = texto.rfind(".", inicio + tamanho // 2, fim)
                if ponto != -1:
                    fim = ponto + 1

            conteudo = texto[inicio:fim].strip()
            if conteudo:
                trechos.append(
                    {
                        "id": f"p{pagina}_t{contador}",
                        "texto": conteudo,
                        "pagina": pagina,
                        "posicao": inicio,
                    }
                )
                contador += 1

            if fim >= len(texto):
                break
            inicio = max(inicio + 1, fim - sobreposicao)

    return trechos


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else "edital_exemplo.pdf"

    print(f"=== Extração: {caminho} ===\n")
    paginas = extrair_paginas(caminho)
    for pagina in paginas:
        amostra = pagina["texto"][:70].replace("\n", " ")
        print(f"Página {pagina['pagina']} ({pagina['caracteres']} chars): {amostra}...")

    print("\n=== Trechos (tamanho=600, sobreposição=100) ===\n")
    trechos = dividir_em_trechos(paginas)
    for trecho in trechos:
        amostra = trecho["texto"][:60].replace("\n", " ")
        print(f"[{trecho['id']}] p.{trecho['pagina']} pos {trecho['posicao']}: {amostra}...")

    print(f"\nTotal: {len(trechos)} trechos em {len(paginas)} páginas.")


if __name__ == "__main__":
    main()
