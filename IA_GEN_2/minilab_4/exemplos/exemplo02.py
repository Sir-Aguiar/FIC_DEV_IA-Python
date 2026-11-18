# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Orçamento do agente e instrumentação por step_callback
# Seção 3.2 – Agentes no CrewAI: limites de execução
# Requisitos: pip install crewai openai python-dotenv
# ============================================================
"""Mostra os parâmetros que limitam um agente e como observar sua execução.

A Aula 03 instalou limites no agente do LangChain por meio de middleware. No
CrewAI os limites são campos do próprio agente, e a observação se faz por uma
função de retorno chamada a cada passo. O efeito é o mesmo, e vale conhecer
as duas formas porque a escolha do framework não deve implicar abrir mão da
contenção.
"""
import pathlib
import time
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = LLM(model="openai/gpt-5.6-luna")
DOSSIE = (BASE / "dossie_projeto.md").read_text(encoding="utf-8")


class Observador:
    """Registra cada passo que o agente dá, com o instante em que ocorreu."""

    def __init__(self) -> None:
        self.passos: list[tuple[float, str]] = []
        self.inicio = time.perf_counter()

    def __call__(self, passo) -> None:
        decorrido = time.perf_counter() - self.inicio
        descricao = type(passo).__name__
        # O objeto de passo muda de forma conforme a etapa; a leitura defensiva
        # evita que a instrumentação derrube a execução que ela observa.
        texto = getattr(passo, "output", None) or getattr(passo, "text", "")
        self.passos.append((decorrido, f"{descricao}: {str(texto)[:60]}"))


def parametros_de_orcamento() -> None:
    """Os campos que impedem um agente de gastar sem teto."""
    print("=" * 72)
    print("Parâmetros de contenção de um agente do CrewAI")
    print("=" * 72)
    referencia = {
        "max_iter": "quantas vezes o agente pode repensar antes de entregar",
        "max_rpm": "teto de requisições por minuto, protege contra estouro de cota",
        "max_execution_time": "tempo máximo em segundos, protege contra travamento",
        "max_retry_limit": "quantas vezes repetir após erro (padrão 2)",
        "respect_context_window": "resume em silêncio quando o contexto estoura",
        "allow_delegation": "permite que o agente peça ajuda a outro da equipe",
    }
    for campo, explicacao in referencia.items():
        existe = campo in Agent.model_fields
        padrao = Agent.model_fields[campo].default if existe else "—"
        print(f"  {campo:24} padrão={str(padrao):8} {explicacao}")

    print("\nO padrão de max_iter é o que mais surpreende. Vinte e cinco iterações")
    print("em um agente que hesita significam vinte e cinco chamadas ao modelo,")
    print("cada uma carregando o histórico inteiro. É o primeiro valor a reduzir,")
    print("e a Aula 03 já mediu o que acontece quando um agente decide insistir.")


def execucao_observada() -> None:
    """A mesma tarefa com teto apertado e com teto folgado.

    O `step_callback` registra passos intermediários, que só existem quando o
    agente recorre a ferramentas. Numa análise puramente textual como esta ele
    não dispara, e o consumo precisa ser lido no `token_usage` — diferença que
    convém conhecer antes de concluir que a instrumentação não funciona.
    """
    print("\n" + "=" * 72)
    print("Execução observada passo a passo")
    print("=" * 72)

    for rotulo, teto in (("max_iter=2", 2), ("max_iter=8", 8)):
        observador = Observador()
        analista = Agent(
            role="Analista Financeiro",
            goal="Avaliar a adequação orçamentária de projetos do Estado",
            backstory=("Você é contador da Secretaria de Fazenda e examina, antes "
                       "de tudo, se o valor pretendido cabe na dotação do exercício."),
            llm=MODELO, verbose=False, max_iter=teto, max_rpm=20,
            max_execution_time=120, allow_delegation=False,
            step_callback=observador,
        )
        tarefa = Task(
            description=("Avalie a adequação orçamentária do projeto do dossiê, "
                         "comparando o valor estimado com a dotação disponível."
                         "\n\nDOSSIÊ:\n" + DOSSIE),
            expected_output="Análise em até dez linhas, com os valores do dossiê.",
            agent=analista,
        )
        equipe = Crew(agents=[analista], tasks=[tarefa],
                      process=Process.sequential, verbose=False)
        resultado = equipe.kickoff()
        uso = resultado.token_usage
        # O step_callback só dispara em passos intermediários, que existem
        # quando o agente usa ferramentas. Numa tarefa puramente textual ele
        # não registra nada, e é o token_usage que informa o consumo real.
        print(f"\n  {rotulo}: {len(observador.passos)} passos intermediários, "
              f"{uso.successful_requests} chamadas ao modelo, "
              f"{uso.prompt_tokens + uso.completion_tokens} tokens")
        print(f"    {str(resultado).strip()[:150]}")


if __name__ == "__main__":
    parametros_de_orcamento()
    execucao_observada()
