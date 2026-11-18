# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Contexto entre tarefas, saída estruturada e guardrail
# Seção 4 – Tarefas no CrewAI
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Encadeia tarefas e impõe a forma da saída da última.

Três recursos da tarefa aparecem aqui. O `context` faz o resultado de uma
tarefa chegar à seguinte, que é o mecanismo de colaboração da equipe. O
`output_pydantic` obriga a saída final a respeitar um esquema, transformando
texto em dado consumível por outro sistema. O `guardrail` reprova a saída que
não atenda a uma condição, devolvendo a tarefa ao agente.
"""
import pathlib
import warnings
from typing import Any, Tuple

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = LLM(model="openai/gpt-5.6-luna")
DOSSIE = (BASE / "dossie_projeto.md").read_text(encoding="utf-8")


class Parecer(BaseModel):
    """A forma que o parecer precisa ter para alimentar o sistema de protocolo."""

    sintese: str = Field(description="Resumo do caso em até três frases")
    valor_estimado: float = Field(description="Valor estimado da contratação, em reais")
    recomendacao: str = Field(description="Recomendação explícita e fundamentada")
    pontos_de_atencao: list[str] = Field(description="Riscos que exigem decisão superior")


def exigir_valor_do_dossie(saida) -> Tuple[bool, Any]:
    """Guardrail: reprova o parecer cujo valor não seja o do dossiê.

    O guardrail recebe a saída da tarefa e devolve um par. Quando o primeiro
    elemento é falso, o segundo vira a mensagem de correção enviada de volta
    ao agente, que tenta novamente. É a barreira mais barata contra o número
    inventado, e ela roda em código e não no prompt.

    A anotação de retorno precisa ser exatamente `Tuple[bool, Any]`, do módulo
    `typing`. O CrewAI valida essa assinatura na construção da tarefa, e a
    forma moderna `tuple[bool, object]` é recusada com erro de validação do
    Pydantic — detalhe que custa alguns minutos a quem escreve o primeiro
    guardrail.
    """
    valor = getattr(getattr(saida, "pydantic", None), "valor_estimado", None)
    if valor is None:
        return (True, saida)
    if abs(valor - 1_870_000.00) > 0.01:
        return (False, f"O valor {valor} não é o do dossiê, que é 1870000.00. "
                       f"Corrija usando exclusivamente os números do dossiê.")
    return (True, saida)


def main() -> None:
    tecnico = Agent(
        role="Analista Técnico",
        goal="Avaliar a viabilidade técnica do projeto",
        backstory=("Você é engenheiro de software com experiência em sistemas "
                   "públicos e conhece os riscos de migração de acervos."),
        llm=MODELO, verbose=False, max_iter=5, allow_delegation=False)

    financeiro = Agent(
        role="Analista Financeiro",
        goal="Avaliar custos e adequação orçamentária",
        backstory=("Você é contador e examina se o valor pretendido cabe na "
                   "dotação do exercício."),
        llm=MODELO, verbose=False, max_iter=5, allow_delegation=False)

    parecerista = Agent(
        role="Parecerista",
        goal="Consolidar as análises em parecer com recomendação",
        backstory=("Você é procurador do Estado e redige pareceres enxutos, "
                   "sempre fundamentados na Lei nº 14.133/2021."),
        llm=MODELO, verbose=False, max_iter=5, allow_delegation=False)

    analise_tecnica = Task(
        description="Analise a viabilidade técnica do projeto.\n\nDOSSIÊ:\n" + DOSSIE,
        expected_output="Análise em até dez linhas, citando os números do dossiê.",
        agent=tecnico)

    analise_financeira = Task(
        description="Analise a adequação orçamentária do projeto.\n\nDOSSIÊ:\n" + DOSSIE,
        expected_output="Análise em até dez linhas, citando os valores do dossiê.",
        agent=financeiro)

    consolidacao = Task(
        description=("Consolide as análises anteriores em um parecer único para "
                     "decisão do Secretário, com recomendação explícita."),
        expected_output=("Parecer com síntese, valor estimado, recomendação e "
                         "pontos de atenção."),
        agent=parecerista,
        # As duas análises chegam a esta tarefa como contexto. Sem isso, o
        # parecerista receberia apenas a descrição acima e não teria o que
        # consolidar.
        context=[analise_tecnica, analise_financeira],
        output_pydantic=Parecer,
        guardrail=exigir_valor_do_dossie,
    )

    equipe = Crew(agents=[tecnico, financeiro, parecerista],
                  tasks=[analise_tecnica, analise_financeira, consolidacao],
                  process=Process.sequential, verbose=False)
    resultado = equipe.kickoff()

    parecer = resultado.pydantic
    print("=" * 72)
    print("PARECER ESTRUTURADO")
    print("=" * 72)
    if parecer:
        print(f"  síntese          : {parecer.sintese[:180]}")
        print(f"  valor estimado   : R$ {parecer.valor_estimado:,.2f}")
        print(f"  recomendação     : {parecer.recomendacao[:180]}")
        print(f"  pontos de atenção: {len(parecer.pontos_de_atencao)} item(ns)")
        for ponto in parecer.pontos_de_atencao[:3]:
            print(f"      - {ponto[:110]}")
    else:
        print("  a tarefa não devolveu objeto estruturado")

    uso = resultado.token_usage
    print(f"\n  {uso.successful_requests} chamadas ao modelo · "
          f"{uso.prompt_tokens + uso.completion_tokens} tokens · "
          f"US$ {uso.prompt_tokens / 1e6 * 0.20 + uso.completion_tokens / 1e6 * 1.20:.5f}")
    print("\nO valor chegou como número, e não como texto: é isso que permite ao")
    print("sistema de protocolo consumi-lo sem uma etapa de interpretação.")


if __name__ == "__main__":
    main()
