from pathlib import Path

import chromadb

VECTORIAL_STORE_PATH = Path(__file__).parent / "database" / "chroma_db4"

client = chromadb.PersistentClient(path=VECTORIAL_STORE_PATH)
colecao = client.get_or_create_collection(
    name="exemplos", metadata={"hnsw:space": "cosine"}
)

# ── Query básica por similaridade semântica ──────────────────
# query_texts: lista de perguntas em linguagem natural
# n_results: quantidade de vizinhos mais próximos a retornar
# include: quais campos projetar no dicionário de resposta
resultado = colecao.query(
    query_texts=["Qual o valor do aluguel e o reajuste?"],
    n_results=3,
    include=["documents", "metadatas", "distances"],
)

# ── Estrutura do resultado (dicionário com listas aninhadas) ──
print("=== Busca Semântica Geral ===")
for i, (doc, meta, dist) in enumerate(
    zip(resultado["documents"][0], resultado["metadatas"][0], resultado["distances"][0])
):
    print(f"--- Resultado {i+1} (distância cosseno: {dist:.4f}) ---")
    print(
        f'Arquivo: {meta["arquivo"]} | Página: {meta["pagina"]} | Tipo: {meta["tipo"]}'
    )
    print(f"Texto recuperado: {doc}")
    print()

# ── Query com filtro de metadados (where) ─────────────────────
# Restringe a busca apenas para chunks marcados como 'contrato'
resultado_filtrado = colecao.query(
    query_texts=["Qual o valor do aluguel?"],
    n_results=2,
    where={"tipo": "contrato"},
    include=["documents", "distances"],
)

print("=== Busca com Filtro de Metadados (tipo: contrato) ===")
for doc, dist in zip(
    resultado_filtrado["documents"][0], resultado_filtrado["distances"][0]
):
    print(f"[{dist:.4f}] {doc}")
print()

# ── Query com filtro de conteúdo (where_document) ─────────────
# Combina busca semântica com presença obrigatória do termo 'aluguel'
resultado_conteudo = colecao.query(
    query_texts=["Existe previsão de multa rescisória?"],
    n_results=2,
    where_document={"$contains": "aluguel"},
    include=["documents", "distances"],
)

print("=== Busca com Filtro de Conteúdo ($contains: aluguel) ===")
for doc, dist in zip(
    resultado_conteudo["documents"][0], resultado_conteudo["distances"][0]
):
    print(f"[{dist:.4f}] {doc}")
