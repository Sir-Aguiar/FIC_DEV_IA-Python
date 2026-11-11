"""Medição do minilab 2 na OpenAI, provedor de referência do curso."""

import json
import os
import pathlib
import re
import time
from difflib import SequenceMatcher
from typing import Literal, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env", override=True)

MODELO = "gpt-5.6-luna"
MODELO_TROCA = "gpt-5.6-sol"
# Preço por milhão de tokens usado no exemplo 04 da aula para o gpt-5.6-luna.
USD_ENTRADA, USD_SAIDA = 0.20, 1.20
CAMPOS = ("numero", "data", "valor", "solicitante", "objeto", "prioridade")

INSTRUCAO = (
    "Você extrai dados de documentos da Gerência de Tecnologia da Informação "
    "da Secretaria de Estado de Fazenda. Extraia exatamente seis campos: "
    "numero (identificador do documento), data (AAAA-MM-DD; converta data por "
    "extenso), valor (número em reais, ou null quando o documento não menciona "
    "valor; converta valor por extenso), solicitante (órgão ou unidade de "
    "destino, o Para), objeto (o assunto em uma frase) e prioridade "
    "(alta, media ou baixa). Responda apenas com o JSON, sem texto antes ou depois."
)


class Documento(BaseModel):
    numero: str = Field(description="Identificador do documento")
    data: str = Field(description="Data no formato AAAA-MM-DD")
    valor: Optional[float] = Field(description="Valor em reais, ou null")
    solicitante: str = Field(description="Unidade de destino, o Para")
    objeto: str = Field(description="Assunto em uma frase")
    prioridade: Literal["alta", "media", "baixa"]


ESQUEMA_JSON = {
    "type": "object",
    "properties": {
        "numero": {"type": "string"},
        "data": {"type": "string"},
        "valor": {"type": ["number", "null"]},
        "solicitante": {"type": "string"},
        "objeto": {"type": "string"},
        "prioridade": {"type": "string", "enum": ["alta", "media", "baixa"]},
    },
    "required": list(CAMPOS),
    "additionalProperties": False,
}


def carregar() -> list[dict]:
    caminho = pathlib.Path(__file__).parent / "documentos.jsonl"
    with caminho.open(encoding="utf-8") as arquivo:
        return [json.loads(linha) for linha in arquivo if linha.strip()]


def campo_correto(nome: str, obtido, esperado) -> bool:
    if obtido is None and esperado is None:
        return True
    if nome == "valor":
        if esperado is None:
            return obtido is None
        try:
            return obtido is not None and abs(float(obtido) - float(esperado)) < 0.01
        except (TypeError, ValueError):
            return False
    if nome == "objeto":
        if not isinstance(obtido, str) or not isinstance(esperado, str):
            return False
        return SequenceMatcher(None, obtido.strip().lower(), esperado.strip().lower()).ratio() >= 0.60
    return str(obtido).strip().lower() == str(esperado).strip().lower()


def conferir(extraido: Optional[dict], gabarito: dict) -> tuple[int, list[str]]:
    if not extraido:
        return 0, list(CAMPOS)
    falhas = [nome for nome in CAMPOS if not campo_correto(nome, extraido.get(nome), gabarito[nome])]
    return len(CAMPOS) - len(falhas), falhas


def montar(nome, acertos, invalidos, entrada, saida, latencias, falhas) -> dict:
    ordenadas = sorted(latencias)
    mediana = ordenadas[len(ordenadas) // 2] if ordenadas else 0.0
    custo = entrada / 1_000_000 * USD_ENTRADA + saida / 1_000_000 * USD_SAIDA
    return {
        "nome": nome,
        "acertos": acertos,
        "invalidos": invalidos,
        "entrada": entrada,
        "saida": saida,
        "latencia": round(mediana, 2),
        "custo": round(custo, 6),
        "falhas": falhas,
    }


def cliente_openai() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def tentar(acao):
    """Repete só limite de cota. Outros erros seguem para a contagem da medição."""
    for tentativa in range(8):
        try:
            return acao()
        except Exception as erro:
            texto = str(erro)
            if "429" not in texto and "rate_limit" not in texto.lower():
                raise
            encontrado = re.search(r"try again in ([0-9.]+)s", texto)
            espera = float(encontrado.group(1)) + 0.4 if encontrado else 8
            time.sleep(min(espera, 30))
            if tentativa == 7:
                raise


def uso_mensagem(resposta) -> tuple[int, int]:
    uso = resposta.usage_metadata or {}
    return uso.get("input_tokens", 0), uso.get("output_tokens", 0)


def caminho_sdk(documentos: list[dict], modelo: str = MODELO) -> dict:
    cliente = cliente_openai()
    tentar(lambda: cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": "ok"}],
        max_completion_tokens=16,
    ))
    acertos = invalidos = entrada = saida = 0
    latencias, falhas = [], []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            resposta = tentar(lambda doc=doc: cliente.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": INSTRUCAO},
                    {"role": "user", "content": doc["texto"]},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "documento", "schema": ESQUEMA_JSON, "strict": True},
                },
            ))
            latencias.append(time.perf_counter() - inicio)
            entrada += resposta.usage.prompt_tokens
            saida += resposta.usage.completion_tokens
            extraido = json.loads(resposta.choices[0].message.content)
        except json.JSONDecodeError:
            invalidos += 1
            extraido = None
        except Exception as erro:
            print(f"    falha SDK em {doc['id']}: {type(erro).__name__}: {str(erro)[:180]}", flush=True)
            invalidos += 1
            extraido = None
        pontos, erros = conferir(extraido, doc["gabarito"])
        acertos += pontos
        falhas.extend(f"{doc['id']}:{nome}" for nome in erros)
    return montar("SDK openai puro", acertos, invalidos, entrada, saida, latencias, falhas)


