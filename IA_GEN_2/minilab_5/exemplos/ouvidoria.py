# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Apoio: os agentes da Ouvidoria e o carregador das manifestações
# Seções 3 a 5
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Os especialistas da Ouvidoria-Geral e o acesso às manifestações.

Os exemplos desta aula montam a mesma equipe de maneiras diferentes, e por
isso os agentes vivem aqui, em um único lugar. Nenhum deles conhece o processo
em que vai trabalhar: é a `Crew` que decide se eles recebem as tarefas em
ordem fixa ou por meio de um gerente, e é o `Flow` que decide quando a equipe
inteira é chamada.
"""
import json
import pathlib
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, LLM
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

# O CrewAI identifica o modelo com o prefixo do provedor, como na Aula 04.
MODELO = LLM(model="openai/gpt-5.6-luna")
PRECO_ENTRADA, PRECO_SAIDA = 0.20, 1.20  # US$ por milhão de tokens


def carregar_manifestacoes() -> list[dict]:
    dados = json.loads((BASE / "manifestacoes.json").read_text(encoding="utf-8"))
    return dados["manifestacoes"]


def custo(token_usage) -> float:
    """Converte o consumo relatado pelo CrewAI em dólares."""
    return (token_usage.prompt_tokens / 1e6 * PRECO_ENTRADA
            + token_usage.completion_tokens / 1e6 * PRECO_SAIDA)


# ------------------------------------------------------------------
# Os três especialistas. Repare que nenhum deles tem allow_delegation:
# no processo hierárquico, quem delega é o gerente, e os especialistas
# apenas executam o que recebem.
# ------------------------------------------------------------------
atendente = Agent(
    role="Analista de Atendimento ao Cidadão",
    goal="Responder reclamações e solicitações sobre prazos e andamento de serviços",
    backstory=(
        "Você trabalha na Ouvidoria-Geral da Controladoria-Geral do Estado de Mato "
        "Grosso e conhece os prazos de cada serviço estadual. Responde ao cidadão com "
        "o prazo correto, o número de protocolo e o próximo passo, sem prometer o que "
        "não pode garantir."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

juridico = Agent(
    role="Analista Jurídico da Ouvidoria",
    goal="Tratar denúncias e questões de proteção de dados pessoais com o rigor que a lei exige",
    backstory=(
        "Você é analista jurídico da Ouvidoria-Geral e aplica a Lei nº 13.709/2018 "
        "(LGPD) e a Lei nº 12.527/2011 (LAI). Em denúncias, preserva a identidade do "
        "denunciante, registra o fato sem juízo de valor e indica o encaminhamento à "
        "Corregedoria."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

tecnico = Agent(
    role="Analista de Sistemas da Ouvidoria",
    goal="Tratar manifestações sobre indisponibilidade e falhas dos sistemas do Estado",
    backstory=(
        "Você é analista de sistemas e faz a ponte entre a Ouvidoria e a equipe de "
        "tecnologia. Transforma a reclamação do cidadão em um registro técnico com "
        "horário, sistema afetado e sintoma, e informa ao cidadão o que fazer enquanto "
        "o problema não é resolvido."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

ESPECIALISTAS = [atendente, juridico, tecnico]
