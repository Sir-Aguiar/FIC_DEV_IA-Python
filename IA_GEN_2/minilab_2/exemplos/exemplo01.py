# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: Modelos, mensagens e os três destinos
# Seção 2 – Um modelo, três destinos: OpenAI, Groq e o roteador do Hugging Face
# Requisitos: pip install langchain langchain-openai langchain-groq python-dotenv
# ============================================================
"""Envia a mesma pergunta administrativa a três destinos diferentes.

A troca de destino em LangChain 1.x se faz por uma linha, o que permite
comparar provedores sem reescrever a aplicação. O exemplo mede o tempo de
cada resposta e o consumo de tokens, para que a escolha do destino deixe de
ser preferência e passe a ser decisão apoiada em número.
"""
import os
import pathlib
import time

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

PERGUNTA = ("Em uma frase, qual a diferença entre dispensa e inexigibilidade "
            "de licitação na Lei nº 14.133/2021?")

# Cada entrada é (rótulo, identificador do modelo, provedor, variável de ambiente).
# O roteador do Hugging Face é acessado pelo provedor openai, porque expõe uma
# interface compatível, bastando apontar a URL base para o roteador.
DESTINOS = [
    ("OpenAI · gpt-5.6-luna", "gpt-5.6-luna", "openai", "OPENAI_API_KEY", {}),
    ("Groq · gpt-oss-20b", "openai/gpt-oss-20b", "groq", "GROQ_API_KEY",
     {"timeout": 45, "max_retries": 0}),
    ("Hugging Face · gpt-oss-20b", "openai/gpt-oss-20b:cheapest", "openai", "HF_TOKEN",
     {"base_url": "https://router.huggingface.co/v1", "timeout": 60, "max_retries": 0}),
]


def main() -> None:
    mensagens = [
        SystemMessage("Você assessora servidores públicos. Responda de forma objetiva."),
        HumanMessage(PERGUNTA),
    ]

    print(f"Pergunta: {PERGUNTA}\n")
    for rotulo, identificador, provedor, variavel, extras in DESTINOS:
        chave = os.getenv(variavel)
        if not chave:
            print(f"{rotulo}: {variavel} não definida, destino ignorado\n")
            continue
        try:
            # A única linha que muda entre os destinos é esta.
            modelo = init_chat_model(identificador, model_provider=provedor,
                                     api_key=chave, **extras)
            # Chamada de aquecimento, descartada da medição. A primeira conexão
            # de um processo a cada host paga o estabelecimento do canal seguro,
            # que na preparação desta aula chegou a 150 segundos. Sem descartá-la,
            # a medição informa a rede local do aluno, e não o provedor.
            modelo.invoke([HumanMessage("ok")])
            inicio = time.perf_counter()
            resposta = modelo.invoke(mensagens)
            decorrido = time.perf_counter() - inicio
            uso = resposta.usage_metadata or {}
            print(f"{rotulo}")
            print(f"   {resposta.content.strip()[:220]}")
            print(f"   {decorrido:.2f}s · entrada {uso.get('input_tokens', 0)} tokens "
                  f"· saída {uso.get('output_tokens', 0)} tokens\n")
        except Exception as erro:
            print(f"{rotulo}: {type(erro).__name__} — {str(erro)[:120]}\n")


if __name__ == "__main__":
    main()
