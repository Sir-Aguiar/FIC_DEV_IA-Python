import os
from pathlib import Path

from dotenv import load_dotenv

# A raiz é a pasta do minilab, dois níveis acima deste módulo.
RAIZ = Path(__file__).resolve().parents[1]

# O .env da pasta do projeto traz LANGFLOW_URL e LANGFLOW_API_KEY.
# A chave da OpenAI não é lida aqui: ela fica no processo que inicia o servidor.
load_dotenv(RAIZ / ".env")


def _limpar(valor: str | None, padrao: str = "") -> str:
    # O arquivo guarda alguns valores entre aspas; a chamada HTTP precisa do texto cru.
    if valor is None:
        return padrao
    return valor.strip().strip('"')


# Parte 5: o cliente fala com o LangFlow local, salvo quando LANGFLOW_URL aponta outro servidor.
URL_LANGFLOW = _limpar(os.environ.get("LANGFLOW_URL"), "http://127.0.0.1:7860").rstrip("/")

# A chave x-api-key autoriza este programa a usar o servidor. Não é a chave do modelo.
CHAVE_LANGFLOW = _limpar(os.environ.get("LANGFLOW_API_KEY"))

# O mesmo limite da Seção 7.2. O classificador responde rápido; o cliente também serve ao agente.
TEMPO_LIMITE_SEGUNDOS = 240

PASTA_FLUXOS = RAIZ / "fluxos"
PASTA_DADOS = RAIZ / "dados"
PASTA_RESULTADOS = RAIZ / "resultados"

# Nome com que o fluxo foi gravado na tela e no JSON exportado.
NOME_CLASSIFICADOR = "Classificador TI MTI"
