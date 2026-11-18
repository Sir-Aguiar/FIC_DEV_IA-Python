# ============================================================
# Minilab 4 — quatro configurações, duas rodadas
# A rubrica já estava gravada antes desta execução.
# ============================================================
"""Roda chamada única e três equipes, duas vezes, e grava a tabela.

O custo em dólar cobre só a geração do parecer, no preço curto do
gpt-5.6-luna usado nos exemplos da aula. O juiz entra nas colunas de
fidelidade e utilidade e não entra no US$.
"""
import json
import os
import pathlib
import sys
import time
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parent / ".env")

sys.path.insert(0, str(BASE.parent / "exemplos"))

from equipe import DOSSIE, Parecer  # noqa: E402

MODELO = "gpt-5.6-luna"
MODELO_JUIZ = "gpt-5.6-terra"
PRECO_ENTRADA, PRECO_SAIDA = 0.20, 1.20

RUBRICA = json.loads(
    (BASE / "dados" / "rubrica.json").read_text(encoding="utf-8")
)["itens"]

PAPEIS = [
    (
        "Analista Técnico",
        "Avaliar disponibilidade, satisfação e entregas do Programa 536",
        (
            "Você é engenheiro da MTI e acompanha o painel dos 19 serviços "
            "críticos desde a implantação do monitoramento. Na carreira, "
            "aprendeu a confrontar o realizado com a meta de 99,80% e a nomear "
            "o mês que puxou a média para baixo antes de falar em arquitetura."
        ),
    ),
    (
        "Analista Financeiro",
        "Avaliar a execução orçamentária do Programa 536 no exercício de 2025",
        (
            "Você é contador da execução do PPA e já devolveu relatório em que "
            "o quadro e o texto não fechavam a mesma conta. Por isso registra "
            "as duas séries oficiais do RAG, a do quadro e a da análise, sem "
            "escolher uma delas no lugar da outra."
        ),
    ),
    (
        "Parecerista",
        "Consolidar as análises em parecer com recomendação para a diretoria",
        (
            "Você é procurador que há anos assina parecer sobre prestação de "
            "contas de empresa estatal. Só recomenda o que o RAG público "
            "sustenta, e aponta contrato ainda em tramitação e dado sigiloso "
            "que o dossiê não abre."
        ),
    ),
]

TAREFA_UNICA = (
    "Elabore um parecer técnico sobre o Programa 536 descrito no dossiê, "
    "para decisão da diretoria da MTI. Trate dos aspectos técnicos, "
    "financeiros e jurídicos e conclua com recomendação explícita."
)


class Julgamento(BaseModel):
    """Notas do juiz. A fidelidade não é decidida pela rubrica."""

    fidelidade: Literal[1, 2, 3, 4, 5] = Field(
        description="5 se toda afirmação se apoia no dossiê; 1 se há invenção relevante"
    )
    utilidade: Literal[1, 2, 3, 4, 5] = Field(
        description="5 se o gestor decidiria com base nele; 1 se é genérico"
    )
    justificativa: str = Field(description="Uma frase explicando as duas notas")


def normalizar(texto: str) -> str:
    """Deixa a busca da rubrica indiferente a maiúsculas e pontuação decimal."""
    return texto.lower().replace(".", "").replace(",", "").replace("**", "")


def aplicar_rubrica(parecer: str) -> tuple[int, list[str]]:
    """Conta quantos dos seis itens aparecem no texto."""
    texto, perdidos = normalizar(parecer), []
    for item in RUBRICA:
        if not any(normalizar(alvo) in texto for alvo in item["alvos"]):
            perdidos.append(item["id"])
    return len(RUBRICA) - len(perdidos), perdidos


def julgar(parecer: str) -> Julgamento:
    """Pede ao modelo superior fidelidade e utilidade do parecer."""
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resposta = cliente.chat.completions.parse(
        model=MODELO_JUIZ,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você avalia pareceres técnicos da administração pública estadual. "
                    "Julgue apenas o parecer apresentado, comparando-o com o dossiê. "
                    "Fidelidade mede se as afirmações se apoiam no dossiê. Utilidade "
                    "mede se um gestor conseguiria decidir a partir dele."
                ),
            },
            {"role": "user", "content": f"DOSSIÊ:\n{DOSSIE}\n\nPARECER:\n{parecer}"},
        ],
        response_format=Julgamento,
    )
    return resposta.choices[0].message.parsed


def custo(entrada: int, saida: int) -> float:
    """Converte tokens do luna no preço curto da aula, em dólar."""
    return entrada / 1e6 * PRECO_ENTRADA + saida / 1e6 * PRECO_SAIDA


def chamada_unica() -> dict:
    """Uma mensagem ao mesmo modelo, sem CrewAI."""
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    inicio = time.perf_counter()
    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é analista da Empresa Mato-grossense de Tecnologia "
                    "da Informação e redige pareceres para a diretoria."
                ),
            },
            {"role": "user", "content": f"{TAREFA_UNICA}\n\nDOSSIÊ:\n{DOSSIE}"},
        ],
    )
    uso = resposta.usage
    return fechar(
        "Chamada única",
        resposta.choices[0].message.content or "",
        1,
        uso.prompt_tokens,
        uso.completion_tokens,
        time.perf_counter() - inicio,
    )


