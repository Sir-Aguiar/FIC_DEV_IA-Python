# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: O processo hierárquico com gerente automático
# Seção 3.1 – O gerente criado pelo framework
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Três manifestações chegam sem rótulo, e ninguém diz qual especialista
trata cada uma. As tarefas são criadas sem o campo `agent`, a equipe recebe
`process=Process.hierarchical` e um `manager_llm`, e é o gerente criado pelo
CrewAI quem lê cada tarefa e decide a quem entregá-la.

Para ver a distribuição acontecer, o exemplo escuta o barramento de eventos
do CrewAI: cada uso da ferramenta de delegação do gerente informa o colega
escolhido, e o evento de início de tarefa diz a qual tarefa a delegação
pertence.
"""
from collections import defaultdict

from crewai import Crew, Process, Task
from crewai.events import TaskStartedEvent, ToolUsageFinishedEvent, crewai_event_bus

from ouvidoria import ESPECIALISTAS, MODELO, carregar_manifestacoes, custo

DELEGACOES: dict[str, list[str]] = defaultdict(list)
TAREFA_EM_CURSO = {"nome": ""}


@crewai_event_bus.on(TaskStartedEvent)
def marcar_tarefa(origem, evento) -> None:
    TAREFA_EM_CURSO["nome"] = evento.task_name


@crewai_event_bus.on(ToolUsageFinishedEvent)
def anotar_delegacao(origem, evento) -> None:
    """O gerente delega por meio de uma ferramenta interna, e cada uso dela
    carrega o nome do colega escolhido."""
    if evento.tool_name == "delegate_work_to_coworker":
        colega = str(evento.tool_args.get("coworker", "?")).strip()
        DELEGACOES[TAREFA_EM_CURSO["nome"]].append(colega)


def montar_tarefas(manifestacoes: list[dict]) -> list[Task]:
    # Nenhuma tarefa nomeia um agente. No processo sequencial isso seria um
    # erro; no hierárquico é o esperado, porque a atribuição cabe ao gerente.
    return [
        Task(
            name=m["id"],
            description=(
                f"Trate a manifestação {m['id']}, recebida pelo canal '{m['canal']}':\n\n"
                f"\"{m['texto']}\"\n\n"
                "Produza a minuta de resposta ao cidadão, em até 120 palavras."
            ),
            expected_output="Minuta de resposta ao cidadão, com o encaminhamento dado.",
        )
        for m in manifestacoes
    ]


def relatar(resultado, manifestacoes: list[dict]) -> None:
    esperado = {m["id"]: m["tipo_esperado"] for m in manifestacoes}
    print("=" * 72)
    print("A quem o gerente delegou cada manifestação")
    print("=" * 72)
    for saida in resultado.tasks_output:
        print(f"  {saida.name}  (área esperada: {esperado[saida.name]})")
        for colega in DELEGACOES.get(saida.name, []):
            print(f"      -> {colega}")
        print(f"      agente registrado na saída: {saida.agent}")
    uso = resultado.token_usage
    print("-" * 72)
    print(f"chamadas ao modelo: {uso.successful_requests}  |  tokens: {uso.total_tokens}"
          f"  |  custo: US$ {custo(uso):.5f}")


def main() -> None:
    manifestacoes = [m for m in carregar_manifestacoes() if m["id"] in ("M1", "M2", "M6")]
    equipe = Crew(
        agents=ESPECIALISTAS,
        tasks=montar_tarefas(manifestacoes),
        process=Process.hierarchical,
        manager_llm=MODELO,   # obrigatório: sem ele o processo hierárquico não existe
    )
    resultado = equipe.kickoff()
    relatar(resultado, manifestacoes)

    print("\n" + "=" * 72)
    print("Minuta produzida para a M2")
    print("=" * 72)
    for saida in resultado.tasks_output:
        if saida.name == "M2":
            print(saida.raw.strip()[:600])


if __name__ == "__main__":
    main()
