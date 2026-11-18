# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: Quanto custa cada consulta, e por quê
# Adaptado ao encaixe de lote de processamento fiscal da GTI
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""Executa as doze consultas com gabarito em seis configurações da OpenAI.

O conjunto, as ferramentas e a instrução ficam fixos. Muda o modelo. Além dos
três níveis da aula, entram GPT-6 Luna, GPT-6.1 Sol e GPT-6 Astra.
"""
import json
import pathlib
import statistics
import sys
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI


RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from criterio import avaliar  # noqa: E402
from ferramentas import FERRAMENTAS  # noqa: E402
from medidor import Registro, instrumentar  # noqa: E402


load_dotenv(RAIZ / ".env")

INSTRUCAO = (
    "Você assessora a Gerência de Tecnologia da Informação da Secretaria de "
    "Estado de Fazenda no encaixe de lotes de processamento. Use as ferramentas "
    "para consultar a rotina e calcular se o lote cabe na janela. Se a pergunta "
    "não trouxer a rotina, o volume ou as horas, peça os dados que faltam em "
    "vez de supor valores. Não grave consumo na janela."
)

# Preço por milhão de tokens na faixa de contexto curto.
# Os três primeiros são os da Seção 5. Os três últimos são o preço padrão
# publicado pela OpenAI para GPT-6 Luna, GPT-6.1 Sol e GPT-6 Astra.
PRECOS = {
    "gpt-5-nano": (0.05, 0.40),
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-sol": (2.00, 10.00),
    "gpt-6-astra": (10.00, 50.00),
}

ROTINA = RAIZ / "src" / "dados" / "rotinas.json"
SAIDA = RAIZ / "resultados" / "experimento.md"


def configuracoes() -> list[tuple[str, callable]]:
    """Seis níveis da OpenAI, sem limite de passos.

    Na família 5.6 e no GPT-6 Luna, ferramentas com raciocínio ativo são
    recusadas no Chat Completions, então o esforço fica em none. Astra e Sol
    não aceitam none: o esforço mínimo é low, e a chamada de ferramenta vai
    pela Responses API.
    """
    return [
        ("gpt-5-nano, sem limite",
         lambda: (ChatOpenAI(model="gpt-5-nano"), [], "gpt-5-nano")),
        ("gpt-5.6-luna, sem limite",
         lambda: (ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none"),
                  [], "gpt-5.6-luna")),
        ("gpt-5.6-terra, sem limite",
         lambda: (ChatOpenAI(model="gpt-5.6-terra", reasoning_effort="none"),
                  [], "gpt-5.6-terra")),
        ("gpt-6-luna, sem limite",
         lambda: (ChatOpenAI(model="gpt-6-luna", reasoning_effort="none",
                             use_responses_api=True),
                  [], "gpt-6-luna")),
        ("gpt-6.1-sol, raciocínio baixo",
         lambda: (ChatOpenAI(model="gpt-6.1-sol", reasoning_effort="low",
                             use_responses_api=True),
                  [], "gpt-6.1-sol")),
        ("gpt-6-astra, raciocínio baixo",
         lambda: (ChatOpenAI(model="gpt-6-astra", reasoning_effort="low",
                             use_responses_api=True),
                  [], "gpt-6-astra")),
    ]


def executar(rotulo: str, construir, consultas: list[dict]) -> dict:
    """Roda as doze consultas e devolve acerto, ferramenta, passos, tempo e custo."""
    modelo, extras, nome_preco = construir()
    registro = Registro()
    usd_entrada, usd_saida = PRECOS[nome_preco]

    acertos = ferramenta_certa = erros = 0
    custos, passos, tempos = [], [], []

    for consulta in consultas:
        registro.zerar()
        agente = create_agent(
            model=modelo,
            tools=FERRAMENTAS,
            system_prompt=INSTRUCAO,
            middleware=[*instrumentar(registro), *extras],
        )
        inicio = time.perf_counter()
        try:
            saida = agente.invoke({"messages": [{"role": "user", "content": consulta["pergunta"]}]})
            final = saida["messages"][-1].content
            if isinstance(final, list):
                final = " ".join(bloco.get("text", "") for bloco in final if isinstance(bloco, dict))
        except Exception as erro:
            print(f"    {consulta['id']}: {type(erro).__name__} — {str(erro)[:70]}")
            erros += 1
            final = ""
        tempos.append(time.perf_counter() - inicio)

        if avaliar(str(final), consulta):
            acertos += 1

        # A ferramenta certa é a esperada. Sem ferramenta esperada, acertar
        # é não ter chamado nenhuma.
        esperadas = set(consulta["ferramentas_esperadas"])
        usadas = set(registro.ferramentas)
        if (esperadas and esperadas <= usadas) or (not esperadas and not usadas):
            ferramenta_certa += 1
        passos.append(registro.chamadas_modelo)
        custos.append(registro.custo(usd_entrada, usd_saida))
        print(f"    {consulta['id']} acerto={acertos} ferramenta={ferramenta_certa}")

    return {
        "rotulo": rotulo,
        "acertos": acertos,
        "ferramenta_certa": ferramenta_certa,
        "erros": erros,
        "passos_mediana": statistics.median(passos),
        "passos_max": max(passos),
        "tempo_mediano": statistics.median(tempos),
        "custo_total": sum(custos),
        "custos": custos,
        "ids": [consulta["id"] for consulta in consultas],
    }


def distribuicao(item: dict) -> dict:
    """Separa a consulta mais barata, a mediana e a mais cara.

    A razão é a mais cara dividida pela mediana. Mediana zero não serve de
    divisor: nesse caso a conta usa um piso mínimo para a razão continuar definida.
    """
    custos = item["custos"]
    mediana = statistics.median(custos)
    mais_cara = max(custos)
    indice = custos.index(mais_cara)
    return {
        "mais_barata": min(custos),
        "mediana": mediana,
        "mais_cara": mais_cara,
        "razao": mais_cara / (mediana or 1e-9),
        "consulta": item["ids"][indice],
    }


def _dolar(valor: float) -> str:
    """Escreve o dólar com seis casas, vírgula decimal."""
    return f"{valor:.6f}".replace(".", ",")


def gravar(resultados: list[dict]) -> None:
    """Escreve as duas tabelas do experimento em resultados/experimento.md."""
    linhas = [
        "| Configuração | Acerto | Ferramenta certa | Passos (med./máx) | Tempo | US$ nas 12 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in resultados:
        tempo = f"{item['tempo_mediano']:.2f}".replace(".", ",") + " s"
        custo = f"{item['custo_total']:.5f}".replace(".", ",")
        passos = f"{item['passos_mediana']:.0f} / {item['passos_max']:.0f}"
        linhas.append(
            f"| {item['rotulo']} | {item['acertos']}/12 | "
            f"{item['ferramenta_certa']}/12 | {passos} | {tempo} | {custo} |"
        )
    linhas.append("")
    linhas.append(
        "| Configuração | Mais barata | Mediana | Mais cara | Razão | Consulta mais cara |"
    )
    linhas.append("| --- | ---: | ---: | ---: | ---: | --- |")
    for item in resultados:
        faixa = distribuicao(item)
        razao = f"{faixa['razao']:.1f}".replace(".", ",") + "x"
        linhas.append(
            f"| {item['rotulo']} | {_dolar(faixa['mais_barata'])} | "
            f"{_dolar(faixa['mediana'])} | {_dolar(faixa['mais_cara'])} | "
            f"{razao} | {faixa['consulta']} |"
        )
    linhas.append("")
    linhas.append(
        "Tempo é a mediana das doze consultas. A razão é a consulta mais cara "
        "dividida pela mediana de custo. O dólar é por milhão de tokens, na "
        "faixa curta: gpt-5-nano 0,05 e 0,40; gpt-5.6-luna 0,20 e 1,20; "
        "gpt-5.6-terra 2,00 e 12,00; gpt-6-luna 0,10 e 0,50; "
        "gpt-6.1-sol 2,00 e 10,00; gpt-6-astra 10,00 e 50,00."
    )
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    caminho = RAIZ / "src" / "dados" / "consultas.json"
    consultas = json.loads(caminho.read_text(encoding="utf-8"))["consultas"]
    print(f"{len(consultas)} consultas com gabarito\n")

    # Uma chamada a atualizar_consumo_janela reescreve a base. O experimento
    # devolve o arquivo ao estado anterior, seja qual for o modelo.
    backup = ROTINA.read_text(encoding="utf-8")
    resultados = []
    try:
        for rotulo, construir in configuracoes():
            print(f"[{rotulo}] executando...")
            resultados.append(executar(rotulo, construir, consultas))
    finally:
        ROTINA.write_text(backup, encoding="utf-8")

    print(f"\n{'Configuração':32} {'Acerto':>7} {'Ferr.':>7} {'Passos':>12} "
          f"{'Tempo':>8} {'US$ nas 12':>11}")
    print("-" * 84)
    for item in resultados:
        print(f"{item['rotulo']:32} {item['acertos']:>3}/12  {item['ferramenta_certa']:>3}/12  "
              f"{item['passos_mediana']:>4.0f} / {item['passos_max']:<4.0f} "
              f"{item['tempo_mediano']:>7.2f}s {item['custo_total']:>11.5f}")

    print(f"\n{'Configuração':32} {'+ barata':>10} {'mediana':>10} {'+ cara':>10} "
          f"{'razão':>8}  consulta")
    print("-" * 84)
    for item in resultados:
        faixa = distribuicao(item)
        print(f"{item['rotulo']:32} {faixa['mais_barata']:>10.6f} {faixa['mediana']:>10.6f} "
              f"{faixa['mais_cara']:>10.6f} {faixa['razao']:>7.1f}x  {faixa['consulta']}")

    gravar(resultados)
    print(f"\nTabela em {SAIDA}")


if __name__ == "__main__":
    main()
