# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Middleware — onde se colocam os limites
# Seção 4 – Middleware: onde se colocam os limites
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""Demonstra os pontos em que se pode intervir no laço do agente.

O middleware é a resposta do LangChain 1.x a uma pergunta prática: onde
colocar as regras que a organização precisa impor a um agente. Sem ele, o
limite de passos, a conferência humana e a proteção de dados pessoais viram
condicionais espalhadas pelo código da aplicação. Com ele, cada regra é um
objeto que se acrescenta ou se remove da lista.
"""
import pathlib

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    wrap_model_call,
    wrap_tool_call,
)
from langchain_openai import ChatOpenAI

from ferramentas import FERRAMENTAS

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

INSTRUCAO = ("Você assessora procuradores do Estado de Mato Grosso. Use as "
             "ferramentas para fundamentar as respostas.")


def modelo() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")


# --- Middleware autoral: registrar cada decisão -----------------------
@wrap_model_call
def registrar_passo(request, handler):
    """Imprime cada consulta ao modelo, para tornar o laço observável."""
    print("    → consulta ao modelo")
    return handler(request)


@wrap_tool_call
def conferir_argumentos(request, handler):
    """Confere os argumentos antes de deixar a ferramenta executar.

    Esta é a barreira que a Seção 6.3 usa contra a alucinação de argumento:
    um valor numérico que o agente inventou não passa daqui, porque a regra
    exige que ele apareça na pergunta original do usuário.
    """
    chamada = getattr(request, "tool_call", {}) or {}
    nome, argumentos = chamada.get("name", "?"), chamada.get("args", {})
    print(f"    → {nome}({argumentos})")
    return handler(request)


def parte_1_limites_prontos() -> None:
    """Os limites que vêm com o framework, sem escrever middleware."""
    print("\n--- 1. Limites prontos ---")
    agente = create_agent(
        model=modelo(), tools=FERRAMENTAS, system_prompt=INSTRUCAO,
        middleware=[
            # Teto de consultas ao modelo por execução: a proteção de orçamento
            # mais direta que existe, e a única que impede um laço infinito.
            ModelCallLimitMiddleware(thread_limit=4, exit_behavior="end"),
            # Teto por ferramenta, para o caso em que uma delas é cara.
            ToolCallLimitMiddleware(thread_limit=3, exit_behavior="end"),
        ],
    )
    saida = agente.invoke({"messages": [{"role": "user", "content":
        "Qual o prazo de recurso administrativo e, se a ciência foi em "
        "2026-04-06, quando ele vence?"}]})
    print(f"    mensagens trocadas: {len(saida['messages'])}")
    print(f"    resposta: {str(saida['messages'][-1].content).strip()[:190]}")


def parte_2_middleware_autoral() -> None:
    """Os dois ganchos escritos à mão, observando o laço por dentro."""
    print("\n--- 2. Middleware autoral: tornar o laço observável ---")
    agente = create_agent(model=modelo(), tools=FERRAMENTAS,
                          system_prompt=INSTRUCAO,
                          middleware=[registrar_passo, conferir_argumentos])
    saida = agente.invoke({"messages": [{"role": "user", "content":
        "Calcule a atualização de um débito de R$ 8.000,00 com 3 meses de atraso."}]})
    print(f"    resposta: {str(saida['messages'][-1].content).strip()[:190]}")


def parte_3_catalogo() -> None:
    """Os middlewares disponíveis na versão instalada."""
    print("\n--- 3. O que vem pronto na versão instalada ---")
    import langchain.agents.middleware as pacote
    prontos = sorted(n for n in dir(pacote) if n.endswith("Middleware") and n != "AgentMiddleware")
    for nome in prontos:
        print(f"    {nome}")
    print(f"\n    {len(prontos)} middlewares prontos. Os ganchos para escrever os seus:")
    ganchos = ["before_agent", "before_model", "wrap_model_call",
               "wrap_tool_call", "after_model", "after_agent"]
    print(f"    {', '.join(ganchos)}")


if __name__ == "__main__":
    parte_1_limites_prontos()
    parte_2_middleware_autoral()
    parte_3_catalogo()
