# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: Pipeline RAG mínimo de ponta a ponta com ChromaDB
# Seção 2.3 – O pipeline mínimo, do documento à resposta citada
# Requisitos: pip install openai chromadb numpy python-dotenv
# ============================================================
"""Indexa um edital real e responde perguntas citando a cláusula de origem.

São as quatro etapas do pipeline, na ordem: dividir, indexar, recuperar e
gerar. O banco vetorial é o ChromaDB, apresentado na Aula 11, Seção 4.
"""

import os
import pathlib

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from openai import OpenAI

from exemplo02 import Chunker, rotulo_do_documento

PASTA = pathlib.Path(__file__).parent
load_dotenv(PASTA.parent.parent.parent / ".env")
load_dotenv(PASTA / ".env")

MODELO_EMBEDDING = "text-embedding-3-small"
MODELO_LLM = "gpt-5.6-luna"

INSTRUCAO = """Você é um assistente que responde sobre editais de licitação \
do Estado de Mato Grosso.

Regras invioláveis:
1. Use exclusivamente os trechos numerados abaixo.
2. Cite a fonte entre colchetes ao final de cada afirmação, no formato [1].
3. Se os trechos não contiverem a resposta, escreva apenas: NÃO ENCONTRADO \
nos documentos indexados.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""


class AssistenteEdital:
    """Pipeline RAG mínimo: dividir, indexar, recuperar, gerar."""

    def __init__(self, nome_colecao: str = "editais"):
        self.llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chroma = chromadb.Client()          # em memória, para a aula
        self.colecao = self.chroma.get_or_create_collection(
            name=nome_colecao,
            embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=MODELO_EMBEDDING,
            ),
            metadata={"hnsw:space": "cosine"},
        )

    # ---------- Etapas 1 e 2: dividir e indexar ----------------------
    def indexar(self, caminho: pathlib.Path) -> int:
        texto = caminho.read_text(encoding="utf-8")
        rotulo = rotulo_do_documento(texto)
        chunks = Chunker.por_clausula_com_titulo(texto, rotulo)

        base = self.colecao.count()
        self.colecao.add(
            documents=[c["texto"] for c in chunks],
            metadatas=[{"origem": c["origem"], "arquivo": caminho.name}
                       for c in chunks],
            ids=[f"{caminho.stem}_{base + i}" for i in range(len(chunks))],
        )
        print(f"  {caminho.name}: {len(chunks)} chunks indexados")
        return len(chunks)

    # ---------- Etapa 3: recuperar -----------------------------------
    def recuperar(self, pergunta: str, k: int = 4) -> list:
        r = self.colecao.query(query_texts=[pergunta], n_results=k)
        return [
            {"texto": doc, "origem": meta["origem"],
             "similaridade": 1 - dist}          # Chroma devolve distância
            for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0],
                                       r["distances"][0])
        ]

    # ---------- Etapa 4: gerar ---------------------------------------
    def responder(self, pergunta: str, k: int = 4) -> dict:
        trechos = self.recuperar(pergunta, k)
        contexto = "\n\n".join(
            f"[{i + 1}] ({t['origem']}) {t['texto']}"
            for i, t in enumerate(trechos))

        r = self.llm.chat.completions.create(
            model=MODELO_LLM,
            messages=[{"role": "user",
                       "content": INSTRUCAO.format(contexto=contexto,
                                                   pergunta=pergunta)}],
            max_completion_tokens=400,
            reasoning_effort="none",
        )
        return {"pergunta": pergunta,
                "resposta": r.choices[0].message.content.strip(),
                "fontes": trechos,
                "tokens": r.usage.prompt_tokens + r.usage.completion_tokens}


if __name__ == "__main__":
    assistente = AssistenteEdital()
    print("Indexando o acervo:")
    assistente.indexar(PASTA / "edital_pregao_012_2026.txt")
    assistente.indexar(PASTA / "edital_pregao_008_2026.txt")
    print(f"  total na coleção: {assistente.colecao.count()} chunks\n")

    for pergunta in [
        "Qual é o prazo de entrega dos equipamentos de informática?",
        "Qual o percentual de garantia de execução exigido no pregão 012/2026?",
        "Qual é a alíquota do Imposto sobre Serviços aplicável à contratação?",
    ]:
        r = assistente.responder(pergunta)
        print(f"P: {r['pergunta']}")
        print(f"R: {r['resposta']}")
        for i, f in enumerate(r["fontes"], 1):
            print(f"   [{i}] sim. {f['similaridade']:.3f} — {f['origem']}")
        print(f"   ({r['tokens']} tokens)\n")
