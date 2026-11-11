# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: Quanto custa cada consulta, e por quê
# Seção 5 – Experimento: quanto custa cada consulta, e por quê
# Requisitos: pip install langchain langchain-openai langchain-groq python-dotenv
# ============================================================
"""Executa as doze consultas com gabarito em quatro configurações de agente.

A comparação isola uma variável por vez: o mesmo conjunto de perguntas, as
mesmas três ferramentas e a mesma instrução, mudando apenas o modelo e a
presença de um limite de passos. O que se quer medir não é só o acerto, mas
a distribuição do custo entre as consultas, porque é ela que decide o
orçamento de um serviço em produção.
"""
import json
import pathlib
import re
import statistics
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_openai import ChatOpenAI

from ferramentas import FERRAMENTAS
from medidor import Registro, instrumentar

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

INSTRUCAO = (
    "Você assessora procuradores do Estado de Mato Grosso. Use as ferramentas "
    "disponíveis para fundamentar suas respostas e cite a norma aplicável. "
    "Se a pergunta não trouxer os dados necessários para um cálculo, peça os "
    "dados que faltam em vez de supor valores."
)

# Preço por milhão de tokens na faixa de contexto curto, confirmado na página
# oficial de preços da OpenAI em setembro de 2026.
PRECOS = {
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5-nano": (0.05, 0.40),
}


def configuracoes() -> list[tuple[str, callable]]:
    """As quatro configurações comparadas, cada uma com seu construtor."""
    return [
        ("A · luna, sem limite",
         lambda: (ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none"),
                  [], "gpt-5.6-luna")),
        ("B · luna, limite de 6 passos",
         lambda: (ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none"),
                  [ModelCallLimitMiddleware(thread_limit=6, exit_behavior="end")],
                  "gpt-5.6-luna")),
        ("C · terra, sem limite",
         lambda: (ChatOpenAI(model="gpt-5.6-terra", reasoning_effort="none"),
                  [], "gpt-5.6-terra")),
        # A geração GPT-5 não aceita `reasoning_effort="none"`, ao contrário da
        # 5.6: é preciso omitir o parâmetro para que as ferramentas funcionem.
        ("D · gpt-5-nano, sem limite",
         lambda: (ChatOpenAI(model="gpt-5-nano"), [], "gpt-5-nano")),
    ]


EXTENSO = {"dez": "10", "quinze": "15", "vinte": "20", "trinta": "30",
           "cinco": "5", "sessenta": "60", "noventa": "90"}


def normalizar(texto: str) -> str:
    """Aproxima grafias equivalentes antes de comparar com o gabarito.

    Uma comparação literal reprovaria cinco respostas corretas deste
    conjunto: o agente escreve "10 dias" onde o gabarito diz "dez dias", e
    "09/04/2026" onde o gabarito diz "2026-04-09". O critério de avaliação é
    parte do experimento, e um critério rígido demais mede a si próprio.
    """
    t = texto.lower().replace(".", "").replace(",", "").replace("**", "")
    for palavra, algarismo in EXTENSO.items():
        t = t.replace(palavra, algarismo)
    # dd/mm/aaaa passa a aaaa-mm-dd, para que as duas grafias se encontrem
    return re.sub(r"\b(\d{2})/(\d{2})/(\d{4})\b", r"\3-\2-\1", t)


def avaliar(resposta: str, consulta: dict) -> bool:
    """A resposta conta como correta se contiver o trecho definido no gabarito."""
    texto = normalizar(resposta)
    return all(normalizar(alvo) in texto for alvo in consulta["deve_conter"])


def executar(rotulo: str, construir, consultas: list[dict]) -> dict:
    modelo, extras, nome_preco = construir()
    registro = Registro()
    usd_entrada, usd_saida = PRECOS[nome_preco]

    acertos = ferramenta_certa = erros = 0
    custos, passos, tempos = [], [], []

    for consulta in consultas:
        registro.zerar()
        agente = create_agent(model=modelo, tools=FERRAMENTAS,
                              system_prompt=INSTRUCAO,
                              middleware=[*instrumentar(registro), *extras])
        inicio = time.perf_counter()
        try:
            saida = agente.invoke({"messages": [{"role": "user",
                                                 "content": consulta["pergunta"]}]})
            final = saida["messages"][-1].content
            if isinstance(final, list):  # Responses API devolve blocos
                final = " ".join(b.get("text", "") for b in final if isinstance(b, dict))
        except Exception as erro:
            print(f"    {consulta['id']}: {type(erro).__name__} — {str(erro)[:70]}")
            erros += 1
            final = ""
        tempos.append(time.perf_counter() - inicio)

        if avaliar(str(final), consulta):
            acertos += 1
        # A ferramenta certa é a esperada; para as consultas sem ferramenta,
        # acertar significa não ter chamado nenhuma.
        esperadas = set(consulta["ferramentas_esperadas"])
        usadas = set(registro.ferramentas)
        if (esperadas and esperadas <= usadas) or (not esperadas and not usadas):
            ferramenta_certa += 1
        passos.append(registro.chamadas_modelo)
        custos.append(registro.custo(usd_entrada, usd_saida))

    return {
        "rotulo": rotulo, "acertos": acertos, "ferramenta_certa": ferramenta_certa,
        "erros": erros, "passos_mediana": statistics.median(passos),
        "passos_max": max(passos), "tempo_mediano": statistics.median(tempos),
        "custo_total": sum(custos), "custos": custos,
        "ids": [c["id"] for c in consultas],
    }


def main() -> None:
    caminho = pathlib.Path(__file__).parent / "consultas_pge.json"
    consultas = json.loads(caminho.read_text(encoding="utf-8"))["consultas"]
    print(f"{len(consultas)} consultas com gabarito\n")

    resultados = []
    for rotulo, construir in configuracoes():
        print(f"[{rotulo}] executando...")
        resultados.append(executar(rotulo, construir, consultas))

    print(f"\n{'Configuração':28} {'Acerto':>7} {'Ferr.':>7} {'Passos':>12} "
          f"{'Tempo':>8} {'US$ nas 12':>11}")
    print("-" * 80)
    for r in resultados:
        print(f"{r['rotulo']:28} {r['acertos']:>3}/12  {r['ferramenta_certa']:>3}/12  "
              f"{r['passos_mediana']:>4.0f} / {r['passos_max']:<4.0f} "
              f"{r['tempo_mediano']:>7.2f}s {r['custo_total']:>11.5f}")

    # A segunda tabela é a que ensina: a distribuição do custo entre consultas.
    print(f"\n{'Configuração':28} {'+ barata':>10} {'mediana':>10} {'+ cara':>10} "
          f"{'razão':>8}  consulta mais cara")
    print("-" * 88)
    for r in resultados:
        custos = r["custos"]
        mediana = statistics.median(custos) or 1e-9
        pior = max(custos)
        print(f"{r['rotulo']:28} {min(custos):>10.6f} {mediana:>10.6f} {pior:>10.6f} "
              f"{pior / mediana:>7.1f}x  {r['ids'][custos.index(pior)]}")

    destino = pathlib.Path(__file__).parent / "resultado_experimento.json"
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados em {destino.name}")


if __name__ == "__main__":
    main()
