# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Experimento — qual estratégia de chunking responde melhor
# Seção 3.3 – Medindo o efeito do chunking sobre a resposta
# Requisitos: pip install openai numpy python-dotenv
# ============================================================
"""Compara cinco estratégias de chunking com o mesmo conjunto de perguntas.

O experimento roda em duas rodadas, porque a resposta muda com o tamanho
do acervo:

  rodada 1  um único edital indexado, perguntas diretas;
  rodada 2  dois editais parecidos indexados juntos, perguntas que não
            citam o número do edital, apenas o assunto.

Três números são medidos para cada estratégia:

  recall@3   fração de perguntas cujo trecho-gabarito aparece íntegro em
             algum dos três chunks recuperados — mede a recuperação;
  acerto     fração de respostas que contêm o valor correto — mede o
             resultado que chega ao usuário;
  contexto   média de tokens enviados ao modelo por pergunta — mede o custo.

Execução: python exemplo03.py   (cerca de 6 minutos e US$ 0,02)
"""

import json
import os
import pathlib
import time
import unicodedata

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from exemplo02 import ESTRATEGIAS, rotulo_do_documento

PASTA = pathlib.Path(__file__).parent
load_dotenv(PASTA.parent.parent.parent / ".env")
load_dotenv(PASTA / ".env")

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODELO_EMBEDDING = "text-embedding-3-small"
MODELO_LLM = "gpt-5.6-luna"
K = 3

PRECO = {"entrada": 0.20 / 1e6, "saida": 1.20 / 1e6, "embedding": 0.02 / 1e6}

INSTRUCAO = """Você responde perguntas sobre editais de licitação usando \
APENAS os trechos fornecidos. Responda em uma frase. Se os trechos não \
contiverem a informação, responda exatamente NÃO ENCONTRADO.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""

tokens_embedding = 0


def normalizar(s: str) -> str:
    """Remove acentos e caixa, para comparar resposta com gabarito."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def embutir(textos: list) -> np.ndarray:
    """Converte uma lista de textos em uma matriz de vetores normalizados."""
    global tokens_embedding
    vetores = []
    for i in range(0, len(textos), 128):
        r = cliente.embeddings.create(model=MODELO_EMBEDDING, input=textos[i:i + 128])
        vetores += [d.embedding for d in r.data]
        tokens_embedding += r.usage.total_tokens
    m = np.array(vetores, dtype=np.float32)
    return m / np.linalg.norm(m, axis=1, keepdims=True)


def recuperar(consulta_vec, matriz, chunks, k=K):
    """Busca por similaridade de cosseno. Vetores já normalizados."""
    scores = matriz @ consulta_vec
    return [(chunks[i], float(scores[i])) for i in np.argsort(-scores)[:k]]


def responder(pergunta: str, recuperados: list):
    contexto = "\n\n".join(f"[{i + 1}] {c['texto']}"
                           for i, (c, _) in enumerate(recuperados))
    r = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=[{"role": "user",
                   "content": INSTRUCAO.format(contexto=contexto, pergunta=pergunta)}],
        max_completion_tokens=300,
        reasoning_effort="none",
    )
    return r.choices[0].message.content.strip(), r.usage


def avaliar(chunks: list, perguntas: list) -> dict:
    matriz = embutir([c["texto"] for c in chunks])
    consultas = embutir([p["pergunta"] for p in perguntas])

    acertos = recall = entrada = saida = 0
    falhas = []
    for p, vec in zip(perguntas, consultas):
        recuperados = recuperar(vec, matriz, chunks)
        contexto_bruto = " ".join(c["texto"] for c, _ in recuperados)
        achou = p["trecho_gabarito"] in contexto_bruto
        recall += achou

        resposta, uso = responder(p["pergunta"], recuperados)
        entrada += uso.prompt_tokens
        saida += uso.completion_tokens
        certo = any(normalizar(ch) in normalizar(resposta) for ch in p["chaves"])
        acertos += certo
        if not certo:
            falhas.append((p["id"], p["clausula"], achou, resposta.replace("\n", " ")[:100]))

    n = len(perguntas)
    return {"chunks": len(chunks), "recall": 100 * recall / n,
            "acerto": 100 * acertos / n, "contexto": entrada / n,
            "custo": entrada * PRECO["entrada"] + saida * PRECO["saida"],
            "falhas": falhas}


def imprimir(titulo: str, resultados: dict):
    print(f"\n{titulo}")
    print(f"{'Estratégia':<22}{'Chunks':>7}{'recall@3':>10}{'Acerto':>9}"
          f"{'Contexto':>10}{'Custo':>10}")
    print("-" * 68)
    for nome, r in resultados.items():
        print(f"{nome:<22}{r['chunks']:>7}{r['recall']:>9.0f}%{r['acerto']:>8.0f}%"
              f"{r['contexto']:>9.0f}t{r['custo']:>10.5f}")
    print("\nRespostas erradas:")
    for nome, r in resultados.items():
        if not r["falhas"]:
            print(f"  {nome}: nenhuma")
        for pid, cl, achou, resp in r["falhas"]:
            origem = "trecho certo recuperado" if achou else "trecho certo NÃO recuperado"
            print(f"  {nome}: pergunta {pid} (cláusula {cl}) — {origem} — {resp}")


def carregar(nome: str):
    texto = (PASTA / nome).read_text(encoding="utf-8")
    return texto, rotulo_do_documento(texto)


if __name__ == "__main__":
    dados = json.loads((PASTA / "perguntas_edital.json").read_text(encoding="utf-8"))
    edital_012, rotulo_012 = carregar("edital_pregao_012_2026.txt")
    edital_008, rotulo_008 = carregar("edital_pregao_008_2026.txt")

    # ---------- Rodada 1: um documento -------------------------------
    perguntas1 = [p for p in dados["perguntas"] if p["respondivel"]]
    print(f"RODADA 1 — um edital ({len(edital_012)} caracteres), "
          f"{len(perguntas1)} perguntas diretas, k = {K}, modelo {MODELO_LLM}")
    r1 = {}
    for nome, funcao in ESTRATEGIAS.items():
        t0 = time.time()
        r1[nome] = avaliar(funcao(edital_012, rotulo_012), perguntas1)
        print(f"  {nome:<22} {time.time() - t0:5.1f} s")
    imprimir("RESULTADO DA RODADA 1", r1)

    # ---------- Rodada 2: dois documentos parecidos ------------------
    perguntas2 = dados["perguntas_acervo"]
    print(f"\n\nRODADA 2 — dois editais ({len(edital_012) + len(edital_008)} "
          f"caracteres), {len(perguntas2)} perguntas por assunto, k = {K}")
    r2 = {}
    for nome, funcao in ESTRATEGIAS.items():
        t0 = time.time()
        chunks = funcao(edital_012, rotulo_012) + funcao(edital_008, rotulo_008)
        r2[nome] = avaliar(chunks, perguntas2)
        print(f"  {nome:<22} {time.time() - t0:5.1f} s")
    imprimir("RESULTADO DA RODADA 2", r2)

    print(f"\nTokens de embedding no experimento: {tokens_embedding} "
          f"(US$ {tokens_embedding * PRECO['embedding']:.5f})")
