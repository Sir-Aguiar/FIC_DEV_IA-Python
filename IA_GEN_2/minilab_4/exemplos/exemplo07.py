# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 07: Ferramenta de busca externa na equipe (ilustrativo)
# Seção 6 – Ferramentas do CrewAI
# Requisitos: pip install crewai crewai-tools
# ============================================================
"""Exemplo ILUSTRATIVO: um agente com acesso a busca na web.

> Este arquivo não é executado na preparação da aula. A `SerperDevTool`
> depende de `SERPER_API_KEY`, chave de um serviço de terceiro que o curso
> não mantém, e a `WebsiteSearchTool` constrói um índice de embeddings a
> cada execução, o que a torna cobrada por uso. Nenhuma etapa do Mini LAB
> depende deste arquivo, e o aluno com chave própria pode executá-lo.

O ponto pedagógico não é a busca em si, e sim o custo escondido de certas
ferramentas do catálogo. Uma ferramenta que apenas consulta uma API custa a
chamada; uma que constrói índice vetorial sobre o conteúdo recuperado custa
a chamada, a geração dos embeddings e o armazenamento — e nada no nome dela
indica essa diferença.
"""
import os

from crewai import Agent, Crew, LLM, Process, Task


def main() -> None:
    if not os.getenv("SERPER_API_KEY"):
        raise SystemExit(
            "Exemplo ilustrativo: defina SERPER_API_KEY para executá-lo.\n"
            "O curso não mantém essa chave, e nenhuma etapa do Mini LAB depende "
            "deste arquivo. A alternativa executável é a busca em acervo local, "
            "conforme o ferramentas.py da Aula 03."
        )

    from crewai_tools import SerperDevTool

    pesquisador = Agent(
        role="Pesquisador de Mercado",
        goal="Levantar preços praticados em contratações semelhantes",
        backstory=("Você é servidor da área de compras e pesquisa preços de "
                   "referência antes de cada estimativa."),
        llm=LLM(model="openai/gpt-5.6-luna"),
        tools=[SerperDevTool()],
        max_iter=5,
        # Sem max_rpm, uma ferramenta de busca pode esgotar a cota do serviço
        # em uma única execução da equipe.
        max_rpm=10,
        allow_delegation=False,
    )

    tarefa = Task(
        description=("Pesquise preços de referência para sistemas de protocolo "
                     "eletrônico contratados por órgãos públicos brasileiros."),
        expected_output="Três referências com valor e fonte.",
        agent=pesquisador,
    )

    equipe = Crew(agents=[pesquisador], tasks=[tarefa],
                  process=Process.sequential, verbose=False)
    resultado = equipe.kickoff()
    print(str(resultado)[:600])
    print(f"\nconsumo: {resultado.token_usage}")


if __name__ == "__main__":
    main()
