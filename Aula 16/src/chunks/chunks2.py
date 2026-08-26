import re


def chunkar_por_paragrafos(
    texto: str, max_palavras: int = 400, min_palavras: int = 20
) -> list[dict]:
    """Divide texto respeitando parágrafos e seções naturais do documento."""
    paragrafos = re.split(r"\n{2,}|(?=CLÁUSULA|CAPÍTULO|ARTIGO|SEÇÃO|§)", texto)
    paragrafos = [p.strip() for p in paragrafos if p.strip()]

    chunks = []
    buffer = []
    indice = 0

    for para in paragrafos:
        palavras_buffer = sum(len(b.split()) for b in buffer)
        palavras_para = len(para.split())

        if buffer and palavras_buffer + palavras_para > max_palavras:
            chunks.append({"texto": " ".join(buffer), "indice": indice})
            indice += 1
            buffer = []

        buffer.append(para)

    if buffer:
        texto_final = " ".join(buffer)
        if len(texto_final.split()) >= min_palavras:
            chunks.append({"texto": texto_final, "indice": indice})

    return chunks


# ── Execução de Teste para o Terminal ────────────────────────
texto_exemplo = """
CLÁUSULA PRIMEIRA — DO OBJETO
A CONTRATADA prestará serviços de desenvolvimento de software e análise de dados.

CLÁUSULA SEGUNDA — DOS VALORES
O valor mensal acordado é de R$ 5.000,00, pagos até o quinto dia útil de cada mês.

CLÁUSULA TERCEIRA — DA RESCISÃO
Em caso de rescisão antecipada sem justa causa, será aplicada multa de 10% sobre o saldo remanescente do contrato.
"""

resultado = chunkar_por_paragrafos(texto_exemplo, max_palavras=25, min_palavras=5)

print(f"Total de chunks gerados: {len(resultado)}\n")

for c in resultado:
    print(f"--- Chunk {c['indice']} ---")
    print(c["texto"])
    print()
