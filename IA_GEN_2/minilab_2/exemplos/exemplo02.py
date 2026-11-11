# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Templates, LCEL e a cadeia de duas etapas
# Seção 3 e 4 – Prompt templates e o encadeamento com o operador |
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""Monta prompts reutilizáveis e os encadeia com o operador de composição.

Um template separa a instrução, que é estável, dos dados, que mudam a cada
chamada. Essa separação é o que permite versionar a instrução como se
versiona código, em vez de espalhar variações do mesmo texto por dezenas de
arquivos. A cadeia de duas etapas mostra o caso em que a saída de uma etapa
alimenta a seguinte sem passar pelo programador.
"""
import pathlib

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = "gpt-5.6-luna"


def parte_1_template() -> None:
    """O mesmo template, três documentos diferentes."""
    print("\n--- 1. Um template, várias chamadas ---")
    template = ChatPromptTemplate.from_messages([
        ("system", "Você redige documentos oficiais do Governo de Mato Grosso. "
                   "Escreva em registro formal, sem lacunas entre colchetes."),
        ("human", "Redija a abertura de um {tipo} sobre {assunto}, dirigido à {destinatario}. "
                  "No máximo três frases."),
    ])

    # `format_messages` mostra o que o template produz antes de chamar a API,
    # que é o hábito que evita descobrir o prompt errado pela resposta errada.
    mensagens = template.format_messages(
        tipo="ofício", assunto="prorrogação de prazo contratual",
        destinatario="Prefeitura de Sinop")
    print(f"    system: {mensagens[0].content[:60]}...")
    print(f"    human : {mensagens[1].content}")

    modelo = init_chat_model(MODELO, model_provider="openai")
    cadeia = template | modelo | StrOutputParser()
    for tipo, assunto in (("ofício", "prorrogação de prazo contratual"),
                          ("memorando", "convocação para reunião de alinhamento")):
        saida = cadeia.invoke({"tipo": tipo, "assunto": assunto,
                               "destinatario": "Prefeitura de Sinop"})
        print(f"\n    [{tipo}] {saida.strip()[:200]}")


def parte_2_cadeia_de_duas_etapas() -> None:
    """A saída da primeira etapa entra na segunda sem passar pelo programador."""
    print("\n\n--- 2. Cadeia de duas etapas: redigir e depois revisar ---")
    modelo = init_chat_model(MODELO, model_provider="openai")

    redigir = ChatPromptTemplate.from_messages([
        ("system", "Você redige documentos oficiais. Seja objetivo."),
        ("human", "Redija um parágrafo de {tipo} sobre {assunto}."),
    ])
    revisar = ChatPromptTemplate.from_messages([
        ("system", "Você revisa documentos oficiais. Aponte em uma linha o principal "
                   "problema do texto e reescreva-o corrigido."),
        ("human", "{minuta}"),
    ])

    # O operador | encadeia: o resultado de cada etapa é a entrada da seguinte.
    # `RunnablePassthrough` nomeia esse resultado para o template seguinte.
    cadeia = (
        redigir | modelo | StrOutputParser()
        | {"minuta": RunnablePassthrough()}
        | revisar | modelo | StrOutputParser()
    )
    saida = cadeia.invoke({"tipo": "despacho", "assunto": "indeferimento de pedido de férias"})
    print(f"    {saida.strip()[:400]}")


def main() -> None:
    parte_1_template()
    parte_2_cadeia_de_duas_etapas()
    print()


if __name__ == "__main__":
    main()
