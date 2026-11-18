# ============================================================
# Minilab 4 — equipe de três agentes sobre o RAG 2025 da MTI
# A rubrica em src/dados/rubrica.json foi escrita antes desta
# execução e não é aplicada aqui: ela mede o parecer depois.
# ============================================================
"""Monta a equipe que analisa o dossiê do Programa 536 em três aspectos.

O técnico lê disponibilidade e entregas. O financeiro lê as duas séries
orçamentárias do mesmo RAG. O parecerista recebe as duas análises pelo
context e devolve um parecer no esquema Parecer. Nenhum agente delega,
porque a colaboração desta equipe é o encadeamento das tarefas, não um
pedido de ajuda no meio do passo.
"""
import pathlib
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field


BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parent / ".env")

# Mesmo modelo dos exemplos da aula. O prefixo openai/ é exigido pela
# camada de compatibilidade do CrewAI.
MODELO = LLM(model="openai/gpt-5.6-luna")

DOSSIE = (BASE / "dados" / "dossie_projeto.md").read_text(encoding="utf-8")

# O padrão de max_iter da biblioteca é 25. Nesta análise não há ferramenta:
# uma chamada basta para redigir e as seguintes só recarregam o histórico.
# Cinco deixa margem para o formato da saída e corta a hesitação cara.
MAX_ITER = 5

# Três agentes em sequência, sem ferramenta, fazem poucas requisições.
# Dez por minuto cabe nessa cadência e segura a cota se um agente repetir
# o passo até o teto de iterações.
MAX_RPM = 10

# Uma página de dossiê não justifica espera longa. Cento e oitenta segundos
# por agente cobrem a redação e um reintento, e encerram o processo se a
# chamada travar. O tempo é por agente, não da equipe inteira.
MAX_EXECUTION_TIME = 180


class Parecer(BaseModel):
    """Forma da saída da última tarefa, consumível sem reinterpretar o texto."""

    sintese: str = Field(description="Resumo do caso em até três frases")
    aspectos_tecnicos: str = Field(description="Disponibilidade, satisfação e entregas")
    aspectos_financeiros: str = Field(description="As duas séries orçamentárias do RAG")
    aspectos_juridicos: str = Field(description="LOA, LGPD, selo e contratos vigentes")
    recomendacao: str = Field(description="Recomendação explícita e fundamentada")
    pontos_de_atencao: list[str] = Field(description="Riscos que exigem decisão superior")


def agente(papel: str, objetivo: str, historia: str) -> Agent:
    """Cria um agente com os três tetos de contenção já justificados acima."""
    return Agent(
        role=papel,
        goal=objetivo,
        backstory=historia,
        llm=MODELO,
        verbose=False,
        max_iter=MAX_ITER,
        max_rpm=MAX_RPM,
        max_execution_time=MAX_EXECUTION_TIME,
        allow_delegation=False,
    )


def montar_equipe() -> Crew:
    """Encadeia técnico, financeiro e parecerista. Só a última tarefa é estruturada."""
    tecnico = agente(
        "Analista Técnico",
        "Avaliar disponibilidade, satisfação e entregas do Programa 536",
        (
            "Você é engenheiro da MTI e acompanha o painel dos 19 serviços "
            "críticos desde a implantação do monitoramento. Na carreira, "
            "aprendeu a confrontar o realizado com a meta de 99,80% e a nomear "
            "o mês que puxou a média para baixo antes de falar em arquitetura."
        ),
    )

    financeiro = agente(
        "Analista Financeiro",
        "Avaliar a execução orçamentária do Programa 536 no exercício de 2025",
        (
            "Você é contador da execução do PPA e já devolveu relatório em que "
            "o quadro e o texto não fechavam a mesma conta. Por isso registra "
            "as duas séries oficiais do RAG, a do quadro e a da análise, sem "
            "escolher uma delas no lugar da outra."
        ),
    )

    parecerista = agente(
        "Parecerista",
        "Consolidar as análises em parecer com recomendação para a diretoria",
        (
            "Você é procurador que há anos assina parecer sobre prestação de "
            "contas de empresa estatal. Só recomenda o que o RAG público "
            "sustenta, e aponta contrato ainda em tramitação e dado sigiloso "
            "que o dossiê não abre."
        ),
    )

    analise_tecnica = Task(
        description=(
            "Analise a viabilidade técnica do Programa 536 com base apenas no "
            "dossiê. Trate da disponibilidade realizada e da meta, dos meses "
            "de março, abril e julho, da satisfação e das entregas digitais."
            "\n\nDOSSIÊ:\n" + DOSSIE
        ),
        expected_output=(
            "Análise em até quinze linhas, citando 99,47%, 99,80% e 89,82%."
        ),
        agent=tecnico,
    )

    analise_financeira = Task(
        description=(
            "Analise a execução orçamentária do programa. Mostre a dotação "
            "inicial e as duas apurações de dotação atualizada, empenhado, "
            "PPD e COFD, sem fundi-las num único número."
            "\n\nDOSSIÊ:\n" + DOSSIE
        ),
        expected_output=(
            "Análise em até quinze linhas, citando R$ 101.311.882,00, "
            "132,57% e 138,52%."
        ),
        agent=financeiro,
        context=[analise_tecnica],
    )

    consolidacao = Task(
        description=(
            "Consolide as análises técnica e financeira em um parecer único "
            "para a diretoria da MTI. Inclua o aspecto jurídico do dossiê "
            "(LOA, LGPD, Selo Diamante e contratos vigentes) e termine com "
            "recomendação explícita."
        ),
        expected_output=(
            "Parecer com síntese, três aspectos, recomendação e pontos de "
            "atenção, citando os números do dossiê."
        ),
        agent=parecerista,
        context=[analise_tecnica, analise_financeira],
        output_pydantic=Parecer,
    )

    return Crew(
        agents=[tecnico, financeiro, parecerista],
        tasks=[analise_tecnica, analise_financeira, consolidacao],
        process=Process.sequential,
        verbose=False,
    )


def main() -> None:
    """Executa a equipe. A rubrica não entra neste fluxo."""
    resultado = montar_equipe().kickoff()
    parecer = resultado.pydantic

    print("=" * 72)
    print("PARECER ESTRUTURADO")
    print("=" * 72)
    if parecer:
        print(parecer.model_dump_json(indent=2, ensure_ascii=False))
    else:
        print(str(resultado).strip())


if __name__ == "__main__":
    main()
