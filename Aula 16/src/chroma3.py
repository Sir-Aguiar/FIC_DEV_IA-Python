from pathlib import Path
import chromadb

VECTORIAL_STORE_PATH = Path(__file__).parent / "database" / "chroma_db3"

# ── Modo 1: Efêmero (em memória - apenas para testes rápidos) ──
client_mem = chromadb.EphemeralClient()

# ── Modo 2: Persistente (salva em disco com SQLite + HNSW) ─────
client = chromadb.PersistentClient(path=VECTORIAL_STORE_PATH)

# ── Criando ou abrindo uma coleção ─────────────────────────────
# get_or_create_collection: cria se não existir, abre se já existir
colecao = client.get_or_create_collection(
    name="documentos_juridicos",
    metadata={
        "hnsw:space": "cosine",  # métricas suportadas: cosine, l2 ou ip
        "description": "Chunks de contratos e certidoes"
    }
)

print(f"Coleção ativa: {colecao.name}")
print(f"Documentos armazenados inicialmente: {colecao.count()}")

# ── (Opcional) Inserindo dados de exemplo para teste ───────────
# O ChromaDB gera os embeddings automaticamente usando o modelo default
colecao.add(
    documents=[
        "Cláusula 1: O presente contrato tem por objeto a prestação de serviços de TI.",
        "Cláusula 2: O pagamento será efetuado até o quinto dia útil de cada mês.",
        "Certidão negativa de débitos trabalhistas emitida em 2026."
    ],
    metadatas=[
        {"tipo": "contrato", "autor": "juridico"},
        {"tipo": "contrato", "autor": "financeiro"},
        {"tipo": "certidao", "autor": "rh"}
    ],
    ids=["doc_1", "doc_2", "doc_3"]
)

print(f"Documentos após inserção: {colecao.count()}")

# ── Listando todas as coleções no banco ────────────────────────
print("\nColeções no banco:")
for col in client.list_collections():
    print(f"  - {col.name}")

# ── Realizando uma busca por similaridade semântica ────────────
resultado = colecao.query(
    query_texts=["qual o prazo para pagamento dos serviços?"],
    n_results=1
)

print("\nResultado da busca semântica:")
print(f"Texto recuperado: {resultado['documents'][0][0]}")
print(f"Distância (cosseno): {resultado['distances'][0][0]:.4f}")

# ── Apagando uma coleção (irreversível) ────────────────────────
# client.delete_collection('documentos_juridicos')