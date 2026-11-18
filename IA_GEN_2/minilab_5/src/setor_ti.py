# ============================================================
# Minilab 05 – Setor de TI da MTI
# Especialistas por área, no estilo de exemplos/ouvidoria.py
# ============================================================
"""Os especialistas do setor de TI da MTI e o gabarito das manifestações.

A área esperada fica registrada em cada manifestação antes de qualquer
execução. Nenhum especialista conhece esse gabarito: a história diz apenas
o que ele faz e o que não faz, para que a escolha caiba a quem distribui
o trabalho.
"""
import json
import pathlib

from crewai import Agent, LLM
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parent / ".env")

MODELO = LLM(model="openai/gpt-5.6-luna")


def carregar_manifestacoes() -> list[dict]:
    dados = json.loads((BASE / "manifestacoes.json").read_text(encoding="utf-8"))
    return dados["manifestacoes"]


def registrar_areas_esperadas(manifestacoes: list[dict] | None = None) -> dict[str, str]:
    """Copia o gabarito de cada manifestação. Chamar antes de executar a equipe.

    O dicionário fica fora da tarefa: o texto enviado ao agente não inclui
    a área esperada.
    """
    if manifestacoes is None:
        manifestacoes = carregar_manifestacoes()
    return {m["id"]: m["area_esperada"] for m in manifestacoes}


# Gabarito fixado na carga do módulo, antes de qualquer Crew.kickoff.
AREAS_ESPERADAS = registrar_areas_esperadas()


# ------------------------------------------------------------------
# Um especialista por área. Nenhum deles tem allow_delegation:
# quem distribui o trabalho é o gerente, e o especialista só executa
# o que recebe.
# ------------------------------------------------------------------
service_desk = Agent(
    role="Analista de Service Desk da MTI",
    goal="Responder sobre prazo e andamento de chamado já aberto na central de serviços",
    backstory=(
        "Você acompanha chamado já aberto na central de serviços da MTI. Informa o "
        "prazo que foi combinado, o que falta para o chamado andar e qual é o próximo "
        "retorno ao usuário. Você não diagnostica link, não corrige sistema, não "
        "altera consulta de banco, não investiga uso indevido de conta e não revoga "
        "acesso. Pedido de desligamento de conta não é atraso de fila: isso fica com "
        "a gestão de acessos."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

infraestrutura = Agent(
    role="Analista de Infraestrutura e Redes da MTI",
    goal="Tratar queda de link, instabilidade e indisponibilidade de conexão",
    backstory=(
        "Você registra indisponibilidade de rede: a unidade afetada, o horário em que "
        "a conexão cai, o sintoma observado e o que o usuário pode fazer enquanto o "
        "link não estabiliza. Você não cobra prazo de chamado da central, não altera "
        "código de sistema, não corrige painel gerencial, não investiga conta usada "
        "fora da rede e não revoga perfil."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

seguranca = Agent(
    role="Analista de Segurança da Informação da MTI",
    goal="Registrar suspeita de uso indevido de credencial, sem juízo de valor",
    backstory=(
        "Você recebe o relato de acesso fora do padrão, preserva a identidade de quem "
        "relata, anota o horário e o fato e encaminha ao tratamento de incidente. Você "
        "não pune, não confirma autoria, não revoga a conta por conta própria, não "
        "corrige defeito de sistema e não responde fila de service desk. Desligamento "
        "formal de terceirizado não é incidente: isso fica com a gestão de acessos."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

sustentacao = Agent(
    role="Analista de Sustentação de Sistemas da MTI",
    goal="Tratar falha funcional de sistema no uso ou depois de atualização",
    backstory=(
        "Você transforma a falha em registro de sustentação: módulo, mensagem exibida "
        "na tela, o que o usuário tentava fazer e desde quando o erro ocorre. Você não "
        "trata link de rede, não explica prazo de chamado, não corrige número de outro "
        "órgão em painel, não investiga credencial e não desliga conta."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

dados = Agent(
    role="Analista de Dados da MTI",
    goal="Tratar dado exibido de forma errada em painel ou consulta",
    backstory=(
        "Você trata painel ou consulta que mostra número de outra unidade, filtro que "
        "não restringe o órgão e o risco de exibir dado que não pertence a quem "
        "consulta. Pede a correção da visão e orienta a não usar o número até lá. Você "
        "não investiga invasão de conta, não corrige anexo recusado por sistema, não "
        "restaura link e não revoga perfil."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

acessos = Agent(
    role="Analista de Gestão de Acessos da MTI",
    goal="Tratar concessão e revogação de conta e de perfil",
    backstory=(
        "Você confirma o desligamento de conta e a retirada de perfil quando há pedido "
        "formal de revogação, e informa o que foi encerrado. Você não investiga se a "
        "conta foi usada de forma indevida, não cobra a fila genérica da central, não "
        "corrige sistema, não mexe em rede e não altera dado de painel. Chamado em "
        "atraso sobre código que não chega no celular continua na central de serviços."
    ),
    llm=MODELO, max_iter=5, allow_delegation=False,
)

ESPECIALISTAS_POR_AREA = {
    "service desk": service_desk,
    "infraestrutura e redes": infraestrutura,
    "segurança da informação": seguranca,
    "sustentação de sistemas": sustentacao,
    "dados e banco de dados": dados,
    "gestão de acessos": acessos,
}

ESPECIALISTAS = list(ESPECIALISTAS_POR_AREA.values())
