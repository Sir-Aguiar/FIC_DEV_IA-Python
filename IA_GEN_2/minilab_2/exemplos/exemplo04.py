# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: O framework compensa? Três implementações medidas
# Seção 6 – O framework compensa? Uma medição contra o SDK cru
# Requisitos: pip install langchain langchain-openai openai python-dotenv
# ============================================================
"""Extrai seis campos de vinte documentos administrativos por três caminhos.

O primeiro caminho usa o SDK da OpenAI diretamente, sem framework algum. O
segundo usa o LangChain com um parser que lê o JSON do texto da resposta. O
terceiro usa o LangChain com `with_structured_output`, que declara o esquema
à API. Os três recebem exatamente o mesmo prompt e o mesmo modelo, de modo
que a única variável é a forma de obter a saída estruturada.

A medição responde a uma pergunta que costuma ser respondida por convicção:
o que o framework de fato entrega em troca da dependência que ele acrescenta
ao projeto.
"""
import json
import os
import pathlib
import time
from difflib import SequenceMatcher
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI
from pydantic import BaseModel, Field

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = "gpt-5.6-luna"
# Preço por milhão de tokens na faixa de contexto curto, conforme a página
# oficial de preços da OpenAI. Serve para converter a medição em reais.
USD_ENTRADA, USD_SAIDA = 0.20, 1.20

INSTRUCAO = (
    "Você extrai dados de documentos administrativos do Estado de Mato Grosso. "
    "Extraia exatamente seis campos do documento: numero (o identificador do "
    "documento), data (no formato AAAA-MM-DD), valor (número em reais, ou null "
    "quando o documento não menciona valor), partes (lista com os dois órgãos "
    "ou entidades envolvidos, na ordem remetente e destinatário), objeto (o "
    "assunto do documento em uma frase) e prioridade (alta, media ou baixa). "
    "Responda apenas com o JSON, sem texto antes ou depois."
)


class Documento(BaseModel):
    """Os seis campos que o experimento extrai de cada documento."""

    numero: str = Field(description="Identificador do documento")
    data: str = Field(description="Data no formato AAAA-MM-DD")
    valor: Optional[float] = Field(description="Valor em reais, ou null")
    partes: list[str] = Field(description="Remetente e destinatário")
    objeto: str = Field(description="Assunto em uma frase")
    prioridade: Literal["alta", "media", "baixa"]


ESQUEMA_JSON = {
    "type": "object",
    "properties": {
        "numero": {"type": "string"},
        "data": {"type": "string"},
        "valor": {"type": ["number", "null"]},
        "partes": {"type": "array", "items": {"type": "string"}},
        "objeto": {"type": "string"},
        "prioridade": {"type": "string", "enum": ["alta", "media", "baixa"]},
    },
    "required": ["numero", "data", "valor", "partes", "objeto", "prioridade"],
    "additionalProperties": False,
}


def carregar() -> list[dict]:
    """Lê o conjunto de avaliação gerado por `gerar_documentos.py`."""
    caminho = pathlib.Path(__file__).parent / "documentos_2026.jsonl"
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo if linha.strip()]


def campo_correto(nome: str, obtido, esperado) -> bool:
    """Compara um campo extraído com o gabarito, campo a campo.

    A comparação é exata para número, data, valor e prioridade. Para as partes
    a ordem é ignorada, porque remetente e destinatário são identificáveis de
    qualquer maneira. Para o objeto, que é texto livre, aceita-se similaridade
    de 60% ou mais, limiar escolhido por ser o menor valor que não aceita uma
    frase de assunto diferente.
    """
    if obtido is None and esperado is None:
        return True
    if nome == "valor":
        if esperado is None:
            return obtido is None
        return obtido is not None and abs(float(obtido) - float(esperado)) < 0.01
    if nome == "partes":
        if not isinstance(obtido, list):
            return False
        norm = lambda xs: {str(x).strip().lower() for x in xs}
        return norm(obtido) == norm(esperado)
    if nome == "objeto":
        if not isinstance(obtido, str):
            return False
        return SequenceMatcher(None, obtido.strip().lower(), esperado.strip().lower()).ratio() >= 0.60
    return str(obtido).strip().lower() == str(esperado).strip().lower()


def conferir(extraido: Optional[dict], gabarito: dict) -> int:
    """Conta quantos dos seis campos saíram corretos."""
    if not extraido:
        return 0
    return sum(campo_correto(nome, extraido.get(nome), gabarito[nome]) for nome in gabarito)


# ---------------------------------------------------------------
# Caminho A — SDK da OpenAI, sem framework
# ---------------------------------------------------------------
def caminho_sdk(documentos: list[dict]) -> dict:
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    acertos = invalidos = entrada = saida = 0
    latencias = []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            resposta = cliente.chat.completions.create(
                model=MODELO,
                messages=[
                    {"role": "system", "content": INSTRUCAO},
                    {"role": "user", "content": doc["texto"]},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "documento", "schema": ESQUEMA_JSON, "strict": True},
                },
            )
            latencias.append(time.perf_counter() - inicio)
            entrada += resposta.usage.prompt_tokens
            saida += resposta.usage.completion_tokens
            extraido = json.loads(resposta.choices[0].message.content)
        except json.JSONDecodeError:
            invalidos += 1
            extraido = None
        except Exception as erro:  # falha de rede ou da API
            print(f"    falha em {doc['id']}: {type(erro).__name__}")
            invalidos += 1
            extraido = None
        acertos += conferir(extraido, doc["gabarito"])
    return montar("SDK openai puro", acertos, invalidos, entrada, saida, latencias)