def montar_equipe(com_backstory: bool, saida_estruturada: bool) -> Crew:
    """Monta os três agentes. A história some quando com_backstory é falso."""
    llm = LLM(model=f"openai/{MODELO}")
    agentes = []
    for papel, objetivo, historia in PAPEIS:
        agentes.append(
            Agent(
                role=papel,
                goal=objetivo,
                backstory=historia if com_backstory else f"Você atua como {papel}.",
                llm=llm,
                verbose=False,
                max_iter=5,
                max_rpm=10,
                max_execution_time=180,
                allow_delegation=False,
            )
        )

    tecnico, financeiro, parecerista = agentes

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
        **({"output_pydantic": Parecer} if saida_estruturada else {}),
    )
    return Crew(
        agents=agentes,
        tasks=[analise_tecnica, analise_financeira, consolidacao],
        process=Process.sequential,
        verbose=False,
    )


def rodar_equipe(rotulo: str, com_backstory: bool, saida_estruturada: bool) -> dict:
    """Mede uma equipe do kickoff até o token_usage."""
    inicio = time.perf_counter()
    resultado = montar_equipe(com_backstory, saida_estruturada).kickoff()
    decorrido = time.perf_counter() - inicio
    uso = resultado.token_usage
    return fechar(
        rotulo,
        str(resultado),
        uso.successful_requests,
        uso.prompt_tokens,
        uso.completion_tokens,
        decorrido,
    )


def fechar(rotulo, texto, chamadas, entrada, saida, tempo) -> dict:
    """Aplica a rubrica e o juiz sobre o texto já produzido."""
    nota, perdidos = aplicar_rubrica(texto)
    juiz = julgar(texto[:6000])
    return {
        "rotulo": rotulo,
        "rubrica": nota,
        "perdidos": perdidos,
        "fidelidade": juiz.fidelidade,
        "utilidade": juiz.utilidade,
        "justificativa": juiz.justificativa,
        "chamadas": chamadas,
        "tokens": entrada + saida,
        "tempo": tempo,
        "custo": custo(entrada, saida),
    }


def uma_rodada() -> list[dict]:
    """Executa as quatro configurações na ordem pedida."""
    return [
        chamada_unica(),
        rodar_equipe("Equipe sem backstory", False, False),
        rodar_equipe("Equipe com backstory", True, False),
        rodar_equipe("Backstory e saída estruturada", True, True),
    ]


def linha(r: dict) -> str:
    """Formata uma configuração para a tabela markdown."""
    return (
        f"| {r['rotulo']} | {r['rubrica']}/6 | {r['fidelidade']} | {r['utilidade']} | "
        f"{r['chamadas']} | {r['tokens']} | {r['tempo']:.1f}s | {r['custo']:.5f} |"
    )


def gravar(rodadas: list[list[dict]]) -> None:
    """Escreve as duas tabelas e a variação das notas do juiz."""
    cabecalho = (
        "| Configuração | Rubrica | Fidelidade | Utilidade | Chamadas | Tokens | Tempo | US$ |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    )
    partes = [
        "# Resultados do experimento",
        "",
        "Preço de geração: US$ 0,20 por milhão de tokens de entrada e US$ 1,20 "
        "por milhão de tokens de saída do gpt-5.6-luna. O juiz é o gpt-5.6-terra "
        "e não entra na coluna US$.",
        "",
        "## Rodada 1",
        "",
        cabecalho,
    ]
    for item in rodadas[0]:
        partes.append(linha(item))
    partes.extend(["", "## Rodada 2", "", cabecalho])
    for item in rodadas[1]:
        partes.append(linha(item))

    partes.extend(
        [
            "",
            "## Variação do juiz entre as rodadas",
            "",
            "Diferença da rodada 2 em relação à rodada 1. Zero significa a mesma nota.",
            "",
            "| Configuração | Fidelidade | Utilidade |",
            "| --- | ---: | ---: |",
        ]
    )
    for antes, depois in zip(rodadas[0], rodadas[1]):
        partes.append(
            f"| {antes['rotulo']} | {depois['fidelidade'] - antes['fidelidade']:+d} | "
            f"{depois['utilidade'] - antes['utilidade']:+d} |"
        )
    partes.append("")
    destino = BASE.parent / "resultados.md"
    destino.write_text("\n".join(partes), encoding="utf-8")
    (BASE / "dados" / "rodadas.json").write_text(
        json.dumps(rodadas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"tabela em {destino}")


def main() -> None:
    rodadas = []
    for indice in (1, 2):
        print(f"=== rodada {indice} ===", flush=True)
        rodadas.append(uma_rodada())
        for item in rodadas[-1]:
            print(
                f"{item['rotulo']}: rubrica {item['rubrica']}/6 "
                f"fid {item['fidelidade']} util {item['utilidade']} "
                f"{item['chamadas']} chamadas {item['tokens']} tokens "
                f"{item['tempo']:.1f}s US$ {item['custo']:.5f}",
                flush=True,
            )
    gravar(rodadas)


if __name__ == "__main__":
    main()
