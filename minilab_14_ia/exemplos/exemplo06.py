# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 06: Recuperação híbrida (BM25 + vetorial) e reranking
# Seção 5.1 – Melhorias que valem o esforço
# Requisitos: pip install openai groq numpy python-dotenv
# ============================================================
"""Mostra onde a busca vetorial sozinha falha e o que a recuperação híbrida
resolve.

A busca vetorial acerta o sentido e erra o literal: número de cláusula, código
orçamentário, endereço de e-mail e sigla são justamente o que o embedding
dilui. O BM25, que conta palavras, acerta o literal e erra o sentido. Somar as
duas listas com Reciprocal Rank Fusion aproveita o forte de cada uma.

O reranking usa um modelo de pesos abertos servido pela Groq, com latência
baixa o bastante para entrar no caminho da resposta.
"""

import json
import math
import os
import re
import time
from collections import Counter

from dotenv import load_dotenv
from groq import Groq

from exemplo02 import Chunker, rotulo_do_documento
from exemplo03 import PASTA, embutir, recuperar, normalizar

load_dotenv(PASTA.parent.parent.parent / ".env")
load_dotenv(PASTA / ".env")

groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODELO_RERANK = "openai/gpt-oss-20b"
K = 3


# ------------------------------------------------------------------ BM25
class BM25:
    """Busca lexical clássica, em Python puro. k1 e b são os valores usuais."""

    def __init__(self, documentos: list, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [self.tokenizar(d) for d in documentos]
        self.tamanhos = [len(d) for d in self.docs]
        self.media = sum(self.tamanhos) / len(self.docs)
        n = len(self.docs)
        frequencia = Counter(t for d in self.docs for t in set(d))
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5))
                    for t, f in frequencia.items()}
        self.contagens = [Counter(d) for d in self.docs]

    @staticmethod
    def tokenizar(texto: str) -> list:
        """Mantém pontos e arrobas dentro do token, mas apara as bordas.

        Sem aparar, "11.6." no documento e "11.6" na pergunta viram tokens
        diferentes e a busca lexical perde exatamente o caso em que deveria
        vencer. Em busca lexical, a tokenização decide o resultado.
        """
        cru = re.findall(r"[\w@./-]+", normalizar(texto))
        return [t.strip("./-") for t in cru if t.strip("./-")]

    def pontuar(self, consulta: str) -> list:
        termos = self.tokenizar(consulta)
        notas = []
        for cont, tam in zip(self.contagens, self.tamanhos):
            s = 0.0
            for t in termos:
                if t not in cont:
                    continue
                f = cont[t]
                s += self.idf.get(t, 0) * f * (self.k1 + 1) / (
                    f + self.k1 * (1 - self.b + self.b * tam / self.media))
            notas.append(s)
        return notas


def rrf(*listas, k: int = 60) -> list:
    """Reciprocal Rank Fusion: soma 1/(k + posição) de cada lista de ranking."""
    pontos = {}
    for lista in listas:
        for posicao, indice in enumerate(lista):
            pontos[indice] = pontos.get(indice, 0) + 1 / (k + posicao + 1)
    return sorted(pontos, key=pontos.get, reverse=True)


def reranquear(pergunta: str, candidatos: list, n: int = K) -> list:
    """Reordena candidatos com um modelo de pesos abertos servido pela Groq.

    Duas cautelas são necessárias. O nível gratuito da Groq limita os tokens
    por minuto e por dia, então a chamada é repetida com espera crescente e,
    esgotado o limite, a ordem da fusão é mantida. E o modelo é de raciocínio:
    os tokens de pensamento saem do mesmo limite de saída, de modo que um teto
    apertado devolve conteúdo vazio, conforme a armadilha descrita na Aula 02,
    Seção 9.
    """
    lista = "\n\n".join(f"[{i}] {c['texto'][:300]}" for i, c in enumerate(candidatos))
    pedido = dict(
        model=MODELO_RERANK,
        messages=[{"role": "user", "content":
                   f"Ordene os trechos do mais para o menos útil para responder "
                   f"à pergunta. Responda apenas com um JSON no formato "
                   f'{{"ordem": [n, n, n]}} com os {n} melhores índices.\n\n'
                   f"PERGUNTA: {pergunta}\n\nTRECHOS:\n{lista}"}],
        response_format={"type": "json_object"},
        reasoning_effort="low",
        max_completion_tokens=1500,
    )
    conteudo = ""
    for tentativa in range(5):
        try:
            r = groq.chat.completions.create(**pedido)
            conteudo = r.choices[0].message.content or ""
            break
        except Exception as erro:
            if "rate_limit" in str(erro) and tentativa < 4:
                time.sleep(5 * (tentativa + 1))
                continue
            print(f"    [rerank indisponível: {str(erro)[:70]}]")
            break
    try:
        ordem = json.loads(conteudo)["ordem"]
        escolhidos = [candidatos[i] for i in ordem
                      if isinstance(i, int) and 0 <= i < len(candidatos)][:n]
    except (json.JSONDecodeError, KeyError, TypeError):
        escolhidos = []
    return escolhidos or candidatos[:n]     # sem resposta válida, mantém a ordem