# ---------------------------------------------------------------
# Caminho B — LangChain com parser de texto
# ---------------------------------------------------------------
def caminho_parser(documentos: list[dict]) -> dict:
    modelo = init_chat_model(MODELO, model_provider="openai")
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{documento}")])
    cadeia = prompt | modelo | JsonOutputParser()
    acertos = invalidos = entrada = saida = 0
    latencias = []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            extraido = cadeia.invoke({"documento": doc["texto"]})
            latencias.append(time.perf_counter() - inicio)
        except Exception as erro:
            # O parser levanta exceção quando a resposta não é JSON válido,
            # que é exatamente a falha que este caminho serve para expor.
            print(f"    JSON inválido em {doc['id']}: {type(erro).__name__}")
            invalidos += 1
            extraido = None
        acertos += conferir(extraido, doc["gabarito"])
    # O parser descarta o objeto de resposta, e com ele o `usage`. Recontamos
    # chamando o modelo sem o parser, o que já é um achado do experimento.
    entrada, saida = medir_tokens(prompt | modelo, documentos)
    return montar("LangChain + JsonOutputParser", acertos, invalidos, entrada, saida, latencias)


# ---------------------------------------------------------------
# Caminho C — LangChain com esquema declarado
# ---------------------------------------------------------------
def caminho_estruturado(documentos: list[dict]) -> dict:
    modelo = init_chat_model(MODELO, model_provider="openai")
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{documento}")])
    cadeia = prompt | modelo.with_structured_output(Documento, include_raw=True)
    acertos = invalidos = entrada = saida = 0
    latencias = []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            bruto = cadeia.invoke({"documento": doc["texto"]})
            latencias.append(time.perf_counter() - inicio)
            uso = bruto["raw"].usage_metadata or {}
            entrada += uso.get("input_tokens", 0)
            saida += uso.get("output_tokens", 0)
            if bruto["parsing_error"] is not None or bruto["parsed"] is None:
                invalidos += 1
                extraido = None
            else:
                extraido = bruto["parsed"].model_dump()
        except Exception as erro:
            print(f"    falha em {doc['id']}: {type(erro).__name__}")
            invalidos += 1
            extraido = None
        acertos += conferir(extraido, doc["gabarito"])
    return montar("LangChain + with_structured_output", acertos, invalidos, entrada, saida, latencias)


def medir_tokens(cadeia, documentos: list[dict]) -> tuple[int, int]:
    """Reexecuta a cadeia sem o parser, só para recuperar o consumo de tokens."""
    entrada = saida = 0
    for doc in documentos:
        try:
            resposta = cadeia.invoke({"documento": doc["texto"]})
            uso = resposta.usage_metadata or {}
            entrada += uso.get("input_tokens", 0)
            saida += uso.get("output_tokens", 0)
        except Exception:
            continue
    return entrada, saida


def montar(nome, acertos, invalidos, entrada, saida, latencias) -> dict:
    ordenadas = sorted(latencias)
    mediana = ordenadas[len(ordenadas) // 2] if ordenadas else 0.0
    custo = entrada / 1_000_000 * USD_ENTRADA + saida / 1_000_000 * USD_SAIDA
    return {
        "nome": nome,
        "acertos": acertos,
        "invalidos": invalidos,
        "entrada": entrada,
        "saida": saida,
        "latencia": mediana,
        "custo": custo,
    }


def main() -> None:
    documentos = carregar()
    total_campos = len(documentos) * 6
    print(f"Conjunto: {len(documentos)} documentos, {total_campos} campos a extrair")
    print(f"Modelo: {MODELO}\n")

    resultados = []
    for rotulo, funcao in (
        ("A", caminho_sdk),
        ("B", caminho_parser),
        ("C", caminho_estruturado),
    ):
        print(f"[{rotulo}] executando...")
        resultados.append(funcao(documentos))

    print(f"\n{'Implementação':34} {'Campos':>10} {'Inválidos':>10} "
          f"{'Entrada':>9} {'Saída':>8} {'Latência':>10} {'US$':>9}")
    print("-" * 96)
    for r in resultados:
        print(f"{r['nome']:34} {r['acertos']:>4}/{total_campos:<5} {r['invalidos']:>10} "
              f"{r['entrada']:>9} {r['saida']:>8} {r['latencia']:>9.2f}s {r['custo']:>9.5f}")

    destino = pathlib.Path(__file__).parent / "resultado_experimento.json"
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados gravados em {destino.name}")


if __name__ == "__main__":
    main()
