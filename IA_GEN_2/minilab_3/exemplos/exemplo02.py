# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: O primeiro agente e a leitura do fluxo de mensagens
# Seção 3 – create_agent: o laço, por baixo, é um grafo
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""Cria um agente com as três ferramentas e mostra o que ele decidiu.

O ponto da seção é que o laço do agente não é opaco. Acompanhando o fluxo de
mensagens é possível ver a decisão de chamar cada ferramenta, os argumentos
que o modelo escolheu e o resultado que voltou, o que torna auditável um
processo que de outra forma se conheceria apenas pelo texto final.
"""
import pathlib

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from ferramentas import FERRAMENTAS

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

INSTRUCAO = (
    "Você assessora procuradores do Estado de Mato Grosso. Use as ferramentas "
    "disponíveis para fundamentar suas respostas e cite a norma aplicável. "
    "Se a pergunta não trouxer os dados necessários para um cálculo, peça os "
    "dados que faltam em vez de supor valores."
)


def mostrar_fluxo(pergunta: str) -> None:
    # `reasoning_effort="none"` não é preferência, é exigência. Com ferramentas
    # declaradas, a família GPT-5.6 recusa o endpoint de Chat Completions se o
    # esforço de raciocínio estiver ativo, conforme a Seção 3.2. A alternativa
    # é `use_responses_api=True`, que mantém o raciocínio e devolve a resposta
    # em blocos em vez de texto corrido.
    modelo = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")
    agente = create_agent(model=modelo, tools=FERRAMENTAS, system_prompt=INSTRUCAO)
    print(f"\nPergunta: {pergunta}\n" + "-" * 70)

    # `stream_mode="updates"` entrega cada passo assim que ele acontece, em vez
    # de esperar o fim. É a substituição do antigo `debug=True`, que imprimia
    # tudo sem estrutura e não podia ser processado por código.
    for passo in agente.stream({"messages": [{"role": "user", "content": pergunta}]},
                               stream_mode="updates"):
        for no, dados in passo.items():
            for mensagem in dados.get("messages", []):
                chamadas = getattr(mensagem, "tool_calls", None)
                if chamadas:
                    for chamada in chamadas:
                        print(f"  [{no}] decide chamar {chamada['name']}({chamada['args']})")
                elif mensagem.type == "tool":
                    print(f"  [{no}] {mensagem.name} devolveu: "
                          f"{str(mensagem.content)[:110]}")
                elif mensagem.content:
                    print(f"  [{no}] resposta final:\n      "
                          f"{str(mensagem.content).strip()[:300]}")


def main() -> None:
    mostrar_fluxo("Um débito de R$ 25.000,00 está com 6 meses de atraso. "
                  "Calcule o valor atualizado e informe qual norma fundamenta o cálculo.")
    mostrar_fluxo("Calcule a atualização do débito daquele processo que "
                  "discutimos ontem e informe o valor final.")


if __name__ == "__main__":
    main()
