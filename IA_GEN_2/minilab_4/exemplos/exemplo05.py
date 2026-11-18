# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 05: Como uma equipe falha, provocado de propósito
# Seção 7 – Modos de falha em equipes de agentes
# Requisitos: pip install crewai openai python-dotenv
# ============================================================
"""Provoca as falhas próprias de uma equipe de agentes, e as mede.

As falhas da Aula 03 eram de um agente diante de ferramentas. As desta aula
são de coordenação: informação que não atravessa a cadeia, contexto que
cresce a cada etapa, agentes que conversam em vez de trabalhar e erro que
ganha autoridade ao ser repetido pelo agente seguinte.
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


def agente(papel: str, objetivo: str, historia: str, **extras) -> Agent:
    return Agent(role=papel, goal=objetivo, backstory=historia, llm=MODELO,
                 verbose=False, max_iter=extras.pop("max_iter", 5),
                 allow_delegation=extras.pop("allow_delegation", False), **extras)


def falha_1_contexto_que_infla() -> None:
    """Cada etapa recebe tudo o que veio antes, e o pedido cresce."""
    print("\n[1] O contexto que infla a cada etapa")
    a1 = agente("Analista Técnico", "Avaliar viabilidade técnica", "Engenheiro experiente.")
    a2 = agente("Analista Financeiro", "Avaliar custos", "Contador experiente.")
    a3 = agente("Parecerista", "Consolidar em parecer", "Procurador experiente.")

    t1 = Task(description="Analise a viabilidade técnica.\n\nDOSSIÊ:\n" + DOSSIE,
              expected_output="Análise em até dez linhas.", agent=a1)
    t2 = Task(description="Analise os custos.\n\nDOSSIÊ:\n" + DOSSIE,
              expected_output="Análise em até dez linhas.", agent=a2, context=[t1])
    t3 = Task(description="Consolide em parecer com recomendação.",
              expected_output="Parecer com recomendação explícita.",
              agent=a3, context=[t1, t2])

    equipe = Crew(agents=[a1, a2, a3], tasks=[t1, t2, t3],
                  process=Process.sequential, verbose=False)
    resultado = equipe.kickoff()
    uso = resultado.token_usage
    print(f"    3 tarefas, {uso.successful_requests} chamadas, "
          f"{uso.prompt_tokens} tokens de ENTRADA no total")
    print(f"    O dossiê tem cerca de {len(DOSSIE.split())} palavras. A entrada acumulada")
    print(f"    equivale a reenviá-lo várias vezes, porque cada etapa recarrega o")
    print(f"    que veio antes. É o preço da colaboração, e ele é linear no número")
    print(f"    de tarefas encadeadas.")


def falha_2_delegacao_que_vira_conversa() -> None:
    """Com delegação liberada, os agentes gastam chamadas conversando."""
    print("\n[2] A delegação que vira conversa")
    for rotulo, delegar in (("allow_delegation=False", False),
                            ("allow_delegation=True", True)):
        a1 = agente("Analista Técnico", "Avaliar viabilidade técnica",
                    "Engenheiro experiente.", allow_delegation=delegar)
        a2 = agente("Analista Financeiro", "Avaliar custos",
                    "Contador experiente.", allow_delegation=delegar)
        t1 = Task(description=("Avalie se o projeto é viável, considerando tanto o "
                               "lado técnico quanto o financeiro.\n\nDOSSIÊ:\n" + DOSSIE),
                  expected_output="Avaliação em até dez linhas.", agent=a1)
        equipe = Crew(agents=[a1, a2], tasks=[t1],
                      process=Process.sequential, verbose=False)
        inicio = time.perf_counter()
        resultado = equipe.kickoff()
        uso = resultado.token_usage
        custo = uso.prompt_tokens / 1e6 * 0.20 + uso.completion_tokens / 1e6 * 1.20
        print(f"    {rotulo:24} {uso.successful_requests} chamadas · "
              f"{uso.prompt_tokens + uso.completion_tokens} tokens · "
              f"{time.perf_counter() - inicio:.1f}s · US$ {custo:.5f}")


def falha_3_erro_que_atravessa_a_cadeia() -> None:
    """Um erro plantado na primeira etapa é repetido com mais autoridade."""
    print("\n[3] O erro que atravessa a cadeia e ganha autoridade")
    # A primeira tarefa recebe um dossiê adulterado, com um valor trocado.
    adulterado = DOSSIE.replace("R$ 1.870.000,00", "R$ 8.170.000,00")

    extrator = agente("Extrator", "Extrair os dados financeiros do dossiê",
                      "Você é técnico administrativo e transcreve valores.")
    parecerista = agente("Parecerista", "Emitir parecer sobre a contratação",
                         "Você é procurador e fundamenta seus pareceres.")

    t1 = Task(description="Extraia o valor estimado e a dotação disponível."
                          "\n\nDOSSIÊ:\n" + adulterado,
              expected_output="Os dois valores, em uma linha cada.", agent=extrator)
    t2 = Task(description="Emita parecer sobre a adequação orçamentária, a partir "
                          "da extração anterior.",
              expected_output="Parecer em até oito linhas, com recomendação.",
              agent=parecerista, context=[t1])

    equipe = Crew(agents=[extrator, parecerista], tasks=[t1, t2],
                  process=Process.sequential, verbose=False)
    resultado = equipe.kickoff()
    final = str(resultado)
    print(f"    valor real do dossiê: R$ 1.870.000,00")
    print(f"    valor plantado      : R$ 8.170.000,00")
    print(f"    o parecer final repete o valor errado? "
          f"{'SIM' if '8.170.000' in final or '8170000' in final else 'não'}")
    print(f"    o parecer questiona o valor recebido?  "
          f"{'sim' if any(p in final.lower() for p in ('divergên', 'conferir', 'confirmar', 'inconsist')) else 'NÃO'}")
    print(f"    {final.strip()[:200]}")


def falha_4_max_iter_sem_teto() -> None:
    """O padrão de vinte e cinco iterações é alto para tarefa de análise."""
    print("\n[4] O teto de iterações que ninguém alterou")
    print(f"    padrão de max_iter no CrewAI: {Agent.model_fields['max_iter'].default}")
    print(f"    padrão de max_rpm           : {Agent.model_fields['max_rpm'].default}")
    print(f"    padrão de max_execution_time: {Agent.model_fields['max_execution_time'].default}")
    print("    Um agente que hesita pode consumir vinte e cinco chamadas, cada uma")
    print("    recarregando o histórico. Sem max_rpm nem max_execution_time, não há")
    print("    teto de gasto nem de tempo — apenas o de iterações.")


if __name__ == "__main__":
    print("=" * 72)
    print("Como uma equipe de agentes falha")
    print("=" * 72)
    for funcao in (falha_1_contexto_que_infla, falha_2_delegacao_que_vira_conversa,
                   falha_3_erro_que_atravessa_a_cadeia, falha_4_max_iter_sem_teto):
        try:
            funcao()
        except Exception as erro:
            print(f"    interrompida: {type(erro).__name__} — {str(erro)[:110]}")
    print()
