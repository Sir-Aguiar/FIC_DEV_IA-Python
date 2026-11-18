# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: A backstory paga o que promete? Cinco configurações medidas
# Seção 5 – Efeito da configuração dos agentes no resultado
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Produz o mesmo parecer por cinco caminhos e mede o que cada um entrega.

A promessa central do CrewAI está na definição do agente: papel, objetivo e
história pessoal. O experimento coloca essa promessa à prova comparando a
equipe completa com uma chamada única ao mesmo modelo, que é a alternativa
que o material de mercado nunca mostra. Entre os dois extremos ficam as
variações que isolam o efeito de cada campo da definição.
"""
import json
import pathlib
import time
import warnings

warnings.filterwarnings("ignore")

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from avaliacao import aplicar_rubrica, julgar

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

DOSSIE = (BASE / "dossie_projeto.md").read_text(encoding="utf-8")

# Preço por milhão de tokens na faixa curta, página oficial da OpenAI, set/2026.
PRECOS = {"gpt-5.6-luna": (0.20, 1.20), "gpt-5.6-terra": (2.00, 12.00)}

TAREFA = ("Elabore um parecer técnico sobre a viabilidade do projeto descrito no "
          "dossiê, para decisão do Secretário. O parecer deve tratar dos aspectos "
          "técnicos, financeiros e jurídicos, e concluir com recomendação explícita.")


class Parecer(BaseModel):
    """Estrutura do parecer, usada apenas pela configuração 4."""

    sintese: str = Field(description="Resumo do caso em até três frases")
    aspectos_tecnicos: str
    aspectos_financeiros: str
    aspectos_juridicos: str
    recomendacao: str = Field(description="Recomendação explícita e fundamentada")
    pontos_de_atencao: list[str] = Field(description="Riscos que exigem decisão superior")


def llm(modelo: str) -> LLM:
    return LLM(model=f"openai/{modelo}")


# ---------------------------------------------------------------
# Configuração 1 — chamada única, sem CrewAI
# ---------------------------------------------------------------
def config_1_chamada_unica() -> dict:
    """A linha de base: um único pedido ao mesmo modelo, sem orquestração."""
    cliente = OpenAI()
    inicio = time.perf_counter()
    resposta = cliente.chat.completions.create(
        model="gpt-5.6-luna",
        messages=[
            {"role": "system", "content":
             "Você é analista da Secretaria de Infraestrutura de Mato Grosso e "
             "redige pareceres técnicos para decisão superior."},
            {"role": "user", "content": f"{TAREFA}\n\nDOSSIÊ:\n{DOSSIE}"},
        ],
    )
    uso = resposta.usage
    return montar("1 · chamada única", resposta.choices[0].message.content,
                  1, uso.prompt_tokens, uso.completion_tokens,
                  time.perf_counter() - inicio, "gpt-5.6-luna")


# ---------------------------------------------------------------
# Configurações 2 a 5 — equipes de três agentes
# ---------------------------------------------------------------
PAPEIS = [
    ("Analista Técnico", "Avaliar a viabilidade técnica do projeto",
     "Você é engenheiro de software com quinze anos de experiência em sistemas "
     "públicos. Já acompanhou três migrações de sistemas de protocolo e conhece "
     "de perto o que costuma dar errado na migração de acervos históricos."),
    ("Analista Financeiro", "Avaliar custos, dotação e retorno do projeto",
     "Você é contador da Secretaria de Fazenda, especialista em execução "
     "orçamentária. Sua preocupação constante é o descompasso entre o valor "
     "empenhado e a dotação disponível no exercício."),
    ("Parecerista", "Consolidar as análises em parecer com recomendação",
     "Você é procurador do Estado com experiência em contratações de tecnologia. "
     "Redige pareceres enxutos, sempre fundamentados na Lei nº 14.133/2021, e "
     "nunca recomenda o que não pode sustentar."),
]


def montar_equipe(com_backstory: bool, saida_estruturada: bool,
                  modelos: tuple[str, str]) -> Crew:
    """Monta a equipe de três agentes conforme a configuração em teste."""
    modelo_analista, modelo_parecerista = modelos
    agentes, tarefas = [], []
    for indice, (papel, objetivo, historia) in enumerate(PAPEIS):
        modelo = modelo_parecerista if indice == 2 else modelo_analista
        agentes.append(Agent(
            role=papel, goal=objetivo,
            backstory=historia if com_backstory else f"Você atua como {papel}.",
            llm=llm(modelo), verbose=False, max_iter=5, allow_delegation=False,
        ))

    for indice, agente in enumerate(agentes):
        if indice < 2:
            esperado = ("Análise em até quinze linhas, citando os números do dossiê."
                        if saida_estruturada else "Sua análise.")
            tarefas.append(Task(
                description=f"{TAREFA}\n\nDOSSIÊ:\n{DOSSIE}\n\nTrate apenas do que "
                            f"compete ao seu papel de {PAPEIS[indice][0]}.",
                expected_output=esperado, agent=agente))
        else:
            esperado = ("Parecer com síntese, os três aspectos, recomendação "
                        "explícita e pontos de atenção, citando os valores do dossiê."
                        if saida_estruturada else "O parecer final.")
            tarefas.append(Task(
                description="Consolide as análises anteriores em parecer único "
                            "para decisão do Secretário, com recomendação explícita.",
                expected_output=esperado, agent=agente, context=tarefas[:2],
                **({"output_pydantic": Parecer} if saida_estruturada else {})))

    return Crew(agents=agentes, tasks=tarefas, process=Process.sequential, verbose=False)


def rodar_equipe(rotulo: str, com_backstory: bool, saida_estruturada: bool,
                 modelos: tuple[str, str]) -> dict:
    equipe = montar_equipe(com_backstory, saida_estruturada, modelos)
    inicio = time.perf_counter()
    resultado = equipe.kickoff()
    decorrido = time.perf_counter() - inicio
    uso = resultado.token_usage
    texto = str(resultado)
    return montar(rotulo, texto, uso.successful_requests, uso.prompt_tokens,
                  uso.completion_tokens, decorrido, modelos[0], modelos[1])


def montar(rotulo, texto, chamadas, entrada, saida, tempo, modelo, modelo2=None) -> dict:
    e1, s1 = PRECOS[modelo]
    if modelo2 and modelo2 != modelo:
        # Aproximação: dois terços do consumo nos analistas, um terço no parecerista.
        e2, s2 = PRECOS[modelo2]
        custo = ((entrada * 2 / 3) / 1e6 * e1 + (saida * 2 / 3) / 1e6 * s1
                 + (entrada / 3) / 1e6 * e2 + (saida / 3) / 1e6 * s2)
    else:
        custo = entrada / 1e6 * e1 + saida / 1e6 * s1
    nota, perdidos = aplicar_rubrica(texto)
    return {"rotulo": rotulo, "texto": texto, "rubrica": nota, "perdidos": perdidos,
            "chamadas": chamadas, "entrada": entrada, "saida": saida,
            "tempo": tempo, "custo": custo}


def main() -> None:
    configuracoes = [
        ("1 · chamada única", config_1_chamada_unica),
        ("2 · crew sem backstory", lambda: rodar_equipe(
            "2 · crew sem backstory", False, False, ("gpt-5.6-luna", "gpt-5.6-luna"))),
        ("3 · crew com backstory", lambda: rodar_equipe(
            "3 · crew com backstory", True, False, ("gpt-5.6-luna", "gpt-5.6-luna"))),
        ("4 · backstory + saída estruturada", lambda: rodar_equipe(
            "4 · backstory + saída estruturada", True, True, ("gpt-5.6-luna", "gpt-5.6-luna"))),
        ("5 · modelos mistos", lambda: rodar_equipe(
            "5 · modelos mistos", True, True, ("gpt-5.6-luna", "gpt-5.6-terra"))),
    ]

    resultados = []
    for rotulo, funcao in configuracoes:
        print(f"[{rotulo}] executando...")
        try:
            resultado = funcao()
            resultado["juiz"] = julgar(resultado["texto"][:6000], DOSSIE)
            resultados.append(resultado)
        except Exception as erro:
            print(f"    falhou: {type(erro).__name__} — {str(erro)[:110]}")

    print(f"\n{'Configuração':36} {'Rubrica':>8} {'Fid.':>5} {'Util.':>6} "
          f"{'Chamadas':>9} {'Tokens':>9} {'Tempo':>8} {'US$':>9}")
    print("-" * 100)
    for r in resultados:
        j = r["juiz"]
        print(f"{r['rotulo']:36} {r['rubrica']:>5}/6  {j.fidelidade:>5} {j.utilidade:>6} "
              f"{r['chamadas']:>9} {r['entrada'] + r['saida']:>9} "
              f"{r['tempo']:>7.1f}s {r['custo']:>9.5f}")

    print("\nItens da rubrica perdidos por configuração:")
    for r in resultados:
        print(f"  {r['rotulo']:36} {r['perdidos'] or 'nenhum'}")

    destino = BASE / "resultado_experimento.json"
    destino.write_text(json.dumps(
        [{k: (v if k != "juiz" else v.model_dump()) for k, v in r.items()}
         for r in resultados], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados em {destino.name}")


if __name__ == "__main__":
    main()
