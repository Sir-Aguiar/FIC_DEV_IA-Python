from pathlib import Path
import chromadb

# Modo 1: Efêmero (apenas para testes)
client_mem = chromadb.EphemeralClient()

# Modo 2: Persistente (salva dados em disco)
# ChromaDB cria automaticamente os arquivos necessários

VECTOR_STORE_PATH = Path(__file__).parent / "database" / "chroma_db"

client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)

# Criando coleção

collection = client.get_or_create_collection(
    name="documentos_juridicos",
    metadata={
        "hnsw:space": "cosine",  # Métrica de distância: cosine, 12 ou ip
        "description": "Chunks de contratos e certidoes",
    },
)

print(f"Coleção criada: {collection.name}")
print(f"Documentos armazenados: {collection.count()}")


# ── Listando todas as coleções no banco ─────────────────────
for col in client.list_collections():
    print(f"  - {col.name}")

# ── Apagando uma coleção (irreversível) ─────────────────────
# client.delete_collection('nome_da_colecao')
