# ============================================================
# Aula 14 – Análise de Sentimentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: Relatório com números calculados e conferidos
# Seções 3.5 e 3.6 – Etapa 4: o modelo redige, e a guarda confere
# Requisitos: pip install openai python-dotenv
# ============================================================
#
# O modelo recebe indicadores.json já calculado pelo exemplo03.py e
# escreve apenas a interpretação. Depois, uma guarda numérica confere
# se todo algarismo do texto existe entre os valores autorizados; o que
# não existir volta ao modelo para correção.

import json
import os
import re
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

MODELO = "gpt-5.6-luna"
TENTATIVAS = 3
TOLERANCIA = 0.051          # margem para arredondamento de uma casa decimal

BASE = os.path.dirname(os.path.abspath(__file__))
INDICADORES = os.path.join(BASE, "indicadores.json")
RELATORIO = os.path.join(BASE, "relatorio_ouvidoria.md")

INSTRUCAO = """Você redige relatórios da Ouvidoria Geral do Estado de Mato Grosso.

REGRA ABSOLUTA: você não calcula nada. Todos os números já vêm calculados no
JSON de indicadores. Você pode copiá-los, jamais somá-los, dividi-los, convertê-los
em outra base ou estimar valores que não estejam ali.

Regras de redação:
1. Use algarismos EXCLUSIVAMENTE para valores presentes no JSON, copiados sem alteração.
2. Qualquer outra quantidade deve ser escrita por extenso (por exemplo, "quatro órgãos").
3. Todo percentual citado deve vir acompanhado do total sobre o qual foi calculado.
4. Estratos com menos de dez manifestações não sustentam conclusão: se os mencionar,
   registre explicitamente que o número de casos é pequeno demais para generalizar.
5. Não afirme tendência de alta ou de queda sem que a série mensal a sustente.
6. Use vírgula como separador decimal, na norma brasileira.
7. Linguagem formal e impessoal, adequada a documento oficial."""

ESTRUTURA = """Escreva o relatório em Markdown com esta estrutura, mantendo a
numeração das seções em algarismos exatamente como aparece abaixo:

## 1. Ficha técnica
## 2. Resumo executivo
## 3. Distribuição das manifestações
## 4. Órgãos e temas em destaque
## 5. Limitações do levantamento
## 6. Recomendações"""

# Texto de teste da guarda: os três primeiros números vêm de indicadores.json;
# os quatro últimos (12, 67, 1.523 e 8,4) são invenções do tipo que um modelo
# produz ao calcular sozinho. O "12 dias" é armadilha proposital: o valor existe
# nos indicadores com outro significado, e por isso a guarda o deixa passar.
AUTOTESTE = """No período foram registradas 60 manifestações, das quais 24 negativas,
correspondentes a 40,0% do total. As reclamações somaram 27 registros e o tempo médio
de resposta foi de 12 dias. A taxa de resolução alcançou 67%, com 1.523 manifestações
positivas e queda de 8,4 pontos percentuais em relação ao semestre anterior."""


def coletar_valores(no, destino: set) -> set:
    """Percorre o JSON e reúne todo número autorizado a aparecer no texto."""
    if isinstance(no, dict):
        for chave, valor in no.items():
            coletar_valores(chave, destino)
            coletar_valores(valor, destino)
    elif isinstance(no, (list, tuple)):
        for item in no:
            coletar_valores(item, destino)
    elif isinstance(no, bool):
        pass
    elif isinstance(no, (int, float)):
        destino.add(float(no))
    elif isinstance(no, str):
        # datas e rótulos como "2026-01" trazem números legítimos
        for achado in re.findall(r"\d+(?:\.\d+)?", no):
            destino.add(float(achado))
    return destino


def numeros_do_texto(texto: str) -> list[tuple[str, float]]:
    """Extrai os algarismos do relatório, ignorando numeração de seção."""
    sem_titulos = re.sub(r"(?m)^#{1,6}\s*\d+\.", "#", texto)
    achados = []
    for bruto in re.findall(r"\d[\d.,]*", sem_titulos):
        limpo = bruto.rstrip(".,")
        if "," in limpo:                       # 40,0 -> 40.0 (decimal brasileiro)
            limpo = limpo.replace(".", "").replace(",", ".")
        elif limpo.count(".") == 1 and len(limpo.split(".")[1]) == 3:
            limpo = limpo.replace(".", "")     # 5.234 -> 5234 (milhar brasileiro)
        try:
            achados.append((bruto, float(limpo)))
        except ValueError:
            continue
    return achados


