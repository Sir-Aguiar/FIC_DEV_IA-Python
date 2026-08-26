def recuperar_chunks(
    pergunta: str,
    modelo: SentenceTransformer,
    colecao: chromadb.Collection,
    n_resultados: int = 5,
    limiar_distancia: float = 0.6,
    filtro_arquivo: str = None,
) -> list[dict]:
    """Recupera os chunks mais relevantes para uma pergunta.

    Args:
        pergunta:          Texto da pergunta em linguagem natural.
        modelo:            Modelo SentenceTransformer.
        colecao:           Coleção ChromaDB a consultar.
        n_resultados:      Numero de chunks a recuperar.
        limiar_distancia:  Descartar chunks com distância acima deste valor.
        filtro_arquivo:    Se informado, restringe a busca a esse arquivo.

    Returns:
        Lista de chunks rankeados, do mais ao menos relevante.
        Cada item: {'texto', 'arquivo', 'pagina', 'distancia', 'rank'}
    """
    # 1. Gerar embedding da pergunta
    emb_pergunta = modelo.encode(pergunta, normalize_embeddings=True).tolist()

    # 2. Montar filtro de metadados (opcional)
    where = None
    if filtro_arquivo:
        where = {"arquivo": filtro_arquivo}

    # 3. Consultar o ChromaDB
    resultado = colecao.query(
        query_embeddings=[emb_pergunta],
        n_results=n_resultados,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # 4. Montar lista de chunks com ranking e filtragem por limiar
    chunks_recuperados = []
    for rank, (doc, meta, dist) in enumerate(
        zip(
            resultado["documents"][0],
            resultado["metadatas"][0],
            resultado["distances"][0],
        ),
        start=1,
    ):
        if dist > limiar_distancia:
            continue  # chunk muito distante — descartado
        chunks_recuperados.append(
            {
                "rank": rank,
                "texto": doc,
                "arquivo": meta.get("arquivo", "?"),
                "pagina": meta.get("pagina", "?"),
                "distancia": round(dist, 4),
                "relevancia": round(1 - dist, 4),  # invertido: maior = mais relevante
            }
        )

    return chunks_recuperados


def montar_contexto(chunks: list[dict], max_palavras: int = 1500) -> str:
    """Monta o bloco de contexto a partir dos chunks recuperados.

    Limita o total de palavras para caber no prompt do LLM.
    Os chunks já chegam rankeados — os mais relevantes entram primeiro.

    Args:
        chunks:      Lista de chunks rankeados por recuperar_chunks().
        max_palavras: Limite total de palavras no contexto (padrão: 1500).

    Returns:
        String formatada com os trechos mais relevantes e suas fontes.
    """
    partes = []
    palavras_total = 0

    for chunk in chunks:
        palavras_chunk = len(chunk["texto"].split())
        if palavras_total + palavras_chunk > max_palavras:
            break
        fonte = f"[{chunk['arquivo']} — p. {chunk['pagina']}]"
        partes.append(f"{fonte}\n{chunk['texto']}")
        palavras_total += palavras_chunk

    return "\n\n---\n\n".join(partes)


def exibir_resultados(pergunta: str, chunks: list[dict]) -> None:
    """Exibe os resultados da recuperação de forma legível no terminal."""
    print()
    print("=" * 60)
    print(f"PERGUNTA: {pergunta}")
    print(f"RECUPERADOS: {len(chunks)} chunks")
    print("=" * 60)

    if not chunks:
        print("Nenhum chunk relevante encontrado.")
        print("Tente reformular a pergunta ou reduzir o limiar de distância.")
        return

    for c in chunks:
        print(f'\n#{c["rank"]} | Relevância: {c["relevancia"]:.4f}')
        print(f"    Fonte: {c['arquivo']} — página {c['pagina']}")
        print(f"    Trecho: {c['texto'][:200]}...")
    print("=" * 60)
