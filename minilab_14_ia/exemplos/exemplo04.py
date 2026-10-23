# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: As três falhas típicas de um RAG e como detectá-las
# Seção 4 – Quando o RAG erra
# Requisitos: pip install openai numpy python-dotenv
# ============================================================
"""Provoca deliberadamente as três falhas e mostra o detector de cada uma.

  Falha 1  a recuperação traz o trecho errado;
  Falha 2  o modelo responde sem contexto suficiente;
  Falha 3  a resposta cita uma fonte que não sustenta a afirmação.

Nenhuma delas produz erro de execução: o programa devolve texto plausível nos
três casos. Só a medição revela o problema.
"""

import json
import pathlib
import re

from exemplo02 import Chunker, rotulo_do_documento
from exemplo03 import PASTA, cliente, MODELO_LLM, embutir, recuperar, normalizar

# Prompt sem regra de abstenção — é assim que a maioria dos tutoriais começa
PROMPT_INGENUO = """Responda à pergunta com base nos trechos abaixo.
Cite a fonte no formato [n].

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""


def gerar(pergunta: str, recuperados: list, modelo_prompt=PROMPT_INGENUO) -> str:
    contexto = "\n\n".join(f"[{i + 1}] {c['texto']}"
                           for i, (c, _) in enumerate(recuperados))
    r = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=[{"role": "user",
                   "content": modelo_prompt.format(contexto=contexto,
                                                   pergunta=pergunta)}],
        max_completion_tokens=300,
        reasoning_effort="none",
    )
    return r.choices[0].message.content.strip()


# ---------------------------------------------------------------- detectores
def margem(recuperados: list) -> float:
    """Distância entre o primeiro e o último trecho recuperado.

    Margem baixa significa que o índice não soube separar os candidatos: todos
    parecem igualmente relevantes, e a escolha do modelo vira sorteio.
    """
    return recuperados[0][1] - recuperados[-1][1]


NUMERO = re.compile(r"\d+(?:[.,]\d+)*\s*%?")


def ancoragem(resposta: str, recuperados: list) -> tuple:
    """Verifica se cada número da resposta existe em algum trecho recuperado.

    É a verificação mais barata de fidelidade: números são o que mais importa
    em edital e o que o modelo mais troca de lugar.
    """
    contexto = " ".join(normalizar(c["texto"]) for c, _ in recuperados)
    numeros = [n.strip() for n in NUMERO.findall(resposta)]
    orfaos = [n for n in numeros if normalizar(n) not in contexto]
    return len(numeros), orfaos


if __name__ == "__main__":
    dados = json.loads((PASTA / "perguntas_edital.json").read_text(encoding="utf-8"))
    corpo = {}
    chunks = []
    for arquivo in dados["acervo"]:
        texto = (PASTA / arquivo).read_text(encoding="utf-8")
        corpo[arquivo] = texto
        # chunking ingênuo, de tamanho fixo: é ele que produz as falhas
        chunks += Chunker.por_tamanho_fixo(texto, rotulo_do_documento(texto), 400, 0)

    matriz = embutir([c["texto"] for c in chunks])
    print(f"Acervo: {len(dados['acervo'])} editais, {len(chunks)} chunks de 400 "
          f"caracteres\n")

    # ---------------- Falha 1: recuperação traz o trecho errado -------------
    print("=" * 70)
    print("FALHA 1 — A RECUPERAÇÃO TRAZ O TRECHO ERRADO")
    print("=" * 70)
    p = next(x for x in dados["perguntas_acervo"] if x["id"] == 107)
    vec = embutir([p["pergunta"]])[0]
    rec = recuperar(vec, matriz, chunks)
    resposta = gerar(p["pergunta"], rec)
    print(f"Pergunta:  {p['pergunta']}")
    print(f"Gabarito:  {p['trecho_gabarito']} ({p['documento']}, cl. {p['clausula']})")
    print(f"Resposta:  {resposta}")
    print("Trechos recuperados:")
    for i, (c, s) in enumerate(rec, 1):
        print(f"  [{i}] sim. {s:.3f} — {c['origem']}")
    achou = p["trecho_gabarito"] in " ".join(c["texto"] for c, _ in rec)
    print(f"\nDetector: trecho-gabarito no contexto? {'sim' if achou else 'NÃO'}")
    print(f"Detector: margem entre o 1º e o 3º trecho = {margem(rec):.3f}")

    # ---------------- Falha 2: responde sem contexto suficiente -------------
    print("\n" + "=" * 70)
    print("FALHA 2 — O MODELO RESPONDE SEM CONTEXTO SUFICIENTE")
    print("=" * 70)
    for p in [x for x in dados["perguntas"] if not x["respondivel"]]:
        vec = embutir([p["pergunta"]])[0]
        rec = recuperar(vec, matriz, chunks)
        resposta = gerar(p["pergunta"], rec)
        marcada = "nao encontrado" in normalizar(resposta)
        print(f"\nPergunta:  {p['pergunta']}")
        print(f"           (não consta de nenhum dos dois editais)")
        print(f"Resposta:  {resposta[:190]}")
        print(f"Detector: similaridade do 1º trecho = {rec[0][1]:.3f} | "
              f"recusa em formato reconhecível pelo sistema: "
              f"{'sim' if marcada else 'NÃO'}")

    # ---------------- Falha 3: citação que não sustenta ---------------------
    print("\n" + "=" * 70)
    print("FALHA 3 — A CITAÇÃO NÃO SUSTENTA A AFIRMAÇÃO")
    print("=" * 70)
    suspeitas = 0
    todas = dados["perguntas_acervo"] + [x for x in dados["perguntas"]
                                         if not x["respondivel"]]
    for p in todas:
        vec = embutir([p["pergunta"]])[0]
        rec = recuperar(vec, matriz, chunks)
        resposta = gerar(p["pergunta"], rec)
        total, orfaos = ancoragem(resposta, rec)
        if orfaos:
            suspeitas += 1
            print(f"\nPergunta {p['id']}: {p['pergunta']}")
            print(f"Resposta: {resposta[:170]}")
            print(f"Detector: {len(orfaos)} de {total} números da resposta "
                  f"não aparecem em nenhum trecho citado → {orfaos}")
    print(f"\nRespostas com número sem lastro no contexto: "
          f"{suspeitas} de {len(todas)}")
    print("O detector numérico não alcança a pergunta 17: o número citado existe "
          "no contexto,\nporém veio do edital errado. Essa falha só aparece na "
          "conferência da fonte.")