def conferir(texto: str, permitidos: set) -> list[str]:
    """Devolve os números do texto que não existem entre os indicadores."""
    suspeitos = []
    for bruto, valor in numeros_do_texto(texto):
        if not any(abs(valor - p) <= TOLERANCIA for p in permitidos):
            suspeitos.append(bruto)
    return sorted(set(suspeitos), key=suspeitos.index)


# Mesma faixa de preço do exemplo02.py, por 1 milhão de tokens.
PRECO_ENTRADA, PRECO_SAIDA = 0.20, 1.20


def redigir(mensagens: list[dict]) -> str:
    inicio = time.perf_counter()
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        reasoning_effort="low",
        max_completion_tokens=8000,
    )
    uso = resposta.usage
    decorrido = time.perf_counter() - inicio
    custo = uso.prompt_tokens / 1e6 * PRECO_ENTRADA + uso.completion_tokens / 1e6 * PRECO_SAIDA
    print(f"Tokens: {uso.prompt_tokens} de entrada, {uso.completion_tokens} de saída")
    print(f"Tempo da chamada: {decorrido:.1f} s  |  custo: US$ {custo:.4f}")
    return resposta.choices[0].message.content


def autoteste(permitidos: set) -> None:
    """Prova que a guarda funciona: roda-a sobre um texto com números inventados."""
    print("Texto de teste:\n" + AUTOTESTE + "\n")
    suspeitos = conferir(AUTOTESTE, permitidos)
    print(f"Números encontrados: {[b for b, _ in numeros_do_texto(AUTOTESTE)]}")
    print(f"Reprovados pela guarda: {suspeitos}")
    print("\nTrês das quatro invenções foram barradas. A quarta, o '12' do tempo "
          "médio de resposta, passou porque esse valor existe nos indicadores com "
          "outro significado. A guarda detecta número ausente da tabela; número "
          "presente e mal atribuído continua sendo trabalho da revisão humana.")


def main():
    with open(INDICADORES, encoding="utf-8") as f:
        indicadores = json.load(f)

    permitidos = coletar_valores(indicadores, set())
    print(f"Valores autorizados a aparecer no relatório: {len(permitidos)}\n")

    if "--autoteste" in sys.argv:
        autoteste(permitidos)
        return

    mensagens = [
        {"role": "system", "content": INSTRUCAO},
        {"role": "user", "content":
            f"INDICADORES JÁ CALCULADOS:\n\n"
            f"{json.dumps(indicadores, ensure_ascii=False, indent=2)}\n\n{ESTRUTURA}"},
    ]

    texto, suspeitos = "", []
    for tentativa in range(1, TENTATIVAS + 1):
        texto = redigir(mensagens)
        suspeitos = conferir(texto, permitidos)
        print(f"Tentativa {tentativa}: {len(numeros_do_texto(texto))} números no texto, "
              f"{len(suspeitos)} não conferem" + (f" -> {suspeitos}" if suspeitos else ""))

        if not suspeitos:
            break

        mensagens += [
            {"role": "assistant", "content": texto},
            {"role": "user", "content":
                f"Os números {suspeitos} não constam dos indicadores fornecidos. "
                f"Reescreva o relatório inteiro removendo-os ou substituindo-os pelo "
                f"valor correto do JSON. Números que não venham do JSON devem ser "
                f"escritos por extenso."},
        ]

    aprovado = not suspeitos
    cabecalho = (
        "<!-- Números conferidos automaticamente contra indicadores.json -->\n"
        if aprovado else
        f"> **REPROVADO NA CONFERÊNCIA AUTOMÁTICA.** Os valores {suspeitos} não foram "
        f"localizados nos indicadores. Revisão humana obrigatória antes de qualquer uso.\n\n"
    )

    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write(cabecalho + texto)

    print(f"\nSituação: {'APROVADO' if aprovado else 'REPROVADO — revisão humana obrigatória'}")
    print(f"Relatório gravado em {os.path.basename(RELATORIO)}\n")
    print(texto)


if __name__ == "__main__":
    main()