def caminho_parser(documentos: list[dict], modelo_id: str = MODELO) -> dict:
    modelo = init_chat_model(modelo_id, model_provider="openai", timeout=60, max_retries=0)
    tentar(lambda: modelo.invoke([HumanMessage("ok")]))
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{documento}")])
    gerar = prompt | modelo
    parser = JsonOutputParser()
    acertos = invalidos = entrada = saida = 0
    latencias, falhas = [], []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            resposta = tentar(lambda doc=doc: gerar.invoke({"documento": doc["texto"]}))
            latencias.append(time.perf_counter() - inicio)
            tokens_entrada, tokens_saida = uso_mensagem(resposta)
            entrada += tokens_entrada
            saida += tokens_saida
            extraido = parser.invoke(resposta)
        except Exception as erro:
            print(f"    JSON inválido em {doc['id']}: {type(erro).__name__}: {str(erro)[:180]}", flush=True)
            invalidos += 1
            extraido = None
        pontos, erros = conferir(extraido, doc["gabarito"])
        acertos += pontos
        falhas.extend(f"{doc['id']}:{nome}" for nome in erros)
    return montar("LangChain + JsonOutputParser", acertos, invalidos, entrada, saida, latencias, falhas)


def caminho_estruturado(documentos: list[dict], modelo_id: str = MODELO) -> dict:
    modelo = init_chat_model(modelo_id, model_provider="openai", timeout=60, max_retries=0)
    tentar(lambda: modelo.invoke([HumanMessage("ok")]))
    prompt = ChatPromptTemplate.from_messages([("system", INSTRUCAO), ("human", "{documento}")])
    cadeia = prompt | modelo.with_structured_output(Documento, include_raw=True)
    acertos = invalidos = entrada = saida = 0
    latencias, falhas = [], []
    for doc in documentos:
        inicio = time.perf_counter()
        try:
            bruto = tentar(lambda doc=doc: cadeia.invoke({"documento": doc["texto"]}))
            latencias.append(time.perf_counter() - inicio)
            tokens_entrada, tokens_saida = uso_mensagem(bruto["raw"])
            entrada += tokens_entrada
            saida += tokens_saida
            if bruto["parsing_error"] is not None or bruto["parsed"] is None:
                invalidos += 1
                extraido = None
            else:
                extraido = bruto["parsed"].model_dump()
        except Exception as erro:
            print(f"    falha esquema em {doc['id']}: {type(erro).__name__}: {str(erro)[:180]}", flush=True)
            invalidos += 1
            extraido = None
        pontos, erros = conferir(extraido, doc["gabarito"])
        acertos += pontos
        falhas.extend(f"{doc['id']}:{nome}" for nome in erros)
    return montar("LangChain + with_structured_output", acertos, invalidos, entrada, saida, latencias, falhas)


