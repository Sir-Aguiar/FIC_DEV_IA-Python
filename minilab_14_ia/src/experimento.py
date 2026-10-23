# ============================================================
# Experimento — qual estratégia de chunking responde melhor
# Acervo: Regimento Interno da MTI (5 subseções)
# Embedding: Gemini  |  Chat: Groq
# Execução: python src/experimento.py
# ============================================================
"""Compara estratégias de chunking com o mesmo conjunto de perguntas.

Rodada 1  uma única subseção indexada (Conselho de Administração);
Rodada 2  as cinco subseções juntas (incluindo duas semelhantes:
          Conselho de Administração e Conselho Fiscal).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
import unicodedata

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI

from chunking import ESTRATEGIAS, chunkar_acervo

PASTA = pathlib.Path(__file__).parent
RAIZ = PASTA.parent
load_dotenv(RAIZ / ".env")
load_dotenv(PASTA / ".env")

IDS_ACERVO = [
    "caracterizacao",
    "objetivos",
    "conselho-administracao",
    "conselho-fiscal",
    "gestao-pessoas",
]
ID_RODADA_1 = "conselho-administracao"
K = 3
MODELO_EMBEDDING = "gemini-embedding-001"
MODELO_LLM = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
LIMITE_EMBED = 6000

gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
groq = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

INSTRUCAO = """Você responde perguntas sobre o Regimento Interno da MTI \
usando APENAS os trechos fornecidos. Responda em uma frase. Se os trechos \
não contiverem a informação, responda exatamente NÃO ENCONTRADO.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""

chamadas_embedding = 0


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def plano(s: str) -> str:
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s).strip()
    return normalizar(s)


def chaves_da(p: dict) -> list[str]:
    if p.get("chaves"):
        return p["chaves"]
    if not p.get("no_acervo", True):
        return ["nao encontrado", "não encontrado"]
    return [p["chave_esperada"]]


def _com_retry(fn, tentativas: int = 6):
    ultimo = None
    for i in range(tentativas):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
            status = getattr(exc, "status_code", None)
            if status in {400, 401, 403, 404}:
                raise
            time.sleep(min(2**i, 20))
    raise ultimo


