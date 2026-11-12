# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: O que o modelo recebe quando declaramos uma ferramenta
# Adaptado ao encaixe de lote de processamento fiscal da GTI
# Requisitos: pip install langchain langchain-openai
# ============================================================
"""Mostra o JSON Schema que cada ferramenta do minilab gera.

O agente nunca vê o código da função. Ele vê o nome, a descrição e o esquema
dos argumentos. A conferência desta parte é a terceira ferramenta: o esquema
Pydantic precisa comunicar o significado de cada argumento.
"""
import json
import sys
from pathlib import Path

from langchain_core.utils.function_calling import convert_to_openai_tool


# O script vive em exemplos/, mas as ferramentas do minilab estão em src/.
# Sem este caminho, o import acharia o ferramentas.py da própria pasta de exemplos.
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from ferramentas import (  # noqa: E402
    FERRAMENTAS,
    atualizar_consumo_janela,
    calcular_encaixe_lote,
    consultar_rotina,
)


# O resultado da execução fica em resultados/, na raiz do repositório.
SAIDA = RAIZ / "resultados" / "parte1_esquema.txt"
LINHAS: list[str] = []


def emitir(texto: str = "") -> None:
    """Imprime a linha e guarda a mesma linha para o arquivo da raiz."""
    print(texto)
    LINHAS.append(texto)


def declaracao(ferramenta) -> dict:
    """Separa o objeto function, que é o que viaja no pedido à API."""
    return convert_to_openai_tool(ferramenta)["function"]


def mostrar_esquema() -> None:
    """Imprime a declaração exata que viaja no pedido à API."""
    emitir("=" * 72)
    emitir("O que o modelo recebe de cada ferramenta")
    emitir("=" * 72)
    for ferramenta in FERRAMENTAS:
        esquema = declaracao(ferramenta)
        emitir(f"\nnome:      {esquema['name']}")
        emitir(f"descrição: {esquema['description'].splitlines()[0]}")
        emitir("parâmetros:")
        for campo, atributos in esquema["parameters"]["properties"].items():
            obrigatorio = campo in esquema["parameters"].get("required", [])
            descricao = atributos.get("description", "— sem descrição —")
            exigencia = "obrigatório" if obrigatorio else "opcional"
            emitir(
                f"    {campo} ({atributos.get('type')}, {exigencia}): {descricao}"
            )


def comparar_documentacao() -> None:
    """A descrição dos argumentos só existe quando alguém a escreve.

    A primeira ferramenta nasce de @tool. A terceira nasce de um esquema
    Pydantic com descrição em cada campo. O JSON abaixo é o que o modelo lê.
    """
    emitir("\n" + "=" * 72)
    emitir("Por que a descrição dos argumentos importa")
    emitir("=" * 72)
    sem = declaracao(consultar_rotina)["parameters"]["properties"]
    com = declaracao(atualizar_consumo_janela)["parameters"]["properties"]
    emitir("\nDeclarada por anotação de tipo (@tool sobre função):")
    emitir(f"    {json.dumps(sem, ensure_ascii=False)}")
    emitir("\nDeclarada com esquema Pydantic explícito (StructuredTool):")
    emitir(json.dumps(com, ensure_ascii=False, indent=4))
    emitir("\nNo primeiro caso o modelo sabe o tipo do argumento e nada além disso.")
    emitir("No segundo, ele sabe o que o argumento significa.")


def confirmar_terceira() -> None:
    """A parte 1 só fecha se todo argumento da terceira ferramenta tiver descrição."""
    propriedades = declaracao(atualizar_consumo_janela)["parameters"]["properties"]
    emitir("\n" + "=" * 72)
    emitir("Conferência da terceira ferramenta")
    emitir("=" * 72)
    faltando = []
    for campo, atributos in propriedades.items():
        texto = atributos.get("description", "").strip()
        emitir(f"    {campo}: {texto or '— sem descrição —'}")
        if not texto:
            faltando.append(campo)

    if faltando:
        emitir(
            "A terceira ferramenta não comunica o significado de: "
            + ", ".join(faltando)
        )
        gravar()
        sys.exit(1)

    emitir(
        "Confirmado: atualizar_consumo_janela comunica ao modelo "
        "o significado de cada argumento."
    )


def executar_direto() -> None:
    """As ferramentas são funções comuns e podem ser testadas sem agente.

    A gravação bem-sucedida alteraria rotinas.json. A chamada da terceira
    pede mais horas do que a janela do IPVA ainda tem, e a função recusa.
    """
    emitir("\n" + "=" * 72)
    emitir("Executando as ferramentas sem agente algum")
    emitir("=" * 72)
    emitir("\nconsultar_rotina('processamento de NF-e'):")
    emitir(f"    {consultar_rotina.invoke({'rotina': 'processamento de NF-e'})}")
    emitir("\ncalcular_encaixe_lote(300000, 120000, 3.5):")
    emitir(f"    {calcular_encaixe_lote(300000, 120000, 3.5)}")
    emitir("\natualizar_consumo_janela('RT-IPVA', 1):")
    emitir(
        "    "
        + atualizar_consumo_janela.invoke(
            {"codigo_rotina": "RT-IPVA", "horas_previstas": 1}
        )
    )


def gravar() -> None:
    """Escreve o esquema impresso em resultados/."""
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(LINHAS) + "\n", encoding="utf-8")


if __name__ == "__main__":
    mostrar_esquema()
    comparar_documentacao()
    confirmar_terceira()
    executar_direto()
    gravar()
