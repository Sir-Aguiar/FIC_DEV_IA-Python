# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: A primeira equipe e a leitura do consumo
# Seção 2.1 – Componentes do CrewAI
# Requisitos: pip install crewai openai python-dotenv
# ============================================================
"""Monta a menor equipe possível e mostra o que ela consumiu.

Duas ideias organizam este exemplo. A primeira é que um agente do CrewAI se
define por três textos — papel, objetivo e história — que juntos formam o
prompt de sistema daquele agente. A segunda é que toda execução devolve um
objeto com o consumo real, e ler esse objeto desde o primeiro exemplo é o
que evita descobrir o custo apenas na fatura.
"""
import pathlib
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

# O CrewAI encaminha as chamadas por uma camada de compatibilidade, e por isso
# o modelo é identificado com o prefixo do provedor.
MODELO = LLM(model="openai/gpt-5.6-luna")

DOSSIE = (BASE / "dossie_projeto.md").read_text(encoding="utf-8")


def main() -> None:
    analista = Agent(
        role="Analista de Tecnologia da Informação",
        goal="Avaliar a viabilidade técnica de projetos de sistemas do Estado",
        backstory=(
            "Você é servidor da Secretaria de Infraestrutura de Mato Grosso e "
            "acompanha contratações de tecnologia há mais de uma década. Já viu "
            "projetos bem orçados fracassarem por falta de equipe própria, e por "
            "isso examina sempre a capacidade de execução antes do preço."
        ),
        llm=MODELO,
        verbose=False,
        # Teto de iterações do agente. O padrão da biblioteca é 25, valor alto
        # demais para uma tarefa de análise e caro quando o agente hesita.
        max_iter=5,
        allow_delegation=False,
    )

    analise = Task(
        description=(
            "Analise a viabilidade técnica do projeto descrito no dossiê abaixo. "
            "Trate da capacidade da equipe própria, do prazo de implantação e dos "
            "riscos de migração.\n\nDOSSIÊ:\n" + DOSSIE
        ),
        # O resultado esperado entra no prompt e é a instrução que mais
        # determina a forma da saída, como mede a Seção 5.
        expected_output=(
            "Análise em até quinze linhas, citando os números do dossiê e "
            "terminando com um juízo sobre a viabilidade técnica."
        ),
        agent=analista,
    )

    equipe = Crew(agents=[analista], tasks=[analise],
                  process=Process.sequential, verbose=False)

    resultado = equipe.kickoff()

    print("=" * 72)
    print("PARECER TÉCNICO")
    print("=" * 72)
    print(str(resultado).strip()[:900])

    uso = resultado.token_usage
    entrada, saida = uso.prompt_tokens, uso.completion_tokens
    custo = entrada / 1e6 * 0.20 + saida / 1e6 * 1.20
    print("\n" + "=" * 72)
    print(f"chamadas ao modelo : {uso.successful_requests}")
    print(f"tokens de entrada  : {entrada}")
    print(f"tokens de saída    : {saida}")
    print(f"custo desta execução: US$ {custo:.5f}")
    print("\nO custo de um agente cresce com o número de chamadas, e o número de")
    print("chamadas depende de quantas vezes ele decide que ainda não terminou.")


if __name__ == "__main__":
    main()
