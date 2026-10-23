# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 07: Avaliação automatizada de um sistema RAG
# Seção 6 – Avaliar antes de colocar no ar
# Requisitos: pip install openai numpy python-dotenv
# ============================================================
"""Avalia as respostas do pipeline protegido com um modelo mais capaz.

Duas medidas são distintas e ambas necessárias. A **fidelidade** pergunta se a
resposta se sustenta nos trechos recuperados, e é o que separa a citação real
da citação decorativa. A **utilidade** pergunta se a resposta atende quem
perguntou, e uma resposta pode ser perfeitamente fiel e inútil.

O confronto com o gabarito objetivo, feito em paralelo, mostra onde o juiz
automático concorda com a verdade conhecida e onde ele se engana.
"""

import json

from exemplo02 import Chunker, rotulo_do_documento
from exemplo03 import PASTA, cliente, embutir, recuperar, normalizar
from exemplo05 import responder_com_guarda, RECUSA

MODELO_JUIZ = "gpt-5.6-terra"
LIMIAR = 0.50

ESQUEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "avaliacao_rag",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "fidelidade": {"type": "integer", "minimum": 0, "maximum": 2,
                               "description": "2 se toda afirmação está nos trechos, "
                                              "1 se parte, 0 se contradiz ou inventa"},
                "utilidade": {"type": "integer", "minimum": 0, "maximum": 2,
                              "description": "2 se responde direto, 1 se parcial, "
                                             "0 se não responde"},
                "justificativa": {"type": "string"},
            },
            "required": ["fidelidade", "utilidade", "justificativa"],
            "additionalProperties": False,
        },
    },
}

PROMPT_JUIZ = """Avalie a resposta de um sistema de perguntas sobre editais.

TRECHOS ENTREGUES AO SISTEMA:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA DO SISTEMA: {resposta}

Julgue apenas com base nos trechos acima. Uma recusa ("{recusa}") é fiel por \
definição, e é útil somente se os trechos realmente não contiverem a resposta."""


def julgar(pergunta: str, resposta: str, recuperados: list) -> dict:
    contexto = "\n\n".join(f"[{i + 1}] {c['texto']}"
                           for i, (c, _) in enumerate(recuperados))
    r = cliente.chat.completions.create(
        model=MODELO_JUIZ,
        messages=[{"role": "user", "content": PROMPT_JUIZ.format(
            contexto=contexto, pergunta=pergunta, resposta=resposta, recusa=RECUSA)}],
        response_format=ESQUEMA,
        max_completion_tokens=3000,
        reasoning_effort="low",
    )
    return json.loads(r.choices[0].message.content)


if __name__ == "__main__":
    dados = json.loads((PASTA / "perguntas_edital.json").read_text(encoding="utf-8"))
    chunks = []
    for arquivo in dados["acervo"]:
        texto = (PASTA / arquivo).read_text(encoding="utf-8")
        chunks += Chunker.por_clausula_com_titulo(texto, rotulo_do_documento(texto))
    matriz = embutir([c["texto"] for c in chunks])

    perguntas = (dados["perguntas_acervo"]
                 + [p for p in dados["perguntas"] if not p["respondivel"]])
    for p in perguntas:
        p.setdefault("respondivel", True)

    print(f"Avaliando {len(perguntas)} respostas com {MODELO_JUIZ}\n")
    print(f"{'P':<5}{'Gabarito':<12}{'Fid.':>6}{'Útil':>6}  Resposta")
    print("-" * 88)

    soma_f = soma_u = 0
    divergencias = []
    for p in perguntas:
        rec = recuperar(embutir([p["pergunta"]])[0], matriz, chunks)
        saida = responder_com_guarda(p["pergunta"], rec, LIMIAR)["resposta"]
        nota = julgar(p["pergunta"], saida, rec)
        soma_f += nota["fidelidade"]
        soma_u += nota["utilidade"]

        recusou = normalizar(RECUSA) in normalizar(saida)
        if p["respondivel"]:
            veredito = "ok" if (not recusou and any(
                normalizar(c) in normalizar(saida) for c in p["chaves"])) else "FALHOU"
        else:
            veredito = "ok" if recusou else "FALHOU"
        print(f"{p['id']:<5}{veredito:<12}{nota['fidelidade']:>6}"
              f"{nota['utilidade']:>6}  {saida[:52]}")

        if (veredito == "FALHOU") != (nota["fidelidade"] < 2 or nota["utilidade"] < 2):
            divergencias.append((p["id"], veredito, nota))

    n = len(perguntas)
    print(f"\nFidelidade média: {soma_f / n:.2f} de 2  |  "
          f"Utilidade média: {soma_u / n:.2f} de 2")
    print(f"\nCasos em que o juiz automático e o gabarito discordaram: "
          f"{len(divergencias)}")
    for pid, veredito, nota in divergencias:
        print(f"  P{pid}: gabarito diz {veredito}, juiz deu fidelidade "
              f"{nota['fidelidade']} e utilidade {nota['utilidade']} — "
              f"{nota['justificativa'][:110]}")
