# ============================================================
# Aula 12 – Introdução ao RAG (Retrieval-Augmented Generation)
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 05: Fazer o sistema dizer "não encontrei"
# Seção 4.4 – Abstenção calibrada e verificação de ancoragem
# Requisitos: pip install openai numpy python-dotenv
# ============================================================
"""Compara o RAG ingênuo com o RAG protegido por três guardas.

  Guarda 1  limiar de similaridade, calibrado com dados e não por palpite;
  Guarda 2  contrato de saída: a recusa tem um formato fixo, reconhecível;
  Guarda 3  ancoragem: número que não está no contexto invalida a resposta.

O conjunto tem 12 perguntas cuja resposta está nos editais e 5 cuja resposta
não está. Um sistema honesto acerta as primeiras e recusa as segundas.
"""

import json
import pathlib

from exemplo02 import Chunker, rotulo_do_documento
from exemplo03 import PASTA, cliente, MODELO_LLM, embutir, recuperar, normalizar
from exemplo04 import ancoragem, gerar, PROMPT_INGENUO

RECUSA = "NÃO ENCONTRADO"

PROMPT_COM_CONTRATO = """Você responde sobre editais de licitação do Estado de \
Mato Grosso para uso em processo administrativo.

Regras invioláveis:
1. Use exclusivamente os trechos numerados abaixo. Conhecimento próprio é proibido.
2. Não calcule, não estime e não deduza valores que não estejam escritos.
3. Confira se o trecho se refere ao edital sobre o qual se pergunta.
4. Se a resposta não estiver literalmente nos trechos, escreva apenas: {recusa}
5. Cite a fonte no formato [n] ao final de cada afirmação.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""


def responder_com_guarda(pergunta: str, recuperados: list, limiar: float) -> dict:
    """Pipeline protegido. Devolve a resposta e o motivo de eventual recusa."""
    if recuperados[0][1] < limiar:                       # Guarda 1
        return {"resposta": RECUSA, "motivo": f"similaridade {recuperados[0][1]:.3f}"
                                              f" abaixo do limiar {limiar}"}

    texto = gerar(pergunta, recuperados,                 # Guarda 2
                  PROMPT_COM_CONTRATO.replace("{recusa}", RECUSA))
    if normalizar(RECUSA) in normalizar(texto):
        return {"resposta": RECUSA, "motivo": "o modelo declarou não encontrar"}

    _, orfaos = ancoragem(texto, recuperados)            # Guarda 3
    if orfaos:
        return {"resposta": RECUSA,
                "motivo": f"números sem lastro no contexto: {orfaos}"}
    return {"resposta": texto, "motivo": ""}


def classificar(p: dict, resposta: str) -> str:
    """Compara a resposta com o gabarito e devolve o veredito.

    Para as perguntas sem resposta no acervo há apenas dois vereditos possíveis,
    porque só isso é verificável por máquina: ou a saída segue o contrato de
    recusa, ou é texto livre que alguém precisa ler. Modelos de 2026 recusam com
    frequência por conta própria, porém em redação variável — e um sistema a
    jusante não consegue distinguir essa recusa de uma resposta afirmativa.
    """
    r = normalizar(resposta)
    recusou = normalizar(RECUSA) in r
    if p["respondivel"]:
        if recusou:
            return "recusa indevida"
        return "acerto" if any(normalizar(c) in r for c in p["chaves"]) else "erro"
    return "recusa no contrato" if recusou else "resposta livre"


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
    vetores = embutir([p["pergunta"] for p in perguntas])
    recuperacoes = [recuperar(v, matriz, chunks) for v in vetores]

    # ---------- Calibração do limiar ---------------------------------
    print("Similaridade do primeiro trecho recuperado\n")
    com = [r[0][1] for p, r in zip(perguntas, recuperacoes) if p["respondivel"]]
    sem = [r[0][1] for p, r in zip(perguntas, recuperacoes) if not p["respondivel"]]
    print(f"  perguntas com resposta no acervo ({len(com)}): "
          f"mínimo {min(com):.3f} | mediana {sorted(com)[len(com) // 2]:.3f} "
          f"| máximo {max(com):.3f}")
    print(f"  perguntas sem resposta no acervo ({len(sem)}): "
          f"mínimo {min(sem):.3f} | mediana {sorted(sem)[len(sem) // 2]:.3f} "
          f"| máximo {max(sem):.3f}")
    print("\n  limiar   corta perguntas respondíveis   corta perguntas sem resposta")
    for limiar in [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
        print(f"   {limiar:.2f}{sum(1 for s in com if s < limiar):>26}"
              f"{sum(1 for s in sem if s < limiar):>32}")

    LIMIAR = 0.50
    print(f"\nLimiar adotado: {LIMIAR}. Ele sozinho não resolve — daí as guardas 2 e 3.\n")

    # ---------- Comparação: ingênuo x protegido ----------------------
    placar = {"ingênuo": {}, "protegido": {}}
    sem_lastro = {"ingênuo": 0, "protegido": 0}
    for p, rec in zip(perguntas, recuperacoes):
        bruto = gerar(p["pergunta"], rec, PROMPT_INGENUO)
        guardado = responder_com_guarda(p["pergunta"], rec, LIMIAR)
        for nome, texto in [("ingênuo", bruto), ("protegido", guardado["resposta"])]:
            v = classificar(p, texto)
            placar[nome][v] = placar[nome].get(v, 0) + 1
            if ancoragem(texto, rec)[1]:
                sem_lastro[nome] += 1
        if not p["respondivel"]:
            print(f"P{p['id']}: {p['pergunta']}")
            print(f"   ingênuo   → {bruto[:110]}")
            print(f"   protegido → {guardado['resposta'][:60]}"
                  f"{'  (' + guardado['motivo'] + ')' if guardado['motivo'] else ''}\n")
        elif normalizar(RECUSA) in normalizar(guardado["resposta"]):
            print(f"P{p['id']} tinha resposta no acervo e mesmo assim foi recusada: "
                  f"{guardado['motivo']}\n")

    print(f"\n{'Veredito':<20}{'Ingênuo':>10}{'Protegido':>12}")
    print("-" * 42)
    for v in ["acerto", "erro", "recusa indevida", "recusa no contrato",
              "resposta livre"]:
        print(f"{v:<20}{placar['ingênuo'].get(v, 0):>10}"
              f"{placar['protegido'].get(v, 0):>12}")
    print(f"{'com nº sem lastro':<20}{sem_lastro['ingênuo']:>10}"
          f"{sem_lastro['protegido']:>12}")