def embutir(textos: list[str], task_type: str) -> np.ndarray:
    """Embeddings Gemini, um lote por vez, vetores L2-normalizados."""
    global chamadas_embedding
    vetores = []
    for i in range(0, len(textos), 8):
        lote = [t[:LIMITE_EMBED] for t in textos[i : i + 8]]

        def _chamar(lote=lote):
            return gemini.models.embed_content(
                model=MODELO_EMBEDDING,
                contents=lote,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=768,
                ),
            )

        r = _com_retry(_chamar)
        chamadas_embedding += 1
        embs = r.embeddings
        if len(embs) == 1 and len(lote) > 1:
            for texto in lote:
                r1 = _com_retry(
                    lambda t=texto: gemini.models.embed_content(
                        model=MODELO_EMBEDDING,
                        contents=t,
                        config=types.EmbedContentConfig(
                            task_type=task_type,
                            output_dimensionality=768,
                        ),
                    )
                )
                chamadas_embedding += 1
                vetores.append(r1.embeddings[0].values)
        else:
            vetores += [e.values for e in embs]
    m = np.array(vetores, dtype=np.float32)
    normas = np.linalg.norm(m, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return m / normas


def recuperar(consulta_vec, matriz, chunks, k=K):
    scores = matriz @ consulta_vec
    return [(chunks[i], float(scores[i])) for i in np.argsort(-scores)[:k]]


def responder(pergunta: str, recuperados: list):
    contexto = "\n\n".join(
        f"[{i + 1}] {c['texto']}" for i, (c, _) in enumerate(recuperados)
    )

    def _chamar():
        return groq.chat.completions.create(
            model=MODELO_LLM,
            messages=[
                {
                    "role": "user",
                    "content": INSTRUCAO.format(
                        contexto=contexto, pergunta=pergunta
                    ),
                }
            ],
            max_tokens=300,
            temperature=0,
        )

    r = _com_retry(_chamar)
    texto = (r.choices[0].message.content or "").strip()
    return texto, r.usage


def avaliar(chunks: list, perguntas: list) -> dict:
    matriz = embutir([c["texto"] for c in chunks], "RETRIEVAL_DOCUMENT")
    consultas = embutir([p["pergunta"] for p in perguntas], "QUESTION_ANSWERING")

    acertos = recall = n_recall = entrada = saida = 0
    falhas = []
    for p, vec in zip(perguntas, consultas):
        recuperados = recuperar(vec, matriz, chunks)
        contexto_bruto = " ".join(c["texto"] for c, _ in recuperados)
        gabarito = p.get("trecho_gabarito") or ""
        achou = bool(gabarito) and plano(gabarito) in plano(contexto_bruto)
        if gabarito:
            n_recall += 1
            recall += int(achou)

        resposta, uso = responder(p["pergunta"], recuperados)
        entrada += uso.prompt_tokens or 0
        saida += uso.completion_tokens or 0
        certo = any(plano(ch) in plano(resposta) for ch in chaves_da(p))
        acertos += int(certo)
        if not certo:
            rotulo = p.get("documento") or p.get("tipo") or "?"
            falhas.append(
                (p["id"], rotulo, achou, resposta.replace("\n", " ")[:120])
            )

    n = len(perguntas)
    return {
        "chunks": len(chunks),
        "recall": 100 * recall / n_recall if n_recall else 0.0,
        "acerto": 100 * acertos / n,
        "contexto": entrada / n if n else 0.0,
        "falhas": falhas,
    }


def imprimir(titulo: str, resultados: dict):
    print(f"\n{titulo}")
    print(
        f"{'Estratégia':<22}{'Chunks':>7}{'recall@3':>10}{'Acerto':>9}"
        f"{'Contexto':>10}"
    )
    print("-" * 58)
    for nome, r in resultados.items():
        print(
            f"{nome:<22}{r['chunks']:>7}{r['recall']:>9.0f}%"
            f"{r['acerto']:>8.0f}%{r['contexto']:>9.0f}t"
        )
    print("\nRespostas erradas:")
    for nome, r in resultados.items():
        if not r["falhas"]:
            print(f"  {nome}: nenhuma")
            continue
        for pid, cl, achou, resp in r["falhas"]:
            origem = (
                "trecho certo recuperado"
                if achou
                else "trecho certo NÃO recuperado"
            )
            print(f"  {nome}: pergunta {pid} ({cl}) — {origem} — {resp}")


def carregar_secoes() -> dict[str, dict]:
    dados = json.loads((PASTA / "data" / "subsecoes.json").read_text(encoding="utf-8"))
    return {s["id"]: s for s in dados["secoes"]}


def serializar(resultados: dict) -> dict:
    return {
        nome: {k: v for k, v in r.items() if k != "falhas"}
        | {
            "falhas": [
                {"id": a, "doc": b, "recall": c, "resposta": d}
                for a, b, c, d in r["falhas"]
            ]
        }
        for nome, r in resultados.items()
    }


def main() -> None:
    secoes = carregar_secoes()
    perguntas = json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8"))[
        "perguntas"
    ]
    respondiveis = [p for p in perguntas if p.get("no_acervo")]
    perguntas1 = [p for p in respondiveis if p.get("documento") == ID_RODADA_1]

    print(
        f"RODADA 1 — {secoes[ID_RODADA_1]['titulo']}, {len(perguntas1)} perguntas "
        f"diretas, k = {K}, embedding {MODELO_EMBEDDING}, chat {MODELO_LLM}"
    )
    r1 = {}
    for nome, funcao in ESTRATEGIAS.items():
        t0 = time.time()
        chunks = chunkar_acervo([secoes[ID_RODADA_1]], funcao)
        r1[nome] = avaliar(chunks, perguntas1)
        print(f"  {nome:<22} {time.time() - t0:5.1f} s  ({len(chunks)} chunks)")
    imprimir("RESULTADO DA RODADA 1", r1)

    acervo = [secoes[i] for i in IDS_ACERVO]
    print(
        f"\n\nRODADA 2 — {len(acervo)} subseções, {len(perguntas)} perguntas "
        f"(10 no acervo + 4 fora), k = {K}"
    )
    r2 = {}
    for nome, funcao in ESTRATEGIAS.items():
        t0 = time.time()
        chunks = chunkar_acervo(acervo, funcao)
        r2[nome] = avaliar(chunks, perguntas)
        print(f"  {nome:<22} {time.time() - t0:5.1f} s  ({len(chunks)} chunks)")
    imprimir("RESULTADO DA RODADA 2", r2)

    saida = PASTA / "data" / "resultado_experimento.json"
    saida.write_text(
        json.dumps(
            {
                "modelo_embedding": MODELO_EMBEDDING,
                "modelo_llm": MODELO_LLM,
                "k": K,
                "chamadas_embedding": chamadas_embedding,
                "rodada_1": serializar(r1),
                "rodada_2": serializar(r2),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados gravados em {saida}")


if __name__ == "__main__":
    main()
