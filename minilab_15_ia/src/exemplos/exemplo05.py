# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 05: A incerteza do classificador
# Seção 4 – Concordância, casos limítrofes e acurácia medida
# Requisitos: pip install openai pandas python-dotenv
# ============================================================
#
# Três medidas independentes da qualidade dos rótulos:
#   A. acurácia contra o conjunto rotulado à mão (sem chamada de API);
#   B. estabilidade do mesmo modelo entre execuções repetidas;
#   C. concordância com um segundo modelo, de pesos abertos, servido pela Groq.
#
# Uso:
#   python exemplo05.py        # 3 execuções repetidas
#   python exemplo05.py 5      # 5 execuções repetidas

import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from dotenv import load_dotenv
from openai import BadRequestError, OpenAI, RateLimitError

from exemplo02 import Classificacao, INSTRUCAO

load_dotenv()

BASE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(BASE, "manifestacoes_sinteticas.csv")
GABARITO = os.path.join(BASE, "gabarito_manual.csv")
ROTULOS = os.path.join(BASE, "rotulos.csv")

MODELO_OPENAI = "gpt-5.6-luna"
MODELO_ABERTO = "openai/gpt-oss-20b"        # servido pela Groq
ESFORCO = "low"                             # o mesmo do exemplo02.py
EXECUCOES = int(sys.argv[1]) if len(sys.argv) > 1 else 3

# O nível gratuito da Groq permite 8 mil tokens por minuto, e cada chamada
# consome cerca de 1,2 mil. A Parte C roda, por isso, em fila única, com pausa
# entre chamadas e sobre um recorte do corpus concentrado nos casos difíceis.
PARALELAS_OPENAI = 6
PAUSA_GROQ = 10.0                           # segundos entre chamadas
RECORTE_SEGUNDA_OPINIAO = 20                # manifestações comparadas na Parte C

openai_client = OpenAI()
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)


def classificar_com(cliente: OpenAI, modelo: str, texto: str, tentativas: int = 6) -> str:
    """Devolve apenas o sentimento, que é o rótulo em análise aqui.

    O mesmo `reasoning_effort` do exemplo02.py é usado nas duas pontas, para
    que a comparação meça o classificador e não uma diferença de configuração.
    Modelos de raciocínio gastam parte do orçamento de tokens antes de escrever
    o JSON, conforme a Aula 02, Seção 9; com folga insuficiente a resposta volta
    vazia e o provedor devolve erro de validação. Daí o limite folgado e a
    repetição diante de erro transitório.
    """
    for tentativa in range(tentativas):
        try:
            resposta = cliente.chat.completions.parse(
                model=modelo,
                messages=[
                    {"role": "system", "content": INSTRUCAO},
                    {"role": "user", "content": f"MANIFESTAÇÃO:\n{texto}"},
                ],
                response_format=Classificacao,
                reasoning_effort=ESFORCO,
                max_completion_tokens=8000,
            )
            return resposta.choices[0].message.parsed.sentimento
        except (RateLimitError, BadRequestError):
            if tentativa == tentativas - 1:
                raise
            time.sleep(15 * (tentativa + 1))    # espera crescente: 15, 30, 45...
    raise RuntimeError("limite de tentativas esgotado")


def rodar_paralelo(cliente: OpenAI, modelo: str, textos: list[str]) -> list[str]:
    with ThreadPoolExecutor(max_workers=PARALELAS_OPENAI) as pool:
        return list(pool.map(lambda t: classificar_com(cliente, modelo, t), textos))


def rodar_em_fila(cliente: OpenAI, modelo: str, textos: list[str],
                  pausa: float) -> list[str]:
    """Fila única com pausa: respeita o limite de tokens por minuto do provedor."""
    saida = []
    for n, texto in enumerate(textos, 1):
        saida.append(classificar_com(cliente, modelo, texto))
        print(f"  [{n:>3}/{len(textos)}] {saida[-1]}")
        if n < len(textos):
            time.sleep(pausa)
    return saida


def parte_a(rot: pd.DataFrame, gab: pd.DataFrame) -> None:
    print("=" * 68)
    print("A. Acurácia contra o conjunto rotulado à mão")
    print("=" * 68)

    junto = rot.merge(gab, on="id", suffixes=("_modelo", "_humano"))
    n = len(junto)
    acertos = (junto["sentimento_modelo"] == junto["sentimento_humano"]).sum()
    print(f"Acurácia geral no sentimento: {acertos}/{n} = {100 * acertos / n:.1f}%")

    for rotulo, nome in ((0, "casos claros"), (1, "casos ambíguos")):
        recorte = junto[junto["ambiguo"] == rotulo]
        if len(recorte):
            certos = (recorte["sentimento_modelo"] == recorte["sentimento_humano"]).sum()
            print(f"  {nome:<16} {certos}/{len(recorte)} = "
                  f"{100 * certos / len(recorte):.1f}%")

    # O modelo marcou como limítrofe os mesmos casos que o revisor humano marcou?
    marcados = set(rot.loc[rot["ambiguidade"] == "limitrofe", "id"])
    humanos = set(gab.loc[gab["ambiguo"] == 1, "id"])
    print(f"\nCasos marcados como limítrofes pelo modelo: {len(marcados)}")
    print(f"Casos marcados como ambíguos pelo revisor:   {len(humanos)}")
    print(f"  em comum: {sorted(marcados & humanos)}")
    print(f"  só o revisor viu: {sorted(humanos - marcados)}")
    print(f"  só o modelo viu:  {sorted(marcados - humanos)}")


