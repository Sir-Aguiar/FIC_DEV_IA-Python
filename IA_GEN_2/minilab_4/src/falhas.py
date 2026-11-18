# ============================================================
# Minilab 4 — falha da Seção 7.3, delegação e ancoragem
# O dossiê verdadeiro não é alterado em disco. A troca de
# valor existe só na entrada da primeira tarefa.
# ============================================================
"""Reproduz o erro que atravessa a cadeia e a barreira que o segura.

A primeira tarefa recebe a dotação inicial trocada. A última só vê essa
extração. Em seguida a mesma tarefa roda com delegação ligada e desligada.
O guardrail confere o número final contra o dossiê verdadeiro.
"""
import pathlib
import re
import time
import warnings
from typing import Any, Tuple

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field


BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parent / ".env")

MODELO = LLM(model="openai/gpt-5.6-luna")
DOSSIE = (BASE / "dados" / "dossie_projeto.md").read_text(encoding="utf-8")

# Troca visível: o dossiê traz 101.311.882,00. A primeira tarefa recebe o dobro
# na casa das centenas de milhão, valor que não decorre de nenhuma conta do RAG.
VALOR_REAL = "101.311.882,00"
VALOR_PLANTADO = "201.311.882,00"
DOSSIE_ADULTERADO = DOSSIE.replace(VALOR_REAL, VALOR_PLANTADO, 1)

# Inteiros que o texto do dossiê autoriza. Percentuais e contagens curtas
# ficam de fora do filtro de cinco dígitos, como no exemplo da aula.
VALORES_DOSSIE = [
    101_311_882,
    162_019_948,
    134_311_172,
    132_503_779,
    132_503_780,
    142_304_955,
    140_338_309,
]
PRAZOS = [12, 19]


def _autorizados() -> set[int]:
    """Inclui somas, diferenças e produtos pelos prazos do próprio dossiê."""
    base = set(VALORES_DOSSIE)
    derivados = set(base)
    for a in base:
        for b in base:
            derivados.add(a + b)
            derivados.add(abs(a - b))
        for prazo in PRAZOS:
            derivados.add(a * prazo)
    return derivados


AUTORIZADOS = _autorizados()

# Conta quantas vezes o guardrail devolveu a tarefa. A confirmação do item 10
# é esta lista deixar de estar vazia diante do valor plantado.
REJEICOES: list[str] = []


class Extrato(BaseModel):
    """Saída que o guardrail consegue ler sem interpretar prosa."""

    dotacao_inicial: float = Field(description="Dotação inicial do programa na LOA, em reais")
    recomendacao: str = Field(description="Recomendação explícita sobre o uso desse valor")


def agente(papel: str, objetivo: str, historia: str, delegar: bool = False) -> Agent:
    """Aplica os mesmos tetos da equipe, para a comparação não misturar orçamento."""
    return Agent(
        role=papel,
        goal=objetivo,
        backstory=historia,
        llm=MODELO,
        verbose=False,
        max_iter=5,
        max_rpm=10,
        max_execution_time=180,
        allow_delegation=delegar,
    )


def ancoragem_numerica(saida) -> Tuple[bool, Any]:
    """Recusa dotação que não esteja no dossiê verdadeiro.

    Roda depois da redação e antes de a tarefa encerrar. O valor plantado
    na primeira etapa chega aqui pelo contexto; o conjunto autorizado foi
    montado só com o arquivo original.
    """
    nota = getattr(saida, "pydantic", None)
    if nota is None:
        return (True, saida)

    if round(nota.dotacao_inicial) not in AUTORIZADOS:
        mensagem = (
            f"A dotação inicial {nota.dotacao_inicial:.2f} não consta do dossiê "
            f"nem decorre de cálculo sobre os valores dele. O valor da LOA é "
            f"{VALOR_REAL}. Corrija."
        )
        REJEICOES.append(mensagem)
        return (False, mensagem)

    texto = f"{nota.recomendacao}"
    for bruto in re.findall(r"\d[\d.]*(?:,\d{2})?", texto):
        limpo = bruto.split(",")[0].replace(".", "")
        if len(limpo) < 5 or not limpo.isdigit():
            continue
        if int(limpo) not in AUTORIZADOS:
            mensagem = (
                f"O valor {bruto} citado no texto não consta do dossiê. Corrija."
            )
            REJEICOES.append(mensagem)
            return (False, mensagem)

    return (True, saida)


def falha_erro_que_atravessa() -> dict:
    """A última tarefa não recebe o dossiê, só a extração adulterada."""
    extrator = agente(
        "Extrator",
        "Extrair a dotação inicial do dossiê",
        "Você é técnico administrativo e transcreve valores.",
    )
    parecerista = agente(
        "Parecerista",
        "Emitir parecer sobre a dotação extraída",
        "Você é procurador e fundamenta seus pareceres.",
    )

    extracao = Task(
        description=(
            "Extraia a dotação inicial do programa e informe o número exato."
            "\n\nDOSSIÊ:\n" + DOSSIE_ADULTERADO
        ),
        expected_output="A dotação inicial, em uma linha.",
        agent=extrator,
    )
    parecer = Task(
        description=(
            "Emita parecer sobre a adequação dessa dotação, usando somente "
            "a extração anterior. Não peça o dossiê de novo."
        ),
        expected_output="Parecer em até oito linhas, com recomendação.",
        agent=parecerista,
        context=[extracao],
    )
    resultado = Crew(
        agents=[extrator, parecerista],
        tasks=[extracao, parecer],
        process=Process.sequential,
        verbose=False,
    ).kickoff()

    final = str(resultado)
    repetiu = "201.311.882" in final or "201311882" in final
    questionou = any(
        pista in final.lower()
        for pista in ("divergên", "conferir", "confirmar", "inconsist", "question")
    )
    return {"texto": final, "repetiu": repetiu, "questionou": questionou}


