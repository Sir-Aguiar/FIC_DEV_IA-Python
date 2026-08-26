def chunkar_texto(
    texto: str, tamanho: int = 500, sobreposicao: int = 100
) -> list[dict]:
    """Divide um texto em chunks de tamanho fixo com sobreposição.

    A sobreposição garante que contexto não seja perdido nas fronteiras.
    Divisão é feita por palavras para não cortar palavras ao meio.

    Args:
        texto:        Texto completo a ser dividido.
        tamanho:      Numero de palavras por chunk (padrão: 500).
        sobreposicao: Numero de palavras de sobreposição entre chunks (padrão: 100).

    Returns:
        Lista de dicionários, cada um com 'texto', 'inicio', 'fim', 'indice'.
    """
    palavras = texto.split()
    chunks = []
    inicio = 0
    indice = 0

    while inicio < len(palavras):
        fim = min(inicio + tamanho, len(palavras))
        chunk = " ".join(palavras[inicio:fim])

        # Descartar chunks muito curtos (ruído de fim de documento)
        if len(chunk.split()) >= 20:
            chunks.append(
                {
                    "texto": chunk,
                    "indice": indice,
                    "inicio": inicio,  # posição inicial em palavras
                    "fim": fim,  # posição final em palavras
                    "tamanho": len(chunk.split()),
                }
            )
            indice += 1

        # Avançar com sobreposição
        inicio += tamanho - sobreposicao

    return chunks


# Demonstração
texto_exemplo = """
CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE CONSULTORIA
Pelo presente instrumento, as partes abaixo qualificadas celebram
contrato de prestação de serviços nas condições descritas a seguir.
CLÁUSULA PRIMEIRA — DO OBJETO: A CONTRATADA se compromete a prestar
serviços de consultoria em tecnologia da informação, incluindo análise
de sistemas, desenvolvimento de software e treinamento de equipes.
O escopo detalhado consta no Anexo I, parte integrante deste instrumento.
CLÁUSULA SEGUNDA — DO PRAZO: O presente contrato tem vigência de
doze meses a partir da data de assinatura, podendo ser prorrogado
mediante acordo escrito entre as partes com antecedência de 30 dias.
"""

chunks = chunkar_texto(texto_exemplo.strip(), tamanho=30, sobreposicao=8)

for c in chunks:
    print(f'Chunk {c["indice"]:02d} | palavras {c["inicio"]}-{c["fim"]}')
    print(f'  {c["texto"][:80]}...')
    print()
