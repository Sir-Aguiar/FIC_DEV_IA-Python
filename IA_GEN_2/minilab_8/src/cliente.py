import json
from pathlib import Path

import httpx

from src.configuracao import (
    CHAVE_LANGFLOW,
    TEMPO_LIMITE_SEGUNDOS,
    URL_LANGFLOW,
)


def abrir_cliente() -> httpx.Client:
    # O cabeçalho x-api-key é o da Seção 7.2. Sem a chave, o servidor recusa a chamada.
    cabecalhos = {"x-api-key": CHAVE_LANGFLOW} if CHAVE_LANGFLOW else {}
    return httpx.Client(
        base_url=f"{URL_LANGFLOW}/api/v1",
        headers=cabecalhos,
        timeout=TEMPO_LIMITE_SEGUNDOS,
    )


def listar() -> list[dict]:
    # GET /flows/ devolve o que está no servidor, inclusive o grafo exportável.
    with abrir_cliente() as cliente:
        resposta = cliente.get("/flows/", params={"get_all": "true", "remove_example_flows": "false"})
        resposta.raise_for_status()
        corpo = resposta.json()

    if isinstance(corpo, dict):
        return corpo.get("flows") or corpo.get("items") or []
    return corpo


def localizar(nome: str) -> dict:
    # Várias importações do mesmo nome deixam cópias. A mais recente é a da tela.
    encontrados = [fluxo for fluxo in listar() if fluxo.get("name") == nome]
    if not encontrados:
        raise LookupError(f"Fluxo não encontrado no servidor: {nome}")
    return max(encontrados, key=lambda fluxo: fluxo.get("updated_at") or "")


def importar(caminho: Path) -> dict:
    # O id do banco local não viaja: o servidor atribui outro ao receber o JSON do setor.
    corpo = json.loads(Path(caminho).read_text())
    corpo.pop("id", None)
    with abrir_cliente() as cliente:
        resposta = cliente.post("/flows/", json=corpo)
        resposta.raise_for_status()
        return resposta.json()


def rodar(nome: str, mensagem: str) -> str:
    # Parte 5: a mesma chamada da Seção 7.2, com a mensagem no lugar de input_value.
    # O classificador não tem Message History, então cada chamada não herda a anterior.
    fluxo = localizar(nome)
    corpo = {"input_value": mensagem, "input_type": "chat", "output_type": "chat"}
    with abrir_cliente() as cliente:
        resposta = cliente.post(f"/run/{fluxo['id']}", params={"stream": "false"}, json=corpo)
        resposta.raise_for_status()
        mensagem_saida = resposta.json()["outputs"][0]["outputs"][0]["results"]["message"]

    texto = mensagem_saida.get("text") if isinstance(mensagem_saida, dict) else None
    if not texto and isinstance(mensagem_saida, dict):
        texto = (mensagem_saida.get("data") or {}).get("text")
    return texto or ""


def apagar(nome: str) -> dict:
    fluxo = localizar(nome)
    with abrir_cliente() as cliente:
        resposta = cliente.delete(f"/flows/{fluxo['id']}")
        resposta.raise_for_status()
        if resposta.content:
            return resposta.json()
    return fluxo
