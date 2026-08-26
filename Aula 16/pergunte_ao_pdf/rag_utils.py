# ============================================================
# rag_utils.py — Funções compartilhadas do sistema RAG
# ============================================================
"""
Funções utilitárias usadas por indexador.py e buscador.py:
chunking, montagem de contexto e exibição de resultados.
"""

import hashlib
import os
from sentence_transformers import SentenceTransformer
import chromadb


# ── Constantes do projeto ────────────────────────────────────
MODELO_NOME      = 'paraphrase-multilingual-MiniLM-L12-v2'
_DIR             = os.path.dirname(os.path.abspath(__file__))
DB_PATH          = os.path.join(_DIR, 'banco')
COLECAO_NOME     = 'pdf_chunks'
CHUNK_PALAVRAS   = 400
CHUNK_OVERLAP    = 80
N_RESULTADOS     = 5
LIMIAR_DISTANCIA = 0.65
MAX_PALAVRAS_CTX = 1500


# ── Inicialização (lazy loading) ─────────────────────────────
_modelo   = None
_cliente  = None
_colecao  = None

def obter_modelo() -> SentenceTransformer:
    global _modelo
    if _modelo is None:
        print('Carregando modelo de embedding...')
        _modelo = SentenceTransformer(MODELO_NOME)
        print(f'Modelo pronto: {MODELO_NOME}')
    return _modelo

def obter_colecao() -> chromadb.Collection:
    global _cliente, _colecao
    if _colecao is None:
        _cliente = chromadb.PersistentClient(path=DB_PATH)
        _colecao = _cliente.get_or_create_collection(
            name=COLECAO_NOME,
            metadata={'hnsw:space': 'cosine',
                      'modelo':     MODELO_NOME}
        )
    return _colecao


# ── Chunking ─────────────────────────────────────────────────

def chunkar(texto: str,
            tamanho: int = CHUNK_PALAVRAS,
            sobreposicao: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto em chunks por palavras com sobreposição."""
    palavras = texto.split()
    chunks   = []
    inicio   = 0
    while inicio < len(palavras):
        fim   = min(inicio + tamanho, len(palavras))
        chunk = ' '.join(palavras[inicio:fim])
        if len(chunk.split()) >= 20:
            chunks.append(chunk)
        inicio += tamanho - sobreposicao
    return chunks


def id_chunk(texto: str) -> str:
    """Gera um ID determinístico baseado no conteúdo do chunk."""
    return hashlib.md5(texto.encode('utf-8')).hexdigest()[:16]


# ── Contexto e exibição ──────────────────────────────────────

def montar_contexto(chunks: list[dict],
                    max_palavras: int = MAX_PALAVRAS_CTX) -> str:
    """Monta bloco de contexto a partir dos chunks recuperados."""
    partes = []
    total  = 0
    for c in chunks:
        n = len(c['texto'].split())
        if total + n > max_palavras:
            break
        fonte = f"[{c['arquivo']} — p. {c['pagina']}]"
        partes.append(f"{fonte}\n{c['texto']}")
        total += n
    return '\n\n---\n\n'.join(partes)


def exibir_chunks(pergunta: str, chunks: list[dict]) -> None:
    """Imprime os chunks recuperados de forma legível."""
    print()
    print('=' * 62)
    print(f'PERGUNTA : {pergunta}')
    print(f'CHUNKS   : {len(chunks)} recuperados')
    print('=' * 62)
    if not chunks:
        print('Nenhum chunk dentro do limiar de relevância.')
        return
    for c in chunks:
        rel = 1 - c['distancia']
        bar = '#' * int(rel * 20)
        print(f"\n  #{c['rank']} [{bar:<20}] rel={rel:.3f}")
        print(f"      {c['arquivo']} — pag. {c['pagina']}")
        print(f"      {c['texto'][:180].strip()}...")
    print('=' * 62)
