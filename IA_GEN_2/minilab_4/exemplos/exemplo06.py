# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 06: A equipe com as barreiras que o órgão exige
# Seção 8 – Nota técnica com ancoragem numérica
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""A equipe de três agentes com contenção, verificação e registro.

A Seção 7 mostrou que o erro plantado na primeira etapa atravessa a cadeia
sem ser questionado. Este exemplo instala a barreira que o intercepta: um
guardrail de ancoragem numérica, que confere cada valor do parecer contra o
dossiê antes de aceitar a tarefa. Acrescenta ainda orçamento por agente e um
registro do que cada etapa consumiu.
"""
import json
import pathlib
import re
import time
import warnings
from typing import Any, Tuple

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = LLM(model="openai/gpt-5.6-luna")
DOSSIE = (BASE / "dossie_projeto.md").read_text(encoding="utf-8")

# Valores que o dossiê autoriza, mais os obtidos por soma, subtração e
# multiplicação por prazos contratuais. É a lista contra a qual o parecer
# é conferido.
VALORES_DOSSIE = [1_870_000, 224_400, 310_000, 1_400_000, 600_000, 340_000, 2_100]
PRAZOS = [4, 12, 14, 48]


def _autorizados() -> set[int]:
    base = set(VALORES_DOSSIE)
    derivados = set(base)
    for a in base:
        for b in base:
            derivados.add(a + b)
            derivados.add(abs(a - b))
        for prazo in PRAZOS:
            derivados.add(a * prazo)
    return derivados


AUTORIZADOS = _autorizados()


class NotaTecnica(BaseModel):
    """A forma final da nota técnica que segue ao Secretário."""

    sintese: str = Field(description="Resumo do caso em até três frases")
    valor_estimado: float = Field(description="Valor estimado da contratação")
    dotacao_disponivel: float = Field(description="Dotação disponível no exercício")
    recomendacao: str = Field(description="Recomendação explícita e fundamentada")
    pontos_de_atencao: list[str] = Field(description="Riscos que exigem decisão superior")


def ancoragem_numerica(saida) -> Tuple[bool, Any]:
    """Confere se todo valor relevante da nota consta do dossiê.

    Esta é a barreira contra a falha demonstrada na Seção 7, em que o erro da
    primeira etapa é repetido com mais autoridade pela última. Ela roda em
    código, depois de o agente produzir a saída e antes de a tarefa ser dada
    por concluída, e devolve ao agente a instrução de corrigir.
    """
    nota = getattr(saida, "pydantic", None)
    if nota is None:
        return (True, saida)

    for campo, valor in (("valor_estimado", nota.valor_estimado),
                         ("dotacao_disponivel", nota.dotacao_disponivel)):
        if round(valor) not in AUTORIZADOS:
            return (False, f"O campo {campo} traz {valor:.2f}, que não consta do "
                           f"dossiê nem decorre de cálculo sobre seus valores. "
                           f"Releia o dossiê e corrija.")

    texto = " ".join([nota.sintese, nota.recomendacao, *nota.pontos_de_atencao])
    for bruto in re.findall(r"\d[\d.]*(?:,\d{2})?", texto):
        limpo = bruto.split(",")[0].replace(".", "")
        if len(limpo) < 5 or not limpo.isdigit():
            continue
        if int(limpo) not in AUTORIZADOS:
            return (False, f"O valor {bruto} citado no texto não consta do dossiê "
                           f"nem decorre de cálculo sobre seus valores. Corrija.")
    return (True, saida)


def montar_equipe() -> Crew:
    comum = dict(llm=MODELO, verbose=False, allow_delegation=False,
                 max_iter=5, max_rpm=20, max_execution_time=180)

    tecnico = Agent(role="Analista Técnico",
                    goal="Avaliar a viabilidade técnica do projeto",
                    backstory=("Você é engenheiro de software com quinze anos em "
                               "sistemas públicos e já acompanhou três migrações "
                               "de protocolo."), **comum)
    financeiro = Agent(role="Analista Financeiro",
                       goal="Avaliar custos, dotação e sustentação do projeto",
                       backstory=("Você é contador especialista em execução "
                                  "orçamentária e examina o descompasso entre "
                                  "empenho e dotação."), **comum)
    parecerista = Agent(role="Parecerista",
                        goal="Consolidar as análises em nota técnica",
                        backstory=("Você é procurador do Estado, redige notas "
                                   "enxutas fundamentadas na Lei nº 14.133/2021 "
                                   "e nunca recomenda o que não pode sustentar."),
                        **comum)

    t1 = Task(description="Analise a viabilidade técnica.\n\nDOSSIÊ:\n" + DOSSIE,
              expected_output="Análise em até doze linhas, citando os números do dossiê.",
              agent=tecnico)
    t2 = Task(description="Analise custos e adequação orçamentária.\n\nDOSSIÊ:\n" + DOSSIE,
              expected_output="Análise em até doze linhas, citando os valores do dossiê.",
              agent=financeiro)
    t3 = Task(description=("Consolide as análises em nota técnica para decisão do "
                           "Secretário, com recomendação explícita. Use exclusivamente "
                           "valores presentes no dossiê ou deles calculados."),
              expected_output=("Nota técnica com síntese, valor estimado, dotação, "
                               "recomendação e pontos de atenção."),
              agent=parecerista, context=[t1, t2],
              output_pydantic=NotaTecnica, guardrail=ancoragem_numerica)

    return Crew(agents=[tecnico, financeiro, parecerista], tasks=[t1, t2, t3],
                process=Process.sequential, verbose=False)


def main() -> None:
    inicio = time.perf_counter()
    resultado = montar_equipe().kickoff()
    decorrido = time.perf_counter() - inicio

    nota = resultado.pydantic
    print("=" * 72)
    print("NOTA TÉCNICA — SEINFRA-2026-PRO-00471")
    print("=" * 72)
    if nota:
        print(f"  síntese     : {nota.sintese[:200]}")
        print(f"  valor       : R$ {nota.valor_estimado:,.2f}")
        print(f"  dotação     : R$ {nota.dotacao_disponivel:,.2f}")
        print(f"  recomendação: {nota.recomendacao[:200]}")
        print(f"  atenção     : {len(nota.pontos_de_atencao)} ponto(s)")
        for ponto in nota.pontos_de_atencao[:3]:
            print(f"      - {ponto[:110]}")
        conferido = round(nota.valor_estimado) in AUTORIZADOS
        print(f"\n  ancoragem numérica conferida: {'sim' if conferido else 'NÃO'}")
    else:
        print("  a tarefa não devolveu objeto estruturado")

    uso = resultado.token_usage
    custo = uso.prompt_tokens / 1e6 * 0.20 + uso.completion_tokens / 1e6 * 1.20
    print(f"\n  {uso.successful_requests} chamadas · "
          f"{uso.prompt_tokens + uso.completion_tokens} tokens · "
          f"{decorrido:.1f}s · US$ {custo:.5f}")

    registro = {
        "processo": "SEINFRA-2026-PRO-00471",
        "chamadas": uso.successful_requests,
        "tokens_entrada": uso.prompt_tokens,
        "tokens_saida": uso.completion_tokens,
        "custo_usd": round(custo, 5),
        "segundos": round(decorrido, 1),
        "nota": nota.model_dump() if nota else None,
    }
    destino = BASE / "nota_tecnica.json"
    destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  registro gravado em {destino.name}")


if __name__ == "__main__":
    main()