def comparar_delegacao() -> list[dict]:
    """A mesma tarefa, com o segundo agente disponível só quando a delegação liga."""
    registros = []
    for delegar in (False, True):
        tecnico = agente(
            "Analista Técnico",
            "Avaliar disponibilidade e execução do Programa 536",
            "Você é engenheiro da MTI.",
            delegar=delegar,
        )
        financeiro = agente(
            "Analista Financeiro",
            "Avaliar a execução orçamentária do Programa 536",
            "Você é contador da execução do PPA.",
            delegar=delegar,
        )
        tarefa = Task(
            description=(
                "Avalie o Programa 536 nos lados técnico e financeiro."
                "\n\nDOSSIÊ:\n" + DOSSIE
            ),
            expected_output="Avaliação em até dez linhas.",
            agent=tecnico,
        )
        inicio = time.perf_counter()
        resultado = Crew(
            agents=[tecnico, financeiro],
            tasks=[tarefa],
            process=Process.sequential,
            verbose=False,
        ).kickoff()
        uso = resultado.token_usage
        registros.append(
            {
                "delegar": delegar,
                "chamadas": uso.successful_requests,
                "tokens": uso.prompt_tokens + uso.completion_tokens,
                "tempo": time.perf_counter() - inicio,
            }
        )
    return registros


def confirmar_guardrail() -> dict:
    """Repete a cadeia adulterada com a ancoragem na última tarefa."""
    REJEICOES.clear()
    extrator = agente(
        "Extrator",
        "Extrair a dotação inicial do dossiê",
        "Você é técnico administrativo e transcreve valores.",
    )
    parecerista = agente(
        "Parecerista",
        "Emitir a dotação inicial somente se ela constar do dossiê",
        "Você é procurador e corrige o número quando a ancoragem recusa.",
    )
    extracao = Task(
        description=(
            "Extraia a dotação inicial do programa."
            "\n\nDOSSIÊ:\n" + DOSSIE_ADULTERADO
        ),
        expected_output="A dotação inicial, em uma linha.",
        agent=extrator,
    )
    parecer = Task(
        description=(
            "Preencha a dotação inicial a partir da extração. Se a ancoragem "
            "recusar o número, use a dotação da LOA citada na mensagem de correção."
        ),
        expected_output="Extrato com a dotação inicial e uma recomendação.",
        agent=parecerista,
        context=[extracao],
        output_pydantic=Extrato,
        guardrail=ancoragem_numerica,
    )
    resultado = Crew(
        agents=[extrator, parecerista],
        tasks=[extracao, parecer],
        process=Process.sequential,
        verbose=False,
    ).kickoff()
    nota = resultado.pydantic
    return {
        "rejeicoes": list(REJEICOES),
        "dotacao": None if nota is None else nota.dotacao_inicial,
    }


def main() -> None:
    """Roda os três ensaios e grava o registro em falhas.md."""
    print("7.3 erro na cadeia", flush=True)
    falha = falha_erro_que_atravessa()
    print(
        f"repetiu={falha['repetiu']} questionou={falha['questionou']}",
        flush=True,
    )
    print(falha["texto"][:500], flush=True)

    print("delegação", flush=True)
    delegacao = comparar_delegacao()
    for item in delegacao:
        print(item, flush=True)

    print("guardrail", flush=True)
    barreira = confirmar_guardrail()
    print(barreira, flush=True)

    linhas = [
        "# Falha da Seção 7.3, delegação e ancoragem",
        "",
        f"Valor real: R$ {VALOR_REAL}. Valor plantado na primeira tarefa: R$ {VALOR_PLANTADO}.",
        "",
        "## Erro que atravessa a cadeia",
        "",
        f"- O parecer final repete o valor plantado: {'sim' if falha['repetiu'] else 'não'}.",
        f"- A última tarefa questiona o número recebido: {'sim' if falha['questionou'] else 'não'}.",
        "",
        "Trecho do parecer:",
        "",
        "```",
        falha["texto"].strip()[:900],
        "```",
        "",
        "## allow_delegation na mesma tarefa",
        "",
        "| allow_delegation | Chamadas | Tokens | Tempo |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in delegacao:
        linhas.append(
            f"| {item['delegar']} | {item['chamadas']} | {item['tokens']} | {item['tempo']:.1f}s |"
        )
    linhas.extend(
        [
            "",
            "## Guardrail de ancoragem",
            "",
            f"- Rejeições antes de aceitar a saída: {len(barreira['rejeicoes'])}.",
            f"- Dotação aceita ao final: {barreira['dotacao']}.",
            "",
        ]
    )
    if barreira["rejeicoes"]:
        linhas.append(f"Primeira recusa: {barreira['rejeicoes'][0]}")
        linhas.append("")
    destino = BASE.parent / "falhas.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print(f"registro em {destino}", flush=True)


if __name__ == "__main__":
    main()
