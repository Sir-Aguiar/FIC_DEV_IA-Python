# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Auditoria de fundamentação do assistente
# Seção 6 – Auditoria: Como Saber se o Assistente Está Fundamentado
# Requisitos: pip install openai chromadb pymupdf python-dotenv
# Execução: python exemplo03.py edital_exemplo.pdf
# ============================================================
"""Verifica se o assistente responde apenas quando o acervo permite.

A bateria abaixo mistura perguntas cuja resposta está no edital com
perguntas cuja resposta não está. Um assistente confiável acerta os
dois casos: responde as primeiras citando a página correta e recusa as
segundas. Responder às segundas é o defeito mais grave possível, pois
produz informação plausível e falsa sobre um documento oficial.
"""

import re
import sys
from typing import Dict, List

from exemplo02 import AssistenteDocumentos

# (pergunta, deve_responder, página esperada quando houver resposta)
BATERIA: List[tuple] = [
    ("Qual o prazo para envio das propostas?", True, 1),
    ("Qual o valor estimado da contratação?", True, 1),
    ("A empresa pode participar em consórcio?", True, 2),
    ("Qual o capital social mínimo exigido?", True, 2),
    ("Qual a garantia exigida para o notebook?", True, 3),
    ("Qual o percentual da multa por atraso na entrega?", False, None),
    ("Quem é o pregoeiro responsável pela sessão?", False, None),
    ("Qual a alíquota do IPVA em Mato Grosso em 2026?", False, None),
]


def paginas_citadas(resposta: str) -> List[int]:
    """Extrai os números de página citados no formato (documento, p. X)."""
    return [int(n) for n in re.findall(r"p\.\s*(\d+)", resposta)]


def avaliar(assistente: AssistenteDocumentos) -> List[Dict]:
    linhas = []

    for pergunta, deve_responder, pagina_esperada in BATERIA:
        resultado = assistente.responder(pergunta)
        respondeu = resultado["fundamentada"]
        citadas = paginas_citadas(resultado["resposta"])

        if not deve_responder:
            situacao = "OK (recusou)" if not respondeu else "FALHA (inventou)"
        elif not respondeu:
            situacao = "FALHA (recusou o que existe)"
        elif pagina_esperada in citadas:
            situacao = "OK (citou a página certa)"
        elif citadas:
            situacao = f"ATENÇÃO (citou p. {citadas}, esperada {pagina_esperada})"
        else:
            situacao = "ATENÇÃO (respondeu sem citar página)"

        linhas.append(
            {
                "pergunta": pergunta,
                "esperado": "responder" if deve_responder else "recusar",
                "obtido": "respondeu" if respondeu else "recusou",
                "paginas": citadas,
                "situacao": situacao,
            }
        )

    return linhas


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else "edital_exemplo.pdf"

    assistente = AssistenteDocumentos(arquivo_auditoria="auditoria.jsonl")
    info = assistente.carregar_documento(caminho)
    print(f"Acervo: {info['nome']} ({info['total_trechos']} trechos)\n")

    linhas = avaliar(assistente)

    print(f"{'Pergunta':<52} {'Esperado':<10} {'Obtido':<10} Situação")
    print("-" * 110)
    for linha in linhas:
        print(
            f"{linha['pergunta'][:50]:<52} "
            f"{linha['esperado']:<10} {linha['obtido']:<10} {linha['situacao']}"
        )

    falhas = [linha for linha in linhas if linha["situacao"].startswith("FALHA")]
    print(f"\n{len(linhas) - len(falhas)} de {len(linhas)} comportamentos corretos.")
    if falhas:
        print("Falhas encontradas — o assistente não está pronto para uso real.")


if __name__ == "__main__":
    main()