def parte_b(df: pd.DataFrame, gab: pd.DataFrame) -> None:
    print("\n" + "=" * 68)
    print(f"B. Estabilidade: {EXECUCOES} execuções do mesmo modelo, mesmo prompt")
    print("=" * 68)

    textos = df["texto"].tolist()
    execucoes = [rodar_paralelo(openai_client, MODELO_OPENAI, textos)
                 for _ in range(EXECUCOES)]

    instaveis = []
    for i, ident in enumerate(df["id"]):
        rotulos = [e[i] for e in execucoes]
        if len(set(rotulos)) > 1:
            instaveis.append((ident, rotulos))

    n = len(df)
    print(f"Manifestações com rótulo idêntico em todas as execuções: "
          f"{n - len(instaveis)}/{n} = {100 * (n - len(instaveis)) / n:.1f}%")

    if instaveis:
        ambiguos = set(gab.loc[gab["ambiguo"] == 1, "id"])
        print("Manifestações que oscilaram:")
        for ident, rotulos in instaveis:
            marca = " (ambígua no gabarito)" if ident in ambiguos else ""
            print(f"  {ident}: {' / '.join(rotulos)}{marca}")

    print("\nEfeito no indicador final:")
    for k, execucao in enumerate(execucoes, 1):
        negativas = sum(1 for r in execucao if r == "negativo")
        print(f"  execução {k}: {negativas}/{n} negativas = {100 * negativas / n:.1f}%")


def recorte_dificil(df: pd.DataFrame, gab: pd.DataFrame) -> pd.DataFrame:
    """Todos os casos ambíguos mais casos claros, até completar o recorte.

    Comparar modelos onde a resposta é óbvia informa pouco. O recorte
    privilegia deliberadamente as manifestações em que o rótulo é disputável.
    """
    ambiguos = set(gab.loc[gab["ambiguo"] == 1, "id"])
    dificeis = df[df["id"].isin(ambiguos)]
    faceis = df[~df["id"].isin(ambiguos)].head(
        max(0, RECORTE_SEGUNDA_OPINIAO - len(dificeis))
    )
    return pd.concat([dificeis, faceis]).sort_values("id").reset_index(drop=True)


def parte_c(df: pd.DataFrame, rot: pd.DataFrame, gab: pd.DataFrame) -> None:
    print("\n" + "=" * 68)
    print(f"C. Segunda opinião: {MODELO_ABERTO} (Groq)")
    print("=" * 68)

    recorte = recorte_dificil(df, gab)
    print(f"Recorte de {len(recorte)} manifestações, com todos os casos ambíguos.")
    print(f"Fila única, com pausa de {PAUSA_GROQ:.0f} s entre chamadas:")

    abertos = rodar_em_fila(groq_client, MODELO_ABERTO,
                            recorte["texto"].tolist(), PAUSA_GROQ)

    comparacao = pd.DataFrame({
        "id": recorte["id"],
        "proprietario": rot.set_index("id").loc[recorte["id"], "sentimento"].values,
        "aberto": abertos,
    }).merge(gab[["id", "sentimento", "ambiguo"]], on="id")

    concordam = (comparacao["proprietario"] == comparacao["aberto"]).sum()
    n = len(comparacao)
    print(f"\nConcordância entre os dois modelos: {concordam}/{n} = "
          f"{100 * concordam / n:.1f}%")

    certos = (comparacao["aberto"] == comparacao["sentimento"]).sum()
    print(f"Acurácia do modelo aberto contra o gabarito: {certos}/{n} = "
          f"{100 * certos / n:.1f}%")

    divergentes = comparacao[comparacao["proprietario"] != comparacao["aberto"]]
    if len(divergentes):
        print("\nOnde discordam:")
        for r in divergentes.itertuples():
            marca = " [ambígua]" if r.ambiguo else ""
            print(f"  {r.id}: proprietário={r.proprietario:<9} aberto={r.aberto:<9} "
                  f"gabarito={r.sentimento}{marca}")

    print("\nDistribuição no recorte, conforme o modelo escolhido:")
    for nome, coluna in (("proprietário", "proprietario"), ("aberto", "aberto"),
                         ("gabarito humano", "sentimento")):
        contagem = Counter(comparacao[coluna])
        negativas = contagem["negativo"]
        print(f"  {nome:<16} negativas: {negativas}/{n} = {100 * negativas / n:.1f}%"
              f"   {dict(contagem)}")
    print("Totais iguais podem esconder discordância item a item, porque erros "
          "em sentidos opostos se compensam. A coincidência do agregado não "
          "torna os classificadores intercambiáveis: trocar de modelo exige "
          "reprocessar o período inteiro, sob pena de comparar séries "
          "produzidas por critérios diferentes.")


def main():
    df = pd.read_csv(CORPUS)
    gab = pd.read_csv(GABARITO)
    rot = pd.read_csv(ROTULOS)

    parte_a(rot, gab)
    parte_b(df, gab)
    parte_c(df, rot, gab)

    print("\nNenhum desses números pode ser pedido ao modelo: todos saem de "
          "comparações feitas em código sobre rótulos gravados.")


if __name__ == "__main__":
    main()
