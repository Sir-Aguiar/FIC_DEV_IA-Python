# ============================================================
# Minilab 05 – Duas formas de gerente no setor de tecnologia
# da informação da Empresa Mato-grossense de Tecnologia da Informação
# ============================================================
"""Compara o gerente criado pelo framework com o gerente escrito por nós.

As tarefas não nomeiam especialista. A área esperada fica de fora do texto,
porque foi registrada antes da execução e serve só de gabarito. A escuta
dos eventos de delegação segue o exemplo 01 da aula.
"""
import json
from collections import defaultdict

from crewai import Agent, Crew, Process, Task
from crewai.events import TaskStartedEvent, ToolUsageFinishedEvent, crewai_event_bus

from setor_ti import AREAS_ESPERADAS, ESPECIALISTAS, MODELO, carregar_manifestacoes


# Cada uso da ferramenta de delegação entra na lista da tarefa que estava
# em curso. A lista é esvaziada entre uma execução e a outra.
DELEGACOES: dict[str, list[str]] = defaultdict(list)
TAREFA_EM_CURSO = {"nome": ""}

ENTREGA = "delegate_work_to_coworker"
PERGUNTA = "ask_question_to_coworker"


@crewai_event_bus.on(TaskStartedEvent)
def marcar_tarefa(origem, evento) -> None:
    """Guarda o nome da tarefa que começou, para saber a qual manifestação
    a próxima delegação pertence."""
    TAREFA_EM_CURSO["nome"] = evento.task_name or ""


@crewai_event_bus.on(ToolUsageFinishedEvent)
def anotar_delegacao(origem, evento) -> None:
    """O gerente entrega o trabalho por uma ferramenta interna. O argumento
    coworker traz o papel do especialista escolhido."""
    nome_ferramenta = str(evento.tool_name).strip().lower().replace(" ", "_")
    if nome_ferramenta not in {ENTREGA, PERGUNTA}:
        return

    argumentos = evento.tool_args
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos)
        except json.JSONDecodeError:
            argumentos = {}

    colega = "?"
    if isinstance(argumentos, dict):
        colega = str(
            argumentos.get("coworker") or argumentos.get("co_worker") or "?"
        ).strip()

    tarefa = (getattr(evento, "task_name", None) or TAREFA_EM_CURSO["nome"] or "").strip()
    DELEGACOES[tarefa].append(colega)


def montar_tarefas(manifestacoes: list[dict]) -> list[Task]:
    """Nenhuma tarefa recebe um agente. No processo hierárquico a escolha
    é do gerente. A área esperada não entra na descrição."""
    return [
        Task(
            name=m["id"],
            description=(
                f"Trate a manifestação {m['id']}, recebida pelo canal '{m['canal']}':\n\n"
                f"\"{m['texto']}\"\n\n"
                "Produza a minuta de resposta, em até 120 palavras."
            ),
            expected_output="Minuta de resposta, com o encaminhamento dado.",
        )
        for m in manifestacoes
    ]


def chamadas_do_modelo() -> int:
    """Lê o contador do modelo compartilhado por todos os agentes.

    O total que a equipe publica soma esse mesmo contador uma vez por
    agente. A diferença antes e depois da execução é o número de chamadas
    que de fato ocorreram.
    """
    return MODELO.get_token_usage_summary().successful_requests


def executar(equipe: Crew) -> tuple[object, int]:
    """Roda uma equipe e devolve o resultado junto com as chamadas dela."""
    DELEGACOES.clear()
    TAREFA_EM_CURSO["nome"] = ""
    antes = chamadas_do_modelo()
    resultado = equipe.kickoff()
    return resultado, chamadas_do_modelo() - antes


def identificar(nome: str, identificadores: list[str]) -> str:
    """Casa o nome visto no evento com o identificador da manifestação."""
    nome = (nome or "").strip()
    if nome in identificadores:
        return nome
    for identificador in identificadores:
        if nome.startswith(identificador):
            return identificador
    return nome or "?"


def tabela(resultado, manifestacoes: list[dict]) -> list[dict]:
    """Uma linha por manifestação: gabarito e especialistas consultados,
    na ordem em que o gerente os chamou."""
    identificadores = [m["id"] for m in manifestacoes]
    por_tarefa: dict[str, list[str]] = defaultdict(list)
    for nome, colegas in DELEGACOES.items():
        por_tarefa[identificar(nome, identificadores)].extend(colegas)

    linhas = []
    for manifestacao in manifestacoes:
        identificador = manifestacao["id"]
        linhas.append(
            {
                "id": identificador,
                "area_esperada": AREAS_ESPERADAS[identificador],
                "consultados": por_tarefa.get(identificador, []),
            }
        )
    return linhas


