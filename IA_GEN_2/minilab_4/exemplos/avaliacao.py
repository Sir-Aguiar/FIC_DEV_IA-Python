# ============================================================
# Aula 04 – Introdução ao CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Apoio: rubrica objetiva e juiz automático usados no experimento
# Seção 5 – A backstory paga o que promete? Um experimento
# Requisitos: pip install openai python-dotenv pydantic
# ============================================================
"""Avalia um parecer por dois caminhos independentes: regra e juiz automático.

A rubrica aplica seis verificações objetivas sobre o texto, sem modelo de
linguagem envolvido, e por isso é reproduzível. O juiz automático usa um
modelo superior para julgar fidelidade e utilidade, dimensões que nenhuma
regra alcança. Os dois são necessários e nenhum basta sozinho: a regra não
percebe um parecer bem escrito e vazio, e o juiz não é determinístico.
"""
import json
import os
import pathlib
import re
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

BASE = pathlib.Path(__file__).parent
RUBRICA = json.loads((BASE / "rubrica.json").read_text(encoding="utf-8"))["itens"]

MODELO_JUIZ = "gpt-5.6-terra"


def _normalizar(texto: str) -> str:
    return texto.lower().replace(".", "").replace(",", "").replace("**", "")


def aplicar_rubrica(parecer: str) -> tuple[int, list[str]]:
    """Aplica os seis itens da rubrica e devolve a nota e os itens perdidos."""
    texto, perdidos = _normalizar(parecer), []
    for item in RUBRICA:
        ok = any(_normalizar(a) in texto for a in item["alvos"])
        if not ok:
            perdidos.append(item["id"])
    return len(RUBRICA) - len(perdidos), perdidos


# A rubrica não tenta detectar número inventado, e a omissão é deliberada.
# Um parecer correto sobre este dossiê cita 470.000, diferença entre o valor
# estimado e a dotação; 897.600, que é a manutenção anual multiplicada pelos
# quatro anos de vigência; e 13.709, que é o número da LGPD. Nenhum deles está
# no dossiê e todos são legítimos. Distinguir cálculo correto e referência
# normativa de valor inventado exige interpretação, e por isso a fidelidade
# fica a cargo do juiz automático, que é a dimensão que nenhuma regra alcança.


class Julgamento(BaseModel):
    """O veredito do juiz automático sobre um parecer."""

    fidelidade: Literal[1, 2, 3, 4, 5] = Field(
        description="5 se toda afirmação se apoia no dossiê; 1 se há invenção relevante")
    utilidade: Literal[1, 2, 3, 4, 5] = Field(
        description="5 se o gestor decidiria com base nele; 1 se é genérico")
    justificativa: str = Field(description="Uma frase explicando as duas notas")


def julgar(parecer: str, dossie: str) -> Julgamento:
    """Pede a um modelo superior que julgue fidelidade e utilidade."""
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resposta = cliente.chat.completions.parse(
        model=MODELO_JUIZ,
        messages=[
            {"role": "system", "content":
             "Você avalia pareceres técnicos da administração pública estadual. "
             "Julgue apenas o parecer apresentado, comparando-o com o dossiê. "
             "Fidelidade mede se as afirmações se apoiam no dossiê. Utilidade "
             "mede se um gestor conseguiria decidir a partir dele."},
            {"role": "user", "content": f"DOSSIÊ:\n{dossie}\n\nPARECER:\n{parecer}"},
        ],
        response_format=Julgamento,
    )
    return resposta.choices[0].message.parsed


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(BASE.parents[2] / ".env")
    exemplo = ("Analisado o processo, o valor estimado de R$ 1.870.000,00 supera a "
               "dotação de R$ 1.400.000,00 do exercício. Falta o estudo técnico "
               "preliminar exigido pela Lei nº 14.133/2021. O prazo de implantação "
               "de 14 meses ultrapassa o limite de empenho de 30 de novembro. "
               "Recomenda-se o sobrestamento até a conclusão do estudo.")
    nota, perdidos = aplicar_rubrica(exemplo)
    print(f"rubrica: {nota}/6  itens perdidos: {perdidos or 'nenhum'}")
