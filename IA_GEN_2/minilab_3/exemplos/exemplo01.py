# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: O que o modelo recebe quando declaramos uma ferramenta
# Seção 1 e 2 – A ferramenta é uma promessa; três formas de declarar
# Requisitos: pip install langchain langchain-openai
# ============================================================
"""Mostra o JSON Schema que cada ferramenta gera e o que o modelo enxerga.

O agente nunca vê o código da função. Ele vê o nome, a descrição e o esquema
dos argumentos, e decide a partir desses três elementos. Imprimir o que o
modelo recebe é o primeiro passo para entender por que ele às vezes escolhe
a ferramenta errada, assunto da Seção 6.
"""
import json

from langchain_core.utils.function_calling import convert_to_openai_tool

from ferramentas import FERRAMENTAS, buscar_legislacao, calcular_atualizacao_debito


def mostrar_esquema() -> None:
    """Imprime a declaração exata que viaja no pedido à API."""
    print("=" * 72)
    print("O que o modelo recebe de cada ferramenta")
    print("=" * 72)
    for ferramenta in FERRAMENTAS:
        declaracao = convert_to_openai_tool(ferramenta)["function"]
        print(f"\nnome:      {declaracao['name']}")
        print(f"descrição: {declaracao['description'].splitlines()[0]}")
        print("parâmetros:")
        for campo, atributos in declaracao["parameters"]["properties"].items():
            obrigatorio = campo in declaracao["parameters"].get("required", [])
            descricao = atributos.get("description", "— sem descrição —")
            print(f"    {campo} ({atributos.get('type')}, "
                  f"{'obrigatório' if obrigatorio else 'opcional'}): {descricao}")


def comparar_documentacao() -> None:
    """A descrição dos argumentos só existe quando alguém a escreve."""
    print("\n" + "=" * 72)
    print("Por que a descrição dos argumentos importa")
    print("=" * 72)
    sem = convert_to_openai_tool(buscar_legislacao)["function"]["parameters"]["properties"]
    com = convert_to_openai_tool(calcular_atualizacao_debito)["function"]["parameters"]["properties"]
    print(f"\nDeclarada por anotação de tipo (@tool sobre função):")
    print(f"    {json.dumps(sem, ensure_ascii=False)}")
    print(f"\nDeclarada com esquema Pydantic explícito (StructuredTool):")
    print(f"    {json.dumps(com, ensure_ascii=False, indent=6)[:420]}")
    print("\nNo primeiro caso o modelo sabe o tipo do argumento e nada além disso.")
    print("No segundo, ele sabe o que o argumento significa — e é essa diferença")
    print("que reduz a chance de ele preencher o campo com o número errado.")


def executar_direto() -> None:
    """As ferramentas são funções comuns e podem ser testadas sem agente."""
    print("\n" + "=" * 72)
    print("Executando as ferramentas sem agente algum")
    print("=" * 72)
    print("\nbuscar_legislacao('prazo recurso administrativo'):")
    print(f"    {buscar_legislacao.invoke({'assunto': 'prazo recurso administrativo'})[:180]}")
    print("\ncalcular_atualizacao_debito(10000, 12):")
    print(f"    {calcular_atualizacao_debito.invoke({'valor_principal': 10000, 'meses_atraso': 12})}")


if __name__ == "__main__":
    mostrar_esquema()
    comparar_documentacao()
    executar_direto()
