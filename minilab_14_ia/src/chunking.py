"""Estratégias de chunking para o acervo do Regimento Interno da MTI."""

from __future__ import annotations


def rotulo_do_documento(secao: dict) -> str:
    numero = secao.get("numero") or secao.get("rotulo") or secao["id"]
    return f"{numero} — {secao['titulo']}"


def _chunk(texto: str, rotulo: str, origem: str, indice: int) -> dict:
    return {
        "texto": f"[{rotulo}]\n{texto.strip()}",
        "origem": origem,
        "rotulo": rotulo,
        "indice": indice,
    }


def secao_inteira(secao: dict) -> list[dict]:
    """Cada subseção vira um único chunk."""
    return [_chunk(secao["texto_completo"], rotulo_do_documento(secao), secao["id"], 0)]


def _janela(secao: dict, tamanho: int, sobreposicao: int) -> list[dict]:
    palavras = secao["texto_completo"].split()
    rotulo = rotulo_do_documento(secao)
    chunks = []
    inicio = 0
    indice = 0
    passo = max(tamanho - sobreposicao, 1)
    while inicio < len(palavras):
        fim = min(inicio + tamanho, len(palavras))
        trecho = " ".join(palavras[inicio:fim])
        if len(trecho.split()) >= 15:
            chunks.append(_chunk(trecho, rotulo, secao["id"], indice))
            indice += 1
        if fim == len(palavras):
            break
        inicio += passo
    return chunks or [_chunk(secao["texto_completo"], rotulo, secao["id"], 0)]


def janela_200_50(secao: dict) -> list[dict]:
    """Janela fixa de 200 palavras com sobreposição de 50."""
    return _janela(secao, tamanho=200, sobreposicao=50)


def janela_80_20(secao: dict) -> list[dict]:
    """Janela curta de 80 palavras com sobreposição de 20."""
    return _janela(secao, tamanho=80, sobreposicao=20)


def _texto_paragrafo(paragrafo: dict) -> str:
    partes = [paragrafo["texto"]]
    for alinea in paragrafo.get("alineas") or []:
        partes.append(f"{alinea['marcador']} - {alinea['texto']}")
        for item in alinea.get("itens") or []:
            partes.append(f"{item['marcador']}) {item['texto']}")
    return " ".join(partes)


def por_paragrafo(secao: dict) -> list[dict]:
    """Um chunk por artigo, com incisos e alíneas."""
    rotulo = rotulo_do_documento(secao)
    chunks = []
    for i, paragrafo in enumerate(secao.get("paragrafos") or []):
        numero = paragrafo.get("numero")
        prefixo = f"Art. {numero}º " if numero is not None else ""
        chunks.append(
            _chunk(prefixo + _texto_paragrafo(paragrafo), rotulo, secao["id"], i)
        )
    return chunks or secao_inteira(secao)


def chunkar_acervo(secoes: list[dict], estrategia) -> list[dict]:
    chunks = []
    for secao in secoes:
        chunks.extend(estrategia(secao))
    return chunks


ESTRATEGIAS = {
    "secao_inteira": secao_inteira,
    "por_paragrafo": por_paragrafo,
    "janela_200_50": janela_200_50,
}
