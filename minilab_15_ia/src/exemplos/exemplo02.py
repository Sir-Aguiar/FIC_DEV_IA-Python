# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Classificação individual com esquema estrito
# Seção 3.2 – Etapa 1: o modelo classifica, uma manifestação por vez
# Requisitos: pip install openai pandas python-dotenv
# ============================================================
#
# Cada manifestação é enviada isoladamente e volta como um objeto
# validado contra o esquema. Nenhum número é pedido ao modelo: ele
# apenas atribui rótulos. A contagem vem depois, no exemplo03.py.
#
# Uso:
#   python exemplo02.py            # classifica as 60 manifestações
#   python exemplo02.py 5          # classifica apenas as 5 primeiras

import csv
import os
import sys
import time
from datetime import datetime, timezone
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()
client = OpenAI()

MODELO = "gpt-5.6-luna"
ESFORCO = "low"

# Preço por 1M de tokens, faixa de contexto curto (OpenAI, ago. 2026)
PRECO_ENTRADA, PRECO_SAIDA = 0.20, 1.20

BASE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(BASE, "manifestacoes_sinteticas.csv")
ROTULOS = os.path.join(BASE, "rotulos.csv")


class Classificacao(BaseModel):
    """Rótulos atribuídos a UMA manifestação de ouvidoria.

    Todos os campos categóricos usam Literal, que vira `enum` no esquema:
    o modelo fica impedido de devolver valor fora da lista, e a contagem
    posterior não precisa tratar grafias divergentes.
    """

    sentimento: Literal["positivo", "negativo", "neutro", "misto"] = Field(
        description="Polaridade predominante. Use 'misto' quando houver elogio e "
                    "crítica relevantes no mesmo texto; 'neutro' apenas para pedidos "
                    "de informação e sugestões sem carga avaliativa."
    )
    intensidade: Literal["leve", "moderada", "forte"] = Field(
        description="Força da carga emocional expressa no texto."
    )
    tipo: Literal["reclamacao", "elogio", "sugestao", "denuncia", "duvida"] = Field(
        description="Natureza da manifestação segundo a classificação de ouvidoria."
    )
    tema: Literal[
        "atendimento", "prazo_e_demora", "infraestrutura", "sistema_e_tecnologia",
        "disponibilidade_de_servico", "conduta_de_servidor",
        "informacao_e_transparencia", "outro",
    ] = Field(description="Tema predominante, escolhido na lista fechada.")
    urgencia: Literal["alta", "media", "baixa"] = Field(
        description="Alta apenas quando houver risco à vida, à saúde ou perda de direito."
    )
    requer_resposta: bool = Field(
        description="Verdadeiro quando o cidadão pede providência ou informação."
    )
    ambiguidade: Literal["clara", "limitrofe"] = Field(
        description="Use 'limitrofe' quando houver ironia, crítica em tom cordial "
                    "ou elogio com ressalva relevante, casos em que outro leitor "
                    "poderia atribuir rótulo diferente."
    )
    trecho_determinante: str = Field(
        description="Trecho copiado literalmente do texto que decidiu o sentimento, "
                    "em no máximo 15 palavras."
    )


INSTRUCAO = (
    "Você classifica manifestações de ouvidoria pública do Estado de Mato Grosso. "
    "Considere a intenção do cidadão, não apenas as palavras: ironia e crítica "
    "cordial contam como avaliação negativa. Não invente informação ausente do texto."
)


def classificar(texto: str) -> tuple[Classificacao, int, int]:
    """Classifica uma manifestação e devolve o objeto validado e o consumo."""
    resposta = client.chat.completions.parse(
        model=MODELO,
        messages=[
            {"role": "system", "content": INSTRUCAO},
            {"role": "user", "content": f"MANIFESTAÇÃO:\n{texto}"},
        ],
        response_format=Classificacao,
        reasoning_effort=ESFORCO,
        max_completion_tokens=4000,
    )

    mensagem = resposta.choices[0].message
    if mensagem.refusal:
        raise RuntimeError(f"Pedido recusado pelo modelo: {mensagem.refusal}")

    return mensagem.parsed, resposta.usage.prompt_tokens, resposta.usage.completion_tokens


COLUNAS = [
    "id", "data", "canal", "orgao", "sentimento", "intensidade", "tipo", "tema",
    "urgencia", "requer_resposta", "ambiguidade", "trecho_determinante",
    "modelo", "classificado_em",
]


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else None
    df = pd.read_csv(CORPUS)
    if limite:
        df = df.head(limite)

    carimbo = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entrada_total = saida_total = 0
    falhas = []
    inicio = time.perf_counter()

    with open(ROTULOS, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()

        for n, linha in enumerate(df.itertuples(), 1):
            try:
                rotulo, entrada, saida = classificar(linha.texto)
            except Exception as erro:                      # rede, cota, recusa
                falhas.append((linha.id, type(erro).__name__))
                print(f"[{n:>3}/{len(df)}] {linha.id}  FALHA: {erro}")
                continue

            entrada_total += entrada
            saida_total += saida

            # O órgão NÃO é perguntado ao modelo: já é campo estruturado do sistema.
            escritor.writerow({
                "id": linha.id, "data": linha.data, "canal": linha.canal,
                "orgao": linha.orgao, "modelo": MODELO, "classificado_em": carimbo,
                **rotulo.model_dump(),
            })
            print(f"[{n:>3}/{len(df)}] {linha.id}  {rotulo.sentimento:<9}"
                  f"{rotulo.tipo:<12}{rotulo.tema:<28}{rotulo.ambiguidade}")

    decorrido = time.perf_counter() - inicio
    classificadas = len(df) - len(falhas)
    custo = entrada_total / 1e6 * PRECO_ENTRADA + saida_total / 1e6 * PRECO_SAIDA

    print(f"\nClassificadas: {classificadas} de {len(df)}  |  falhas: {len(falhas)}")
    print(f"Tempo total: {decorrido:.1f} s  ({decorrido / max(classificadas, 1):.2f} s por manifestação)")
    print(f"Tokens: {entrada_total} de entrada, {saida_total} de saída")
    print(f"Custo medido: US$ {custo:.4f}  |  projeção para 5.000: "
          f"US$ {custo / max(classificadas, 1) * 5000:.2f}")
    if falhas:
        print("Manifestações não classificadas:", falhas)
    print(f"Rótulos gravados em {os.path.basename(ROTULOS)}")


if __name__ == "__main__":
    main()