def comparar_destinos() -> list[dict]:
    pergunta = (
        "Em uma frase, qual a diferença entre dispensa e inexigibilidade "
        "de licitação na Lei nº 14.133/2021?"
    )
    mensagens = [
        SystemMessage("Você assessora servidores públicos. Responda de forma objetiva."),
        HumanMessage(pergunta),
    ]
    destinos = [
        ("OpenAI · gpt-5.6-luna", "gpt-5.6-luna", "openai", "OPENAI_API_KEY", {}),
        ("Groq · gpt-oss-20b", "openai/gpt-oss-20b", "groq", "GROQ_API_KEY",
         {"timeout": 45, "max_retries": 0}),
    ]
    saida = []
    for rotulo, identificador, provedor, variavel, extras in destinos:
        chave = os.getenv(variavel)
        if not chave:
            saida.append({"destino": rotulo, "status": f"{variavel} ausente"})
            continue
        try:
            modelo = init_chat_model(identificador, model_provider=provedor, api_key=chave, **extras)
            tentar(lambda: modelo.invoke([HumanMessage("ok")]))
            inicio = time.perf_counter()
            resposta = tentar(lambda: modelo.invoke(mensagens))
            decorrido = time.perf_counter() - inicio
            entrada, tokens_saida = uso_mensagem(resposta)
            saida.append({
                "destino": rotulo,
                "status": "ok",
                "segundos": round(decorrido, 2),
                "entrada": entrada,
                "saida": tokens_saida,
                "trecho": str(resposta.content).strip().replace("\n", " ")[:180],
            })
        except Exception as erro:
            saida.append({"destino": rotulo, "status": f"{type(erro).__name__}: {str(erro)[:180]}"})
    if not os.getenv("HF_TOKEN"):
        saida.append({"destino": "Hugging Face · gpt-oss-20b", "status": "HF_TOKEN ausente"})
    return saida


def parametros_descartados() -> dict:
    """O SDK recusa temperature e max_tokens. O LangChain reescreve um e descarta o outro."""
    cliente = cliente_openai()
    mensagens = [{"role": "user", "content": "Responda apenas: ok"}]
    sdk = []
    for rotulo, parametros in (
        ("temperature=0.3", {"temperature": 0.3}),
        ("max_tokens=500", {"max_tokens": 500}),
        ("max_completion_tokens=500", {"max_completion_tokens": 500}),
    ):
        try:
            cliente.chat.completions.create(model=MODELO, messages=mensagens, **parametros)
            sdk.append({"parametro": rotulo, "resultado": "aceito"})
        except Exception as erro:
            sdk.append({"parametro": rotulo, "resultado": f"{type(erro).__name__}: {str(erro)[:140]}"})
    modelo = init_chat_model(MODELO, model_provider="openai", temperature=0.3, max_tokens=500)
    enviados = {chave: valor for chave, valor in modelo._default_params.items() if chave != "stream"}
    return {
        "sdk": sdk,
        "enviado_pelo_langchain": enviados,
        "temperature_no_objeto": getattr(modelo, "temperature", None),
    }


def trocar_provedor(documentos: list[dict], vencedor: str) -> dict:
    """Repete o caminho vencedor. A única edição funcional é o identificador do modelo."""
    if vencedor.startswith("SDK"):
        resultado = caminho_sdk(documentos, MODELO_TROCA)
    elif "JsonOutputParser" in vencedor:
        resultado = caminho_parser(documentos, MODELO_TROCA)
    else:
        resultado = caminho_estruturado(documentos, MODELO_TROCA)
    resultado["destino"] = f"OpenAI · {MODELO_TROCA}"
    resultado["linhas_alteradas"] = 1
    resultado["preco_nao_recalculado"] = "a tabela principal permanece na tarifa do gpt-5.6-luna"
    return resultado


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY ausente no .env do minilab.")
    documentos = carregar()
    relatorio = {
        "modelo": MODELO,
        "provedor": "openai",
        "motivo_do_provedor": "GROQ_API_KEY e HF_TOKEN ausentes; as três implementações ficam na OpenAI.",
        "documentos": len(documentos),
        "campos": len(documentos) * len(CAMPOS),
        "preco_usd_por_milhao": {"entrada": USD_ENTRADA, "saida": USD_SAIDA},
        "destinos": comparar_destinos(),
        "parametros": parametros_descartados(),
    }
    resultados = []
    for rotulo, funcao in (
        ("A", caminho_sdk),
        ("B", caminho_parser),
        ("C", caminho_estruturado),
    ):
        print(f"[{rotulo}] executando...", flush=True)
        resultados.append(funcao(documentos))
        pathlib.Path(__file__).with_name("_parcial.json").write_text(
            json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    relatorio["resultados"] = resultados
    vencedor = max(resultados, key=lambda item: (item["acertos"], -item["custo"]))
    relatorio["vencedor"] = vencedor["nome"]
    print("[troca] executando...", flush=True)
    try:
        relatorio["troca"] = trocar_provedor(documentos, vencedor["nome"])
    except Exception as erro:
        relatorio["troca"] = {"status": f"{type(erro).__name__}: {str(erro)[:300]}", "linhas_alteradas": 1}
    print("RELATORIO_JSON")
    print(json.dumps(relatorio, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
