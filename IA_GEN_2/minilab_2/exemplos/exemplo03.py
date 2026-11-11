# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: Parser de texto contra esquema declarado
# Seção 5 – Saída estruturada: with_structured_output contra parser de texto
# Requisitos: pip install langchain langchain-openai openai python-dotenv
# ============================================================
"""As três implementações mínimas da mesma extração, lado a lado.

Cada bloco abaixo é a versão mais curta que resolve o problema por um caminho
diferente, sem instrumentação e sem tratamento de erro. Servem para comparar
o que cada abordagem custa em linhas de código e, principalmente, para ver o
que muda quando se precisa trocar de provedor — que é a pergunta prática de
quem mantém o sistema depois.
"""
import json
import os
import pathlib
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI
from pydantic import BaseModel

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = "gpt-5.6-luna"
INSTRUCAO = ("Extraia do documento: numero, data (AAAA-MM-DD), valor (número ou null), "
             "partes (lista), objeto e prioridade (alta, media ou baixa). Só o JSON.")
DOCUMENTO = ("OFÍCIO Nº OF-SEPLAG-2026-0142\nCuiabá, 15 de março de 2026.\n"
             "De: Secretaria de Estado de Planejamento e Gestão\nPara: Prefeitura de Sinop\n"
             "Assunto: Repasse de R$ 125.000,00 para modernização tecnológica. "
             "Prazo até 30 de março, matéria de alta prioridade.")


class Documento(BaseModel):
    numero: str
    data: str
    valor: Optional[float]
    partes: list[str]
    objeto: str
    prioridade: Literal["alta", "media", "baixa"]


# --- Caminho A: SDK da OpenAI, sem framework ------------------------
def com_sdk() -> dict:
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=[{"role": "system", "content": INSTRUCAO},
                  {"role": "user", "content": DOCUMENTO}],
        response_format={"type": "json_schema", "json_schema": {
            "name": "documento", "strict": True,
            "schema": {**Documento.model_json_schema(), "additionalProperties": False}}},
    )
    return json.loads(resposta.choices[0].message.content)


# --- Caminho B: LangChain com parser de texto -----------------------
def com_parser() -> dict:
    modelo = init_chat_model(MODELO, model_provider="openai")
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{d}")])
    return (prompt | modelo | JsonOutputParser()).invoke({"d": DOCUMENTO})


# --- Caminho C: LangChain com esquema declarado ---------------------
def com_esquema() -> dict:
    modelo = init_chat_model(MODELO, model_provider="openai")
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{d}")])
    return (prompt | modelo.with_structured_output(Documento)).invoke({"d": DOCUMENTO}).model_dump()


# --- O que muda para trocar de provedor -----------------------------
def com_esquema_no_groq() -> dict:
    """Idêntico ao caminho C, com uma única linha trocada — a do modelo.

    O `timeout` e o `max_retries` não fazem parte da troca de provedor: são
    proteção. O padrão do LangChain repete a chamada várias vezes quando o
    provedor demora, e o script parece travado em vez de acusar o atraso.
    """
    modelo = init_chat_model("openai/gpt-oss-20b", model_provider="groq",
                             timeout=45, max_retries=0)
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{d}")])
    return (prompt | modelo.with_structured_output(Documento)).invoke({"d": DOCUMENTO}).model_dump()


def main() -> None:
    for rotulo, funcao in (("A · SDK openai", com_sdk),
                           ("B · parser de texto", com_parser),
                           ("C · esquema declarado", com_esquema),
                           ("C' · o mesmo no Groq", com_esquema_no_groq)):
        try:
            saida = funcao()
            print(f"\n{rotulo}")
            print(f"   numero={saida.get('numero')!r}  valor={saida.get('valor')!r}  "
                  f"prioridade={saida.get('prioridade')!r}")
            print(f"   chaves: {sorted(saida.keys())}")
        except Exception as erro:
            print(f"\n{rotulo}: {type(erro).__name__} — {str(erro)[:110]}")


if __name__ == "__main__":
    main()
