# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Estratégias de chunking aplicadas a um edital real
# Seção 3.2 – As cinco estratégias de divisão
# Requisitos: nenhum (biblioteca padrão)
# ============================================================
"""Divide o Edital de Pregão 012/2026 por cinco estratégias e mede o efeito.

Este arquivo também é importado pelos exemplos 03 a 07, que reaproveitam a
classe ``Chunker``. Por isso a demonstração fica protegida por
``if __name__ == "__main__"``.

Cada estratégia devolve uma lista de dicionários com duas chaves:

    texto   o que será convertido em embedding e enviado ao modelo;
    origem  de onde o trecho veio, guardado como metadado.

A distinção importa: a busca vetorial enxerga apenas ``texto``.
"""

import pathlib
import re
from typing import List

# Cabeçalho de seção: "1. DO OBJETO", "11. DOS PRAZOS DE ENTREGA..."
CABECALHO = re.compile(r"^(\d{1,2})\.\s+([A-ZÀ-ÚÇ][A-ZÀ-ÚÇ\s\-,/]+)$")
# Cláusula numerada: "11.1. O prazo de entrega..."
CLAUSULA = re.compile(r"^(\d{1,2}\.\d{1,2})\.\s")
# Palavras que não devem encerrar um rótulo truncado
APOIO = {"de", "da", "do", "das", "dos", "a", "à", "o", "e", "em", "no", "na",
         "para", "por", "com", "ao", "aos"}


def rotulo_do_documento(texto: str) -> str:
    """Extrai do próprio documento uma identificação curta.

    Combina o número do edital, que está no preâmbulo, com o objeto, que está
    na cláusula 1.1. É esse rótulo que a estratégia consciente da estrutura
    injeta em cada chunk.
    """
    numero = re.search(r"EDITAL DE PREGÃO ELETRÔNICO N\. ?([\d/]+)", texto)
    objeto = re.search(r"^1\.1\..*?a aquisição de (.+?),", texto,
                       re.MULTILINE | re.DOTALL)
    numero = f"Edital de Pregão {numero.group(1)}" if numero else "Documento"
    if not objeto:
        return numero
    resumo = objeto.group(1)
    if len(resumo) > 60:                       # mantém o rótulo curto
        resumo = resumo[:60].rsplit(" ", 1)[0]
        while resumo.split()[-1].lower() in APOIO:   # não termina em preposição
            resumo = resumo.rsplit(" ", 1)[0]
    return f"{numero} — {resumo}"


def _curto(rotulo: str) -> str:
    """Versão curta do rótulo, usada nos metadados de origem."""
    return rotulo.split(" — ")[0] if rotulo else "documento"


