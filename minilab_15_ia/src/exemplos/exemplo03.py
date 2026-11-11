# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Agregação em Python — o código conta
# Seção 3.4 – Etapa 3: contagens, percentuais e séries
# Requisitos: pip install pandas
# ============================================================
#
# Nenhuma chamada de API acontece aqui. Todo número do relatório nasce
# de uma operação sobre a tabela de rótulos gravada pelo exemplo02.py.
# O resultado vai para indicadores.json, único insumo numérico que o
# exemplo04.py entrega ao modelo redator.

import json
import math
import os

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
ROTULOS = os.path.join(BASE, "rotulos.csv")
GABARITO = os.path.join(BASE, "gabarito_manual.csv")
INDICADORES = os.path.join(BASE, "indicadores.json")

# As 60 manifestações são o conjunto completo do período, e não uma amostra
# dele. Com censo, o percentual é exato e não cabe margem de erro amostral.
# Se você tiver classificado apenas parte do universo, mude para True.
E_AMOSTRA = False


def intervalo_wilson(sucessos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de 95% para uma proporção (método de Wilson)."""
    if n == 0:
        return (0.0, 0.0)
    p = sucessos / n
    divisor = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / divisor
    meia = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / divisor
    return (round(max(0.0, centro - meia) * 100, 1),
            round(min(1.0, centro + meia) * 100, 1))


def distribuicao(serie: pd.Series, n: int) -> dict:
    """Contagem e percentual por categoria, sempre com o denominador explícito."""
    contagem = serie.value_counts()
    saida = {}
    for categoria, quantidade in contagem.items():
        item = {"n": int(quantidade), "percentual": round(100 * quantidade / n, 1)}
        if E_AMOSTRA:
            item["ic95"] = intervalo_wilson(int(quantidade), n)
        saida[str(categoria)] = item
    return saida


def acuracia_contra_gabarito(rot: pd.DataFrame) -> dict:
    """Compara os rótulos do modelo com o conjunto rotulado à mão."""
    if not os.path.exists(GABARITO):
        return {"conferencia_manual": "não realizada"}

    gab = pd.read_csv(GABARITO)
    junto = rot.merge(gab, on="id", suffixes=("_modelo", "_humano"))
    if junto.empty:
        return {"conferencia_manual": "não realizada"}

    acertos_sent = int((junto["sentimento_modelo"] == junto["sentimento_humano"]).sum())
    acertos_tipo = int((junto["tipo_modelo"] == junto["tipo_humano"]).sum())
    n = len(junto)

    discordancias = [
        {"id": r.id, "humano": r.sentimento_humano, "modelo": r.sentimento_modelo}
        for r in junto.itertuples()
        if r.sentimento_modelo != r.sentimento_humano
    ]

    return {
        "n_conferido": n,
        "acuracia_sentimento_percentual": round(100 * acertos_sent / n, 1),
        "acuracia_tipo_percentual": round(100 * acertos_tipo / n, 1),
        "discordancias_de_sentimento": discordancias,
    }


def main():
    rot = pd.read_csv(ROTULOS)
    n = len(rot)
    rot["mes"] = rot["data"].str.slice(0, 7)

    limitrofes = int((rot["ambiguidade"] == "limitrofe").sum())

    # Série mensal de negativas: contagem e percentual dentro de cada mês.
    serie = {}
    for mes, grupo in rot.groupby("mes"):
        negativas = int((grupo["sentimento"] == "negativo").sum())
        serie[mes] = {
            "n": len(grupo),
            "negativas": negativas,
            "percentual_negativas": round(100 * negativas / len(grupo), 1),
        }

    # Órgãos: o percentual de negativas só é comparável com o n ao lado.
    orgaos = {}
    for orgao, grupo in rot.groupby("orgao"):
        negativas = int((grupo["sentimento"] == "negativo").sum())
        orgaos[orgao] = {
            "n": len(grupo),
            "negativas": negativas,
            "percentual_negativas": round(100 * negativas / len(grupo), 1),
        }
    orgaos = dict(sorted(orgaos.items(), key=lambda kv: -kv[1]["n"]))

    indicadores = {
        "ficha_tecnica": {
            "n_total": n,
            "periodo": f"{rot['data'].min()} a {rot['data'].max()}",
            "origem": "corpus sintético do curso (manifestacoes_sinteticas.csv)",
            "tipo_de_levantamento": "amostra" if E_AMOSTRA else "censo do período",
            "modelo_classificador": sorted(rot["modelo"].unique().tolist()),
            "classificado_em": sorted(rot["classificado_em"].unique().tolist()),
            "casos_limitrofes": limitrofes,
            "percentual_limitrofes": round(100 * limitrofes / n, 1),
            "qualidade_do_classificador": acuracia_contra_gabarito(rot),
        },
        "por_sentimento": distribuicao(rot["sentimento"], n),
        "por_tipo": distribuicao(rot["tipo"], n),
        "por_tema": distribuicao(rot["tema"], n),
        "por_canal": distribuicao(rot["canal"], n),
        "por_urgencia": distribuicao(rot["urgencia"], n),
        "por_orgao": orgaos,
        "serie_mensal": serie,
        "requerem_resposta": {
            "n": int(rot["requer_resposta"].sum()),
            "percentual": round(100 * rot["requer_resposta"].sum() / n, 1),
        },
    }

    with open(INDICADORES, "w", encoding="utf-8") as f:
        json.dump(indicadores, f, ensure_ascii=False, indent=2)

    ficha = indicadores["ficha_tecnica"]
    print(f"Manifestações classificadas: {n}  ({ficha['tipo_de_levantamento']})")
    print(f"Período: {ficha['periodo']}")
    print(f"Casos limítrofes: {limitrofes} ({ficha['percentual_limitrofes']}%)\n")

    print("Distribuição por sentimento")
    for classe, dados in indicadores["por_sentimento"].items():
        faixa = f"  IC95 {dados['ic95']}" if "ic95" in dados else ""
        print(f"  {classe:<10} {dados['n']:>3} de {n}   {dados['percentual']:>5}%{faixa}")

    print("\nNegativas por órgão (ordenado por volume)")
    for orgao, dados in indicadores["por_orgao"].items():
        print(f"  {orgao:<34} {dados['negativas']:>2}/{dados['n']:<3} "
              f"{dados['percentual_negativas']:>5}%")

    print("\nSérie mensal")
    for mes, dados in indicadores["serie_mensal"].items():
        print(f"  {mes}  {dados['negativas']:>2}/{dados['n']:<3} "
              f"{dados['percentual_negativas']:>5}% negativas")

    qualidade = ficha["qualidade_do_classificador"]
    if "n_conferido" in qualidade:
        print(f"\nConferência contra {qualidade['n_conferido']} rótulos manuais: "
              f"acurácia de {qualidade['acuracia_sentimento_percentual']}% no sentimento e "
              f"{qualidade['acuracia_tipo_percentual']}% no tipo")
        if qualidade["discordancias_de_sentimento"]:
            print("  Discordâncias:", qualidade["discordancias_de_sentimento"])

    print(f"\nIndicadores gravados em {os.path.basename(INDICADORES)}")


if __name__ == "__main__":
    main()
