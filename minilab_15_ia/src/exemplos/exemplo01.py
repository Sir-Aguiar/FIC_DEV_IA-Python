# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: A falha — pedir estatística ao modelo em vez de contar
# Seção 2 – O Modelo Não Conta, Ele Estima
# Requisitos: pip install openai pandas python-dotenv
# ============================================================
#
# Este programa faz de propósito o que a aula recomenda NÃO fazer:
# entrega as 60 manifestações ao modelo de uma vez e pede que ele
# devolva os números agregados. Em seguida compara cada resposta com
# a contagem exata feita em Python sobre o mesmo arquivo.
#
# Uso:
#   python exemplo01.py            # esforço de raciocínio "none"
#   python exemplo01.py medium     # repete com raciocínio ativado
#
# O corpus manifestacoes_sinteticas.csv é SINTÉTICO: os 60 textos foram
# escritos para o curso e não correspondem a manifestações reais.

import json
import os
import sys
from collections import Counter

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

MODELO = "gpt-5.6-luna"
EXECUCOES = 3
ESFORCO = sys.argv[1] if len(sys.argv) > 1 else "none"

BASE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(BASE, "manifestacoes_sinteticas.csv")
GABARITO = os.path.join(BASE, "gabarito_manual.csv")
SAIDA = os.path.join(BASE, f"estimativas_lote_{ESFORCO}.json")

CLASSES = ["positivo", "negativo", "neutro", "misto"]


def montar_prompt(df: pd.DataFrame) -> str:
    """Monta o pedido em lote: todas as manifestações em uma única chamada."""
    linhas = [
        f"[{r.id}] ({r.data} | {r.orgao}) {r.texto}"
        for r in df.itertuples()
    ]
    return f"""Abaixo estão todas as manifestações recebidas pela Ouvidoria no período.

{chr(10).join(linhas)}

Analise o conjunto e responda em JSON, com estes campos exatos:

{{
  "total_manifestacoes": número inteiro de manifestações na lista,
  "manifestacoes_em_marco": quantas têm data em março de 2026,
  "por_orgao": {{ "nome do órgão": quantidade, ... }},
  "por_sentimento": {{ "positivo": n, "negativo": n, "neutro": n, "misto": n }},
  "percentual_negativas": percentual de manifestações negativas, com uma casa decimal
}}"""


def perguntar_em_lote(prompt: str) -> tuple[dict, int, int]:
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        reasoning_effort=ESFORCO,
        max_completion_tokens=16000,
    )
    uso = resposta.usage
    return (
        json.loads(resposta.choices[0].message.content),
        uso.prompt_tokens,
        uso.completion_tokens,
    )


def contar_em_python(df: pd.DataFrame, gab: pd.DataFrame) -> dict:
    """A verdade: contagem exata, feita pelo código, sobre o mesmo arquivo."""
    return {
        "total_manifestacoes": len(df),
        "manifestacoes_em_marco": int(df["data"].str.startswith("2026-03").sum()),
        "por_orgao": dict(Counter(df["orgao"])),
        "por_sentimento": {c: int((gab["sentimento"] == c).sum()) for c in CLASSES},
        "percentual_negativas": round(
            100 * (gab["sentimento"] == "negativo").sum() / len(gab), 1
        ),
    }


def comparar(real: dict, est: dict) -> list[tuple]:
    """Devolve (indicador, valor real, valor estimado, erro)."""
    linhas = []
    for campo in ("total_manifestacoes", "manifestacoes_em_marco"):
        v_real, v_est = real[campo], est.get(campo)
        linhas.append((campo, v_real, v_est, None if v_est is None else v_est - v_real))

    for classe in CLASSES:
        v_real = real["por_sentimento"][classe]
        v_est = est.get("por_sentimento", {}).get(classe)
        linhas.append(
            (f"sentimento: {classe}", v_real, v_est,
             None if v_est is None else v_est - v_real)
        )

    v_real, v_est = real["percentual_negativas"], est.get("percentual_negativas")
    linhas.append(
        ("percentual_negativas", v_real, v_est,
         None if v_est is None else round(v_est - v_real, 1))
    )
    return linhas


def main():
    df = pd.read_csv(CORPUS)
    gab = pd.read_csv(GABARITO)
    real = contar_em_python(df, gab)
    prompt = montar_prompt(df)

    print(f"Modelo: {MODELO} | reasoning_effort={ESFORCO} | {len(df)} manifestações\n")
    print("Contagem exata em Python (a verdade):")
    print(json.dumps(real, ensure_ascii=False, indent=2), "\n")

    estimativas = []
    for n in range(1, EXECUCOES + 1):
        est, entrada, saida = perguntar_em_lote(prompt)
        estimativas.append(est)

        print(f"--- Execução {n} ({entrada} tokens de entrada, {saida} de saída) ---")
        print(f"{'indicador':<26} {'real':>8} {'modelo':>8} {'erro':>8}")
        for nome, v_real, v_est, erro in comparar(real, est):
            texto_est = "ausente" if v_est is None else f"{v_est}"
            texto_erro = "-" if erro is None else f"{erro:+}"
            print(f"{nome:<26} {v_real:>8} {texto_est:>8} {texto_erro:>8}")

        soma = sum(est.get("por_sentimento", {}).get(c, 0) for c in CLASSES)
        print(f"{'soma das classes':<26} {len(df):>8} {soma:>8} {soma - len(df):>+8}")

        soma_orgaos = sum(est.get("por_orgao", {}).values())
        print(f"{'soma por órgão':<26} {len(df):>8} {soma_orgaos:>8} {soma_orgaos - len(df):>+8}\n")

    variacao = [e.get("percentual_negativas") for e in estimativas]
    print("Percentual de negativas em cada execução:", variacao)
    validos = [v for v in variacao if v is not None]
    if len(validos) > 1:
        print(f"Amplitude entre execuções: {max(validos) - min(validos):.1f} pontos percentuais")
    print(f"Valor correto, contado em Python: {real['percentual_negativas']}")

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(
            {"modelo": MODELO, "reasoning_effort": ESFORCO,
             "real": real, "estimativas": estimativas},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\nEstimativas gravadas em {os.path.basename(SAIDA)}")


if __name__ == "__main__":
    main()
