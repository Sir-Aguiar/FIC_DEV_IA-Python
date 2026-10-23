# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Auditoria de fundamentação do assistente
# Seção 6 – Auditoria: Como Saber se o Assistente Está Fundamentado
# Requisitos: pip install openai chromadb pymupdf python-dotenv
# Execução: python exemplo03.py edital_exemplo.pdf
# ============================================================
"""Verifica se o assistente responde apenas quando o acervo permite.

A bateria abaixo mistura perguntas cuja resposta está no edital com
perguntas cuja resposta não está. Um assistente confiável acerta os
dois casos: responde as primeiras citando a página correta e recusa as
segundas. Responder às segundas é o defeito mais grave possível, pois
produz informação plausível e falsa sobre um documento oficial.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from exemplo02 import AssistenteDocumentos

# Páginas = número no arquivo PDF (não o número impresso no Diário Oficial).
# (pergunta, deve_responder, página esperada quando houver resposta)
BATERIA: List[tuple] = [
    ("Há cobrança de taxa de inscrição no processo seletivo da MTI?", True, 1),
    ("Qual a remuneração do perfil Analista de TI - Gerente de Projeto?", True, 2),
    ("Qual o percentual de vagas reservadas às pessoas com deficiência?", True, 3),
    ("Qual o período de inscrições previsto no cronograma do edital?", True, 4),
    ("O exame admissional é obrigatório na contratação?", True, 5),
    (
        "Qual a multa aplicada se o contratado não cumprir o aviso prévio de 30 dias?",
        True,
        27,
    ),
    (
        "A Gerência de Aquisições realiza procedimentos licitatórios de quais modalidades?",
        True,
        10,
    ),
    ("Qual o capital social mínimo exigido para participar do certame?", False, None),
    ("Quem é o pregoeiro responsável pela sessão pública?", False, None),
    ("Qual a alíquota do IPVA em Mato Grosso em 2026?", False, None),
]

DOCUMENTOS_PADRAO = [
    "processo_seletivo_mti.pdf",
    "regimento_interno_mti.pdf",
]


def paginas_citadas(resposta: str) -> List[int]:
    """Extrai os números de página citados no formato (documento, p. X)."""
    return [int(n) for n in re.findall(r"p\.\s*(\d+)", resposta)]


def avaliar(assistente: AssistenteDocumentos) -> List[Dict]:
    linhas = []

    for pergunta, deve_responder, pagina_esperada in BATERIA:
        resultado = assistente.responder(pergunta)
        respondeu = resultado["fundamentada"]
        citadas = paginas_citadas(resultado["resposta"])

        if not deve_responder:
            situacao = "OK (recusou)" if not respondeu else "FALHA (inventou)"
        elif not respondeu:
            situacao = "FALHA (recusou o que existe)"
        elif pagina_esperada in citadas:
            situacao = "OK (citou a página certa)"
        elif citadas:
            situacao = f"ATENÇÃO (citou p. {citadas}, esperada {pagina_esperada})"
        else:
            situacao = "ATENÇÃO (respondeu sem citar página)"

        linhas.append(
            {
                "pergunta": pergunta,
                "esperado": "responder" if deve_responder else "recusar",
                "obtido": "respondeu" if respondeu else "recusou",
                "pagina_esperada": pagina_esperada,
                "pagina_citada": citadas,
                "paginas": citadas,
                "situacao": situacao,
                "resposta": resultado["resposta"],
            }
        )

    return linhas


def _pasta_data() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _parse_args() -> tuple:
    """Aceita PDFs e um limiar opcional no intervalo (0, 1)."""
    limiar = 0.45
    caminhos: List[str] = []
    for argumento in sys.argv[1:]:
        try:
            valor = float(argumento)
        except ValueError:
            caminhos.append(argumento)
            continue
        if 0 < valor < 1:
            limiar = valor
        else:
            caminhos.append(argumento)
    if not caminhos:
        caminhos = [str(_pasta_data() / nome) for nome in DOCUMENTOS_PADRAO]
    return caminhos, limiar


def _fmt_pagina(valor: Optional[int] | List[int]) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, list):
        return ", ".join(str(n) for n in valor) if valor else "—"
    return str(valor)


def main() -> None:
    caminhos, limiar = _parse_args()

    assistente = AssistenteDocumentos(
        similaridade_minima=limiar,
        arquivo_auditoria="auditoria.jsonl",
    )
    for caminho in caminhos:
        info = assistente.carregar_documento(caminho)
        print(f"Acervo: {info['nome']} ({info['total_trechos']} trechos)")
    print(f"Limiar de similaridade: {limiar}\n")

    linhas = avaliar(assistente)

    print(
        f"{'Pergunta':<58} {'Esperado':<10} {'Obtido':<10} "
        f"{'Pág. esp.':<10} {'Pág. citada':<12} Situação"
    )
    print("-" * 130)
    for linha in linhas:
        print(
            f"{linha['pergunta'][:56]:<58} "
            f"{linha['esperado']:<10} {linha['obtido']:<10} "
            f"{_fmt_pagina(linha['pagina_esperada']):<10} "
            f"{_fmt_pagina(linha['pagina_citada']):<12} "
            f"{linha['situacao']}"
        )

    falhas = [linha for linha in linhas if linha["situacao"].startswith("FALHA")]
    legitimas_recusadas = [
        linha
        for linha in linhas
        if linha["esperado"] == "responder" and linha["obtido"] == "recusou"
    ]
    print(f"\n{len(linhas) - len(falhas)} de {len(linhas)} comportamentos corretos.")
    print(f"Perguntas legítimas recusadas: {len(legitimas_recusadas)}.")
    if falhas:
        print("Falhas encontradas — o assistente não está pronto para uso real.")


if __name__ == "__main__":
    main()
