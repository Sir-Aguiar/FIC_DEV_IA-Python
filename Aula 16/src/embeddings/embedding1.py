import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Criar a embedding function integrada ao ChromaDB
emb_fn = SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2", normalize_embeddings=True
)

# Associar à coleção — ChromaDB usa automaticamente em add() e query()
client = chromadb.PersistentClient(path="./banco")
colecao = client.get_or_create_collection(
    name="docs_com_embedding_fn",
    embedding_function=emb_fn,
    metadata={"hnsw:space": "cosine"},
)

# add() sem embeddings= — ChromaDB chama emb_fn(documents) automaticamente
colecao.add(
    ids=["chunk1", "chunk2"],
    documents=[
        "O contrato de locação foi assinado em março.",
        "O valor mensal é de R$ 2.500,00.",
    ],
    metadatas=[
        {"pagina": 1},
        {"pagina": 1},
    ],
)

# query() sem query_embeddings= — ChromaDB chama emb_fn(query_texts) automaticamente
resultado = colecao.query(
    query_texts=["Qual é o valor do aluguel?"],  # texto bruto, não vetor
    n_results=2,
    include=["documents", "distances"],
)

print(resultado["documents"][0])

# AVISO: use SEMPRE a mesma embedding_function para indexar e consultar
# Misturar modelos diferentes gera resultados completamente errados