def recall(perguntas: list, obter_trechos) -> float:
    acertos = 0
    for p in perguntas:
        contexto = " ".join(t["texto"] for t in obter_trechos(p))
        acertos += p["trecho_gabarito"] in contexto
    return 100 * acertos / len(perguntas)


if __name__ == "__main__":
    dados = json.loads((PASTA / "perguntas_edital.json").read_text(encoding="utf-8"))
    chunks = []
    for arquivo in dados["acervo"]:
        texto = (PASTA / arquivo).read_text(encoding="utf-8")
        chunks += Chunker.por_clausula_com_titulo(texto, rotulo_do_documento(texto))

    matriz = embutir([c["texto"] for c in chunks])
    bm25 = BM25([c["texto"] for c in chunks])
    print(f"Índice: {len(chunks)} chunks, {len(bm25.idf)} termos distintos\n")

    cache = {}

    def vetorial(p, k=K):
        if p["id"] not in cache:
            cache[p["id"]] = embutir([p["pergunta"]])[0]
        return [c for c, _ in recuperar(cache[p["id"]], matriz, chunks, k)]

    def lexical(p, k=K):
        notas = bm25.pontuar(p["pergunta"])
        ordem = sorted(range(len(notas)), key=lambda i: -notas[i])[:k]
        return [chunks[i] for i in ordem]

    def hibrido(p, k=K):
        if p["id"] not in cache:
            cache[p["id"]] = embutir([p["pergunta"]])[0]
        scores = matriz @ cache[p["id"]]
        rank_vet = sorted(range(len(chunks)), key=lambda i: -scores[i])[:20]
        notas = bm25.pontuar(p["pergunta"])
        rank_lex = sorted(range(len(chunks)), key=lambda i: -notas[i])[:20]
        return [chunks[i] for i in rrf(rank_vet, rank_lex)[:k]]

    def hibrido_rerank(p):
        return reranquear(p["pergunta"], hibrido(p, k=12), K)

    grupos = {
        "perguntas por assunto (12)": dados["perguntas_acervo"],
        "perguntas com termo literal (6)": dados["perguntas_literais"],
    }

    print(f"{'Conjunto':<32}{'Vetorial':>9}{'BM25':>8}{'Híbrido':>9}"
          f"{'Híbr.@12':>10}{'+ rerank':>10}")
    print("-" * 78)
    for nome, perguntas in grupos.items():
        print(f"{nome:<32}{recall(perguntas, vetorial):>8.0f}%"
              f"{recall(perguntas, lexical):>7.0f}%"
              f"{recall(perguntas, hibrido):>8.0f}%"
              f"{recall(perguntas, lambda p: hibrido(p, k=12)):>9.0f}%"
              f"{recall(perguntas, hibrido_rerank):>9.0f}%")

    print("\nOnde a busca vetorial sozinha falhou e o BM25 salvou:")
    for p in dados["perguntas_literais"]:
        so_vetorial = p["trecho_gabarito"] in " ".join(t["texto"] for t in vetorial(p))
        so_lexical = p["trecho_gabarito"] in " ".join(t["texto"] for t in lexical(p))
        if not so_vetorial and so_lexical:
            print(f"  P{p['id']}: {p['pergunta']}")
            print(f"     gabarito: {p['trecho_gabarito']}")

    # ---- Fecho: a pergunta que o pipeline do exemplo 05 recusou -----
    p103 = next(x for x in dados["perguntas_acervo"] if x["id"] == 103)
    print(f"\nA pergunta 103, recusada pelo pipeline do exemplo 05:")
    print(f"  {p103['pergunta']}")
    for nome, obter in [("vetorial", vetorial), ("híbrido", hibrido)]:
        trechos = obter(p103)
        marca = "sim" if p103["trecho_gabarito"] in " ".join(
            t["texto"] for t in trechos) else "NÃO"
        print(f"  {nome:<9} trouxe a cláusula 11.6? {marca}"
              f"   ({', '.join(t['origem'].split(', ')[-1] for t in trechos)})")
