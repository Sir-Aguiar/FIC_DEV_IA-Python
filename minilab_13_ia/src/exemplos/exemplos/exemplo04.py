# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: Trocando o provedor de geração sem tocar no acervo
# Seção 8 – Trocando o Provedor sem Reconstruir o Assistente
# Requisitos: pip install openai chromadb pymupdf python-dotenv
# Execução: python exemplo04.py edital_exemplo.pdf
# ============================================================
"""Compara a mesma pergunta respondida por dois provedores.

A camada de recuperação é idêntica nos dois casos: mesmo PDF, mesmos
trechos, mesmo índice vetorial. Muda apenas o cliente de geração, o
que evidencia que o acervo é o ativo duradouro do órgão e o modelo é
peça substituível.
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from exemplo02 import AssistenteDocumentos

load_dotenv()

PERGUNTAS = [
    "Qual o prazo para envio das propostas?",
    "Qual o percentual da multa por atraso na entrega?",
]


def montar_assistente_groq() -> AssistenteDocumentos:
    """Assistente com geração no Groq, via API compatível com a OpenAI."""
    cliente_groq = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
    )
    return AssistenteDocumentos(
        modelo="openai/gpt-oss-120b",
        cliente=cliente_groq,
        parametros_geracao={"max_completion_tokens": 2000, "reasoning_effort": "low"},
        arquivo_auditoria="consultas_groq.jsonl",
    )


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else "edital_exemplo.pdf"

    # Atenção: os embeddings continuam sendo gerados pela OpenAI nos dois
    # assistentes. Trocar o modelo de embedding obriga a reindexar todo o
    # acervo, porque vetores de modelos diferentes não são comparáveis.
    assistentes = {
        "OpenAI (gpt-5.6-luna)": AssistenteDocumentos(),
        "Groq (openai/gpt-oss-120b)": montar_assistente_groq(),
    }

    for rotulo, assistente in assistentes.items():
        assistente.carregar_documento(caminho)
        print(f"\n===== {rotulo} =====")

        for pergunta in PERGUNTAS:
            resultado = assistente.responder(pergunta)
            marca = "fundamentada" if resultado["fundamentada"] else "recusa"
            print(f"\n[{marca}] {pergunta}")
            print(resultado["resposta"])


if __name__ == "__main__":
    main()
