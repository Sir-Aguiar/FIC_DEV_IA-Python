# ============================================================
# buscador.py — Interface de perguntas sobre PDFs indexados
# Uso: python buscador.py
#      python buscador.py --arquivo contrato.pdf
#      python buscador.py --n 8 --limiar 0.5
# ============================================================

import argparse
import sys
import rag_utils as ru


def recuperar(pergunta: str,
              n: int,
              limiar: float,
              arquivo: str = None) -> list[dict]:
    """Gera embedding da pergunta e busca no ChromaDB."""
    modelo  = ru.obter_modelo()
    colecao = ru.obter_colecao()

    emb = modelo.encode(
        pergunta,
        normalize_embeddings=True
    ).tolist()

    kwargs = {
        'query_embeddings': [emb],
        'n_results': n,
        'include': ['documents', 'metadatas', 'distances'],
    }
    if arquivo:
        kwargs['where'] = {'arquivo': arquivo}

    resultado = colecao.query(**kwargs)

    docs  = resultado.get('documents') or [[]]
    metas = resultado.get('metadatas') or [[]]
    dists = resultado.get('distances') or [[]]
    if not docs[0]:
        return []

    chunks = []
    for rank, (doc, meta, dist) in enumerate(zip(
        docs[0],
        metas[0],
        dists[0]
    ), start=1):
        if dist <= limiar:
            chunks.append({
                'rank':      rank,
                'texto':     doc,
                'arquivo':   meta.get('arquivo', '?'),
                'pagina':    meta.get('pagina', '?'),
                'distancia': round(dist, 4),
            })
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Busca semântica em PDFs indexados no ChromaDB.'
    )
    parser.add_argument('--arquivo', default=None,
        help='Restringir busca a um arquivo específico.')
    parser.add_argument('--n', type=int, default=ru.N_RESULTADOS,
        help=f'Número de chunks a recuperar (padrão: {ru.N_RESULTADOS}).')
    parser.add_argument('--limiar', type=float, default=ru.LIMIAR_DISTANCIA,
        help=f'Limiar de distância máxima (padrão: {ru.LIMIAR_DISTANCIA}).')
    parser.add_argument('--contexto', action='store_true',
        help='Exibir contexto montado (pronto para LLM) em vez dos chunks.')
    args = parser.parse_args()

    colecao = ru.obter_colecao()
    if colecao.count() == 0:
        print('Banco vazio. Execute primeiro: python indexador.py <arquivo.pdf>')
        sys.exit(1)

    print('=' * 62)
    print('  BUSCADOR SEMÂNTICO DE PDFs — ChromaDB + sentence-transformers')
    print(f'  Documentos indexados: {colecao.count()} chunks')
    if args.arquivo:
        print(f'  Filtro de arquivo: {args.arquivo}')
    print("  Digite 'sair' para encerrar.")
    print('=' * 62)

    while True:
        print()
        pergunta = input('Pergunta: ').strip()

        if not pergunta:
            continue
        if pergunta.lower() in ('sair', 'exit', 'q'):
            print('Encerrando.')
            break

        chunks = recuperar(
            pergunta,
            n=args.n,
            limiar=args.limiar,
            arquivo=args.arquivo
        )

        if args.contexto:
            ctx = ru.montar_contexto(chunks)
            print('\n=== CONTEXTO MONTADO (para LLM) ===')
            print(ctx if ctx else '(nenhum chunk dentro do limiar)')
        else:
            ru.exibir_chunks(pergunta, chunks)


if __name__ == '__main__':
    main()