def imprimir_tabela(titulo: str, linhas: list[dict], chamadas: int) -> None:
    print("=" * 72)
    print(titulo)
    print("=" * 72)
    for linha in linhas:
        distintos = list(dict.fromkeys(linha["consultados"]))
        print(f"  {linha['id']}  (área esperada: {linha['area_esperada']})")
        if linha["consultados"]:
            for colega in linha["consultados"]:
                print(f"      -> {colega}")
        else:
            print("      -> nenhuma delegação observada")
        if len(distintos) > 1:
            print(f"      consultou {len(distintos)} especialistas")
    print("-" * 72)
    print(f"chamadas ao modelo nesta execução: {chamadas}")
    print()


def mais_de_um_especialista(linhas: list[dict]) -> list[str]:
    """Manifestações em que a lista de consultas tem mais de um papel distinto."""
    return [
        linha["id"]
        for linha in linhas
        if len(set(linha["consultados"])) > 1
    ]


# O gerente escrito carrega a regra do setor na história. Ele não entra
# na lista de especialistas: no processo hierárquico ele só distribui.
coordenador = Agent(
    role="Coordenador de Triagem do Setor de Tecnologia da Informação",
    goal=(
        "Entregar cada manifestação a um único especialista e devolver "
        "a minuta dele sem reescrevê-la"
    ),
    backstory=(
        "Você coordena a triagem do setor de tecnologia da informação da "
        "Empresa Mato-grossense de Tecnologia da Informação. A regra da casa "
        "é uma só: cada manifestação vai a um único especialista, escolhido "
        "pelo assunto. Prazo e andamento de chamado já aberto vão ao Analista "
        "de Service Desk da MTI. Queda de link e instabilidade de conexão vão "
        "ao Analista de Infraestrutura e Redes da MTI. Uso indevido de "
        "credencial e acesso fora do padrão vão ao Analista de Segurança da "
        "Informação da MTI. Falha de tela, de módulo ou de anexo vão ao "
        "Analista de Sustentação de Sistemas da MTI. Número de outro órgão em "
        "painel, ou filtro que não restringe a unidade, vão ao Analista de "
        "Dados da MTI. Concessão e revogação de conta ou de perfil vão ao "
        "Analista de Gestão de Acessos da MTI. Chamado atrasado sobre código "
        "que não chega no celular permanece com o Analista de Service Desk da "
        "MTI. Desligamento formal de conta não é incidente de segurança. Você "
        "não consulta mais de um especialista para a mesma manifestação e "
        "entrega a minuta do especialista como resposta final, sem reescrevê-la."
    ),
    llm=MODELO,
    allow_delegation=True,
)


def main() -> None:
    # O gabarito já existe em AREAS_ESPERADAS, montado na importação,
    # antes destas duas execuções.
    manifestacoes = carregar_manifestacoes()

    print("Execução 1: gerente criado pelo framework.", flush=True)
    equipe_automatica = Crew(
        agents=ESPECIALISTAS,
        tasks=montar_tarefas(manifestacoes),
        process=Process.hierarchical,
        manager_llm=MODELO,
        verbose=False,
    )
    resultado_automatico, chamadas_automaticas = executar(equipe_automatica)
    linhas_automaticas = tabela(resultado_automatico, manifestacoes)
    imprimir_tabela(
        "Gerente criado pelo framework",
        linhas_automaticas,
        chamadas_automaticas,
    )

    print("Execução 2: gerente escrito com a regra do setor.", flush=True)
    equipe_escrita = Crew(
        agents=ESPECIALISTAS,
        tasks=montar_tarefas(manifestacoes),
        process=Process.hierarchical,
        manager_agent=coordenador,
        verbose=False,
    )
    resultado_escrito, chamadas_escritas = executar(equipe_escrita)
    linhas_escritas = tabela(resultado_escrito, manifestacoes)
    imprimir_tabela(
        "Gerente escrito com a regra do setor",
        linhas_escritas,
        chamadas_escritas,
    )

    varias = mais_de_um_especialista(linhas_automaticas)
    print("=" * 72)
    print(
        "Manifestações em que o gerente automático consultou "
        f"mais de um especialista: {len(varias)} de {len(linhas_automaticas)}"
    )
    if varias:
        print("  " + ", ".join(varias))
    print("=" * 72)


if __name__ == "__main__":
    main()
