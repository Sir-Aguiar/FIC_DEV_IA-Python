# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: O gerente definido pelo programador
# Seção 3.2 – O gerente como agente da equipe
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""O mesmo trabalho do exemplo01, agora com `manager_agent` no lugar de
`manager_llm`. O gerente passa a ser um agente comum, com papel, objetivo e
história escritos pelo programador, e é na história que entra a regra de
distribuição da Ouvidoria: cada manifestação vai a um único especialista,
escolhido pelo assunto.

A comparação com o exemplo01 mostra o que a instrução do gerente muda no
número de delegações e no consumo.
"""
from crewai import Agent, Crew, Process

from exemplo01 import DELEGACOES, montar_tarefas, relatar
from ouvidoria import ESPECIALISTAS, MODELO, carregar_manifestacoes

ouvidor = Agent(
    role="Ouvidor-Geral Adjunto",
    goal="Distribuir cada manifestação ao especialista correto e devolver a minuta dele ao cidadão",
    backstory=(
        "Você coordena a triagem da Ouvidoria-Geral. A regra da casa é uma só: cada "
        "manifestação é entregue a um único especialista, escolhido pelo assunto. "
        "Prazos e andamento de serviços vão ao Analista de Atendimento ao Cidadão; "
        "denúncias e qualquer questão de dados pessoais vão ao Analista Jurídico da "
        "Ouvidoria; falhas de sistema e do portal vão ao Analista de Sistemas da "
        "Ouvidoria. Você não consulta mais de um especialista para a mesma "
        "manifestação e entrega a minuta do especialista como resposta final, sem "
        "reescrevê-la."
    ),
    llm=MODELO,
    allow_delegation=True,   # o gerente é o único que delega
)


def main() -> None:
    manifestacoes = [m for m in carregar_manifestacoes() if m["id"] in ("M1", "M2", "M6")]
    equipe = Crew(
        agents=ESPECIALISTAS,     # o gerente não entra nesta lista
        tasks=montar_tarefas(manifestacoes),
        process=Process.hierarchical,
        manager_agent=ouvidor,
    )
    DELEGACOES.clear()
    resultado = equipe.kickoff()
    relatar(resultado, manifestacoes)


if __name__ == "__main__":
    main()
