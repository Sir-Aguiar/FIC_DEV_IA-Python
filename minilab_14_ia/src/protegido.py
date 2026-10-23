# ============================================================
# Pipeline protegido — fazer o sistema dizer "não encontrei"
# Acervo: Regimento Interno da MTI (5 subseções)
# Embedding: Gemini  |  Chat: Groq
# Execução: python src/protegido.py
# ============================================================
"""Compara o RAG ingênuo com o RAG protegido por três guardas.

  Guarda 1  limiar de similaridade, calibrado com as 14 perguntas do acervo;
  Guarda 2  contrato de saída: a recusa tem um formato fixo, reconhecível;
  Guarda 3  ancoragem: número que não está no contexto invalida a resposta.

O conjunto tem 10 perguntas cuja resposta está no acervo e 4 cuja resposta
não está (uma delas é armadilha aritmética).
"""

from __future__ import annotations

import json
import math
import re

from chunking import ESTRATEGIAS, chunkar_acervo
from experimento import (
    IDS_ACERVO,
    MODELO_EMBEDDING,
    MODELO_LLM,
    PASTA,
    _com_retry,
    carregar_secoes,
    embutir,
    groq,
    normalizar,
    plano,
    recuperar,
)

ESTRATEGIA = "janela_200_50"
RECUSA = "NÃO ENCONTRADO"

PROMPT_INGENUO = """Responda à pergunta com base nos trechos abaixo.
Cite a fonte no formato [n].

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""

PROMPT_COM_CONTRATO = """Você responde sobre o Regimento Interno da Empresa \
Mato-grossense de Tecnologia da Informação - MTI para uso em processo \
administrativo.

Regras invioláveis:
1. Use exclusivamente os trechos numerados abaixo. Conhecimento próprio é proibido.
2. Não calcule, não estime e não deduza valores que não estejam escritos.
3. Confira se o trecho se refere ao órgão ou à unidade sobre a qual se pergunta.
4. Se a resposta não estiver literalmente nos trechos, escreva apenas: {recusa}
5. Cite a fonte no formato [n] ao final de cada afirmação.

TRECHOS:
{contexto}

