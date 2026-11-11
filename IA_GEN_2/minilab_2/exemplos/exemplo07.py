# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 07: A mesma cadeia com outro fornecedor (ilustrativo)
# Seção 2.5 – Trocar de fornecedor sem reescrever a aplicação
# Requisitos: pip install langchain langchain-anthropic python-dotenv
# ============================================================
"""Exemplo ILUSTRATIVO: a mesma cadeia servida pela Anthropic.

> Este arquivo não é executado na preparação da aula, porque o curso não
> mantém chave da Anthropic. O código foi escrito conforme a documentação
> atual do provedor e serve para evidenciar quanto da aplicação permanece
> igual ao trocar de fornecedor. O aluno que tiver chave própria pode
> executá-lo; nenhuma etapa do Mini LAB depende dele.

O ponto pedagógico é a extensão da mudança. Comparando com o `exemplo03.py`,
apenas a linha que constrói o modelo é diferente: o template, a composição
com o operador de barra vertical e o esquema Pydantic permanecem idênticos.
É essa portabilidade que justifica a dependência do framework, e ela é
mensurável em número de linhas alteradas.
"""
import os
from typing import Literal, Optional

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

INSTRUCAO = ("Extraia do documento: numero, data (AAAA-MM-DD), valor (número ou null), "
             "partes (lista), objeto e prioridade (alta, media ou baixa).")
DOCUMENTO = ("OFÍCIO Nº OF-SEPLAG-2026-0142, de 15 de março de 2026, da Secretaria de "
             "Planejamento para a Prefeitura de Sinop, sobre repasse de R$ 125.000,00 "
             "para modernização tecnológica. Alta prioridade.")


class Documento(BaseModel):
    numero: str
    data: str
    valor: Optional[float]
    partes: list[str]
    objeto: str
    prioridade: Literal["alta", "media", "baixa"]


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "Exemplo ilustrativo: defina ANTHROPIC_API_KEY para executá-lo.\n"
            "O curso não mantém essa chave, e nenhuma etapa do Mini LAB depende deste arquivo."
        )

    # A ÚNICA linha diferente em relação ao exemplo03.py. O restante é idêntico.
    modelo = init_chat_model("claude-haiku-4-5", model_provider="anthropic")

    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{d}")])
    resultado = (prompt | modelo.with_structured_output(Documento)).invoke({"d": DOCUMENTO})
    print(resultado.model_dump())


if __name__ == "__main__":
    main()
