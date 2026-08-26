from sentence_transformers import SentenceTransformer
import chromadb
import pdfplumber
import hashlib
import os


# ── Configuração global ──────────────────────────────────────
MODELO_NOME = "paraphrase-multilingual-MiniLM-L12-v2"
DB_PATH = "./rag_banco"
COLECAO_NOME = "pdf_chunks"
CHUNK_PALAVRAS = 400
CHUNK_OVERLAP = 80


def extrair_texto_pdf(caminho_pdf: str) -> list[dict]:
    """Extrai texto de um PDF digital página por página.

    Args:
        caminho_pdf: Caminho para o arquivo PDF.

    Returns:
        Lista de dicionários com 'pagina' e 'texto'.
    """
    paginas = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pagina in enumerate(pdf.pages, 1):
            texto = pagina.extract_text() or ""
            texto = texto.strip()
            if texto:
                paginas.append({"pagina": i, "texto": texto})
    return paginas


def chunkar_texto(texto: str, tamanho: int, sobreposicao: int) -> list[str]:
    """Divide texto em chunks de tamanho fixo com sobreposição."""
    palavras = texto.split()
    chunks = []
    inicio = 0
    while inicio < len(palavras):
        fim = min(inicio + tamanho, len(palavras))
        chunk = " ".join(palavras[inicio:fim])
        if len(chunk.split()) >= 20:
            chunks.append(chunk)
        inicio += tamanho - sobreposicao
    return chunks


def indexar_pdf(
    caminho_pdf: str, modelo: SentenceTransformer, colecao: chromadb.Collection
) -> int:
    """Executa o ciclo completo de indexação de um PDF.

    Extrai texto -> chunkea -> gera embeddings -> insere no ChromaDB.
    IDs são gerados por hash do conteúdo — garante idempotência.

    Args:
        caminho_pdf: Caminho para o arquivo PDF.
        modelo:      Modelo SentenceTransformer carregado.
        colecao:     Coleção ChromaDB de destino.

    Returns:
        Número de chunks inseridos.
    """
    nome_arquivo = os.path.basename(caminho_pdf)
    print(f"Indexando: {nome_arquivo}")

    # 1. Extrair texto por página
    paginas = extrair_texto_pdf(caminho_pdf)
    print(f"  Paginas com texto: {len(paginas)}")

    # 2. Chunkar cada página e montar listas para inserção em lote
    todos_chunks = []
    todos_ids = []
    todos_metadados = []

    for pg in paginas:
        chunks_pg = chunkar_texto(pg["texto"], CHUNK_PALAVRAS, CHUNK_OVERLAP)
        for j, chunk in enumerate(chunks_pg):
            # ID determinístico: hash do conteúdo do chunk
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()[:16]

            todos_chunks.append(chunk)
            todos_ids.append(chunk_id)
            todos_metadados.append(
                {
                    "arquivo": nome_arquivo,
                    "pagina": pg["pagina"],
                    "chunk_local": j,
                    "num_palavras": len(chunk.split()),
                }
            )

    print(f"  Chunks gerados: {len(todos_chunks)}")

    # 3. Verificar quais IDs já existem (evitar reinserção)
    existentes = set(colecao.get(ids=todos_ids)["ids"])
    novos_idx = [i for i, cid in enumerate(todos_ids) if cid not in existentes]

    if not novos_idx:
        print("  Todos os chunks já estavam indexados. Nada a fazer.")
        return 0

    chunks_novos = [todos_chunks[i] for i in novos_idx]
    ids_novos = [todos_ids[i] for i in novos_idx]
    metas_novas = [todos_metadados[i] for i in novos_idx]

    # 4. Gerar embeddings em lote
    print(f"  Gerando embeddings para {len(chunks_novos)} chunks...")
    embeddings = modelo.encode(
        chunks_novos, batch_size=32, show_progress_bar=True, normalize_embeddings=True
    ).tolist()  # ChromaDB aceita lista de listas

    # 5. Inserir no ChromaDB
    colecao.add(
        ids=ids_novos,
        documents=chunks_novos,
        embeddings=embeddings,
        metadatas=metas_novas,
    )

    print(f"  Inseridos: {len(ids_novos)} chunks")
    print(f"  Total na coleção: {colecao.count()}")
    return len(ids_novos)


import sys

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "indexar_pdf":
        print("Uso: py src/ciclo_rag/rag1.py indexar_pdf <caminho.pdf>")
        sys.exit(1)

    caminho_pdf = sys.argv[2]
    modelo = SentenceTransformer(MODELO_NOME)
    client = chromadb.PersistentClient(path=DB_PATH)
    colecao = client.get_or_create_collection(
        name=COLECAO_NOME,
        metadata={"hnsw:space": "cosine"},
    )

    indexar_pdf(caminho_pdf, modelo, colecao)