PERGUNTA: {pergunta}
RESPOSTA:"""

NUMERO = re.compile(r"\d+(?:[.,]\d+)*\s*%?")
CITACAO = re.compile(r"[\[【]\d+(?:†[^\]】]*)?[\]】]")


def gerar(pergunta: str, recuperados: list, modelo_prompt: str) -> str:
    contexto = "\n\n".join(
        f"[{i + 1}] {c['texto']}" for i, (c, _) in enumerate(recuperados)
    )

    def _chamar():
        return groq.chat.completions.create(
            model=MODELO_LLM,
            messages=[
                {
                    "role": "user",
                    "content": modelo_prompt.format(
                        contexto=contexto, pergunta=pergunta
                    ),
                }
            ],
            max_completion_tokens=1500,
            reasoning_effort="low",
            temperature=0,
        )

    r = _com_retry(_chamar)
    return (r.choices[0].message.content or "").strip()


def margem(recuperados: list) -> float:
    return recuperados[0][1] - recuperados[-1][1]


def ancoragem(resposta: str, recuperados: list) -> tuple:
    """Verifica se cada número da resposta existe em algum trecho recuperado.

    Os marcadores [n] exigidos pela regra 5 do contrato não são dados do
    documento e ficam fora da conferência. O gpt-oss também os escreve como
    【n】 ou 【n†L1-L4】.
    """
    contexto = " ".join(normalizar(c["texto"]) for c, _ in recuperados)
    numeros = [n.strip() for n in NUMERO.findall(CITACAO.sub(" ", resposta))]
    orfaos = [n for n in numeros if normalizar(n) not in contexto]
    return len(numeros), orfaos


def responder_com_guarda(pergunta: str, recuperados: list, limiar: float) -> dict:
    """Pipeline protegido. Devolve a resposta e o motivo de eventual recusa."""
    if recuperados[0][1] < limiar:  # Guarda 1
        return {
            "resposta": RECUSA,
            "motivo": f"similaridade {recuperados[0][1]:.3f} abaixo do limiar {limiar}",
        }

    texto = gerar(  # Guarda 2
        pergunta, recuperados, PROMPT_COM_CONTRATO.replace("{recusa}", RECUSA)
    )
    if normalizar(RECUSA) in normalizar(texto):
        return {"resposta": RECUSA, "motivo": "o modelo declarou não encontrar"}

    _, orfaos = ancoragem(texto, recuperados)  # Guarda 3
    if orfaos:
        return {"resposta": RECUSA, "motivo": f"números sem lastro no contexto: {orfaos}"}
    return {"resposta": texto, "motivo": ""}


def classificar(p: dict, resposta: str) -> str:
    """Só critérios verificáveis por máquina; nas sem resposta, contrato ou texto livre."""
    r = plano(resposta)
    recusou = plano(RECUSA) in r
    if p["respondivel"]:
        if recusou:
            return "recusa indevida"
        return "acerto" if any(plano(c) in r for c in p["chaves"]) else "erro"
    return "recusa no contrato" if recusou else "resposta livre"


def calibrar(com: list[float], sem: list[float]) -> float:
    """Maior limiar (em centésimos) que não corta nenhuma pergunta respondível."""
    return math.floor(min(com) * 100) / 100


def resumo(valores: list[float]) -> str:
    ordenados = sorted(valores)
    return (
        f"mínimo {ordenados[0]:.3f} | mediana {ordenados[len(ordenados) // 2]:.3f} "
        f"| máximo {ordenados[-1]:.3f}"
    )


def main() -> None:
    secoes = carregar_secoes()
    chunks = chunkar_acervo([secoes[i] for i in IDS_ACERVO], ESTRATEGIAS[ESTRATEGIA])
    matriz = embutir([c["texto"] for c in chunks], "RETRIEVAL_DOCUMENT")

    perguntas = json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8"))[
        "perguntas"
    ]
    for p in perguntas:
        p["respondivel"] = bool(p.get("no_acervo"))
    vetores = embutir([p["pergunta"] for p in perguntas], "QUESTION_ANSWERING")
    recuperacoes = [recuperar(v, matriz, chunks) for v in vetores]

    print(
        f"Acervo: {len(IDS_ACERVO)} subseções, {len(chunks)} chunks ({ESTRATEGIA}), "
        f"embedding {MODELO_EMBEDDING}, chat {MODELO_LLM}\n"
    )

    # ---------- Calibração do limiar ---------------------------------
    print("Similaridade do primeiro trecho recuperado\n")
    com = [r[0][1] for p, r in zip(perguntas, recuperacoes) if p["respondivel"]]
    sem = [r[0][1] for p, r in zip(perguntas, recuperacoes) if not p["respondivel"]]
    print(f"  perguntas com resposta no acervo ({len(com)}): {resumo(com)}")
    print(f"  perguntas sem resposta no acervo ({len(sem)}): {resumo(sem)}")

    todos = com + sem
    inicio = math.floor(min(todos) * 20) / 20
    fim = math.ceil(max(todos) * 20) / 20
    grade = [round(inicio + 0.05 * i, 2) for i in range(int(round((fim - inicio) / 0.05)) + 1)]
    tabela_corte = []
    print("\n  limiar   corta perguntas respondíveis   corta perguntas sem resposta")
    for limiar in grade:
        c_com = sum(1 for s in com if s < limiar)
        c_sem = sum(1 for s in sem if s < limiar)
        tabela_corte.append({"limiar": limiar, "corta_com": c_com, "corta_sem": c_sem})
        print(f"   {limiar:.2f}{c_com:>26}{c_sem:>32}")

    LIMIAR = calibrar(com, sem)
    print(
        f"\nLimiar adotado: {LIMIAR:.2f} (maior valor que não corta pergunta "
        f"respondível; corta {sum(1 for s in sem if s < LIMIAR)} de {len(sem)} "
        f"sem resposta).\n"
    )

    # ---------- Comparação: ingênuo x protegido ----------------------
    vereditos = ["acerto", "erro", "recusa indevida", "recusa no contrato", "resposta livre"]
    placar = {"ingênuo": dict.fromkeys(vereditos, 0), "protegido": dict.fromkeys(vereditos, 0)}
    sem_lastro = {"ingênuo": 0, "protegido": 0}
    detalhes = []
    for p, rec in zip(perguntas, recuperacoes):
        bruto = gerar(p["pergunta"], rec, PROMPT_INGENUO)
        guardado = responder_com_guarda(p["pergunta"], rec, LIMIAR)
        linha = {
            "id": p["id"],
            "pergunta": p["pergunta"],
            "respondivel": p["respondivel"],
            "tipo": p.get("tipo"),
            "documento": p.get("documento"),
            "similaridade_top1": round(rec[0][1], 4),
            "margem": round(margem(rec), 4),
            "trechos": [
                {"origem": c["origem"], "indice": c["indice"], "similaridade": round(s, 4)}
                for c, s in rec
            ],
            "gabarito_no_contexto": bool(p.get("trecho_gabarito"))
            and plano(p["trecho_gabarito"]) in plano(" ".join(c["texto"] for c, _ in rec)),
        }
        for nome, texto in [("ingênuo", bruto), ("protegido", guardado["resposta"])]:
            v = classificar(p, texto)
            placar[nome][v] += 1
            total, orfaos = ancoragem(texto, rec)
            if orfaos:
                sem_lastro[nome] += 1
            linha[nome] = {"resposta": texto, "veredito": v, "numeros": total, "orfaos": orfaos}
        linha["protegido"]["motivo"] = guardado["motivo"]
        detalhes.append(linha)

        if not p["respondivel"]:
            print(f"P{p['id']}: {p['pergunta']}")
            print(f"   ingênuo   → {bruto[:110]}")
            print(
                f"   protegido → {guardado['resposta'][:60]}"
                f"{'  (' + guardado['motivo'] + ')' if guardado['motivo'] else ''}\n"
            )
        elif linha["protegido"]["veredito"] != "acerto":
            print(
                f"P{p['id']} tinha resposta no acervo e o protegido deu "
                f"'{linha['protegido']['veredito']}': {guardado['motivo'] or guardado['resposta'][:100]}\n"
            )

    print(f"\n{'Veredito':<20}{'Ingênuo':>10}{'Protegido':>12}")
    print("-" * 42)
    for v in vereditos:
        print(f"{v:<20}{placar['ingênuo'][v]:>10}{placar['protegido'][v]:>12}")
    print(f"{'com nº sem lastro':<20}{sem_lastro['ingênuo']:>10}{sem_lastro['protegido']:>12}")

    saida = PASTA / "data" / "resultado_protegido.json"
    saida.write_text(
        json.dumps(
            {
                "modelo_embedding": MODELO_EMBEDDING,
                "modelo_llm": MODELO_LLM,
                "estrategia": ESTRATEGIA,
                "limiar": LIMIAR,
                "calibracao": {
                    "com_resposta": sorted(round(s, 4) for s in com),
                    "sem_resposta": sorted(round(s, 4) for s in sem),
                    "tabela_corte": tabela_corte,
                },
                "placar": placar,
                "sem_lastro": sem_lastro,
                "perguntas": detalhes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResultados gravados em {saida}")


if __name__ == "__main__":
    main()