class Chunker:
    """Cinco estratégias de divisão de documentos administrativos."""

    @staticmethod
    def por_tamanho_fixo(texto: str, rotulo: str = "",
                         tamanho: int = 400, sobreposicao: int = 0) -> List[dict]:
        """Corta o texto a cada N caracteres, ignorando a estrutura."""
        passo = max(1, tamanho - sobreposicao)
        chunks = []
        for inicio in range(0, len(texto), passo):
            trecho = texto[inicio:inicio + tamanho].strip()
            if trecho:
                chunks.append({"texto": trecho,
                               "origem": f"{_curto(rotulo)}, offset {inicio}"})
        return chunks

    @staticmethod
    def por_paragrafos(texto: str, rotulo: str = "") -> List[dict]:
        """Uma cláusula por chunk. Respeita a unidade redacional do edital."""
        chunks = []
        for bloco in texto.split("\n\n"):
            bloco = bloco.strip()
            if not bloco:
                continue
            m = CLAUSULA.match(bloco)
            chunks.append({"texto": bloco,
                           "origem": f"{_curto(rotulo)}, cláusula {m.group(1)}" if m
                                     else f"{_curto(rotulo)}, preâmbulo"})
        return chunks

    @staticmethod
    def por_secoes(texto: str, rotulo: str = "") -> List[dict]:
        """Uma seção numerada inteira por chunk, com todas as suas cláusulas."""
        chunks, titulo, buffer = [], "Preâmbulo", []
        for bloco in texto.split("\n\n"):
            bloco = bloco.strip()
            if not bloco:
                continue
            if CABECALHO.match(bloco) and "\n" not in bloco:
                if buffer:
                    chunks.append({"texto": "\n".join(buffer),
                                   "origem": f"{_curto(rotulo)}, {titulo}"})
                titulo, buffer = bloco, []
            else:
                buffer.append(bloco)
        if buffer:
            chunks.append({"texto": "\n".join(buffer),
                           "origem": f"{_curto(rotulo)}, {titulo}"})
        return chunks

    @staticmethod
    def por_clausula_com_titulo(texto: str, rotulo: str = "") -> List[dict]:
        """Uma cláusula por chunk, prefixada pelo documento e pela seção.

        É a estratégia consciente da estrutura: mantém o chunk pequeno, mas
        devolve ao trecho o contexto que a numeração sozinha não carrega.
        """
        chunks, titulo = [], "Preâmbulo"
        for bloco in texto.split("\n\n"):
            bloco = bloco.strip()
            if not bloco:
                continue
            if CABECALHO.match(bloco) and "\n" not in bloco:
                titulo = bloco
                continue
            c = CLAUSULA.match(bloco)
            chunks.append({
                "texto": f"[{rotulo} | {titulo}]\n{bloco}",
                "origem": f"{_curto(rotulo)}, cláusula {c.group(1)}" if c
                          else f"{_curto(rotulo)}, {titulo}",
            })
        return chunks


ESTRATEGIAS = {
    "fixo_400": lambda t, r="": Chunker.por_tamanho_fixo(t, r, 400, 0),
    "fixo_400_sobrep_80": lambda t, r="": Chunker.por_tamanho_fixo(t, r, 400, 80),
    "paragrafos": Chunker.por_paragrafos,
    "secoes": Chunker.por_secoes,
    "clausula_com_titulo": Chunker.por_clausula_com_titulo,
}


def clausulas_inteiras(texto: str, chunks: List[dict]) -> float:
    """Percentual de cláusulas que sobrevivem inteiras em algum chunk."""
    originais = [b.strip() for b in texto.split("\n\n") if CLAUSULA.match(b.strip())]
    corpos = [c["texto"] for c in chunks]
    intactas = sum(1 for cl in originais if any(cl in c for c in corpos))
    return 100 * intactas / len(originais)


if __name__ == "__main__":
    caminho = pathlib.Path(__file__).parent / "edital_pregao_012_2026.txt"
    edital = caminho.read_text(encoding="utf-8")
    rotulo = rotulo_do_documento(edital)
    print(f"Documento: {caminho.name} — {len(edital)} caracteres")
    print(f"Rótulo extraído: {rotulo}\n")

    print(f"{'Estratégia':<22}{'Chunks':>8}{'Média':>9}{'Maior':>8}"
          f"{'Cláusulas inteiras':>21}")
    print("-" * 68)
    for nome, funcao in ESTRATEGIAS.items():
        chunks = funcao(edital, rotulo)
        tam = [len(c["texto"]) for c in chunks]
        print(f"{nome:<22}{len(chunks):>8}{sum(tam) // len(tam):>9}"
              f"{max(tam):>8}{clausulas_inteiras(edital, chunks):>20.0f}%")

    print("\nA cláusula 11.1 vista por cada estratégia:\n")
    for nome, funcao in ESTRATEGIAS.items():
        achado = next((c for c in funcao(edital, rotulo)
                       if "45 (quarenta e cinco)" in c["texto"]), None)
        corpo = achado["texto"].replace("\n", " ") if achado else "(dividida entre dois chunks)"
        print(f"  {nome}\n    {corpo[:160]}...\n")
