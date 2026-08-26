# ============================================================
# indexador.py — Indexa PDFs no ChromaDB
# Uso: python indexador.py caminho/para/arquivo.pdf
#      python indexador.py pdfs/  (indexa todos os PDFs da pasta)
# ============================================================

import sys
import os
import pdfplumber
import rag_utils as ru


def extrair_paginas(caminho_pdf: str) -> list[dict]:
    """Extrai texto de cada página de um PDF com pdfplumber."""
    paginas = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for i, pag in enumerate(pdf.pages, 1):
            texto = (pag.extract_text() or '').strip()
            if len(texto.split()) >= 10:   # ignorar páginas quase vazias
                paginas.append({'pagina': i, 'texto': texto})
    return paginas


def indexar_arquivo(caminho: str) -> int:
    """Indexa um único PDF. Retorna número de chunks inseridos."""
    nome    = os.path.basename(caminho)
    modelo  = ru.obter_modelo()
    colecao = ru.obter_colecao()

    print(f'\nIndexando: {nome}')
    paginas = extrair_paginas(caminho)
    print(f'  Páginas com texto: {len(paginas)}')

    # Montar todos os chunks do arquivo
    ids, docs, metas = [], [], []
    for pg in paginas:
        for j, chunk in enumerate(ru.chunkar(pg['texto'])):
            cid = ru.id_chunk(chunk)
            ids.append(cid)
            docs.append(chunk)
            metas.append({
                'arquivo':     nome,
                'pagina':      pg['pagina'],
                'chunk_local': j,
            })

    print(f'  Chunks gerados: {len(docs)}')

    # Filtrar IDs já indexados (idempotência)
    ja_existem = set(colecao.get(ids=ids)['ids']) if ids else set()
    novos      = [(i, d, m) for i, d, m in zip(ids, docs, metas)
                  if i not in ja_existem]

    if not novos:
        print('  Nenhum chunk novo — arquivo já estava indexado.')
        return 0

    ids_n, docs_n, metas_n = zip(*novos)

    print(f'  Gerando embeddings para {len(docs_n)} chunks...')
    embs = modelo.encode(
        list(docs_n),
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True
    ).tolist()

    colecao.add(
        ids=list(ids_n),
        documents=list(docs_n),
        embeddings=embs,
        metadatas=list(metas_n)
    )
    print(f'  Inseridos: {len(docs_n)} chunks')
    print(f'  Total na coleção: {colecao.count()}')
    return len(docs_n)


def main() -> None:
    if len(sys.argv) < 2:
        print('Uso: python indexador.py <arquivo.pdf|diretorio/>')
        sys.exit(1)

    alvo = sys.argv[1]
    if not os.path.isabs(alvo):
        alvo = os.path.normpath(os.path.join(os.path.dirname(__file__), alvo))

    if os.path.isdir(alvo):
        pdfs = [os.path.join(alvo, f)
                for f in os.listdir(alvo) if f.lower().endswith('.pdf')]
        if not pdfs:
            print(f'Nenhum PDF encontrado em: {alvo}')
            sys.exit(1)
        print(f'PDFs encontrados: {len(pdfs)}')
        total = sum(indexar_arquivo(p) for p in sorted(pdfs))
        print(f'\nIndexação concluída. Total de novos chunks: {total}')

    elif alvo.lower().endswith('.pdf') and os.path.isfile(alvo):
        indexar_arquivo(alvo)

    else:
        print(f'Erro: {alvo} nao é um PDF nem um diretório válido.')
        sys.exit(1)


if __name__ == '__main__':
    main()
