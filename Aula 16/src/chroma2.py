from pathlib import Path
import chromadb


VECTORIAL_STORE_PATH = Path(__file__).parent / "database" / "chroma_db2"


client = chromadb.PersistentClient(path=VECTORIAL_STORE_PATH)
colecao = client.get_or_create_collection(
    name="exemplos", metadata={"hnsw:space": "cosine"}
)

# ── Inserção em lote (recomendada) ──────────────────────────
colecao.add(
    ids=[
        "doc1_chunk0",
        "doc1_chunk1",
        "doc1_chunk2",
        "doc2_chunk0",
    ],
    documents=[
        "O contrato de locação foi assinado entre as partes em março de 2024.",
        "O valor do aluguel mensal é de R$ 2.500,00 com reajuste anual pelo IGPM.",
        "Em caso de rescisão antecipada, aplica-se multa de três aluguéis.",
        "A procuração foi outorgada com poderes amplos e gerais ao advogado.",
    ],
    metadatas=[
        {"arquivo": "contrato_locacao.pdf", "pagina": 1, "tipo": "contrato"},
        {"arquivo": "contrato_locacao.pdf", "pagina": 1, "tipo": "contrato"},
        {"arquivo": "contrato_locacao.pdf", "pagina": 2, "tipo": "contrato"},
        {"arquivo": "procuracao.pdf", "pagina": 1, "tipo": "procuracao"},
    ],
    # embeddings=None  -> ChromaDB gera automaticamente se embedding_function configurada
    # embeddings=[[...], [...], ...]  -> fornecer manualmente (nossa abordagem)
)

print(f"Total na coleção: {colecao.count()}")  # 4

# ── Verificando se um ID já existe (evitar duplicatas) ───────
existentes = colecao.get(ids=["doc1_chunk0"])
if existentes["ids"]:
    print("ID já existe — não reinserindo")
