"""Critério de acerto do gabarito, definido antes de executar as doze consultas.

A Seção 5.2 mostra que uma comparação literal mede o critério, não o agente:
"7,0 h", "7 horas" e "sete horas" são a mesma resposta. Os dois lados, o
gabarito e a resposta, passam pela mesma normalização antes do confronto.
"""
import re
import unicodedata


# Horas que o gabarito cobra por extenso. A troca é de palavra inteira,
# para "sete" não alterar outra palavra que apenas comece assim.
EXTENSO = {"sete": "7", "quatro": "4", "uma": "1"}


def normalizar(texto: str) -> str:
    """Aproxima grafias equivalentes antes de comparar com o gabarito.

    A aula apaga ponto e vírgula de uma vez porque o gabarito de lá não tem
    decimal. Aqui "7,0" e "120.000" usam o mesmo sinal com sentidos diferentes,
    então o separador de milhar sai primeiro e o decimal zero só depois.
    """
    t = texto.lower().replace("**", "")
    sem_acento = unicodedata.normalize("NFKD", t)
    t = "".join(caractere for caractere in sem_acento if not unicodedata.combining(caractere))

    for palavra, algarismo in EXTENSO.items():
        t = re.sub(rf"\b{palavra}\b", algarismo, t)

    # "120 mil" e "120.000" precisam cair no mesmo número.
    t = re.sub(r"\b(\d+)\s*mil\b", lambda encontrado: str(int(encontrado.group(1)) * 1000), t)
    t = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", t)

    # "7,0" e "7.0" viram 7. "0,5" permanece 0.5, porque não é zero à toa.
    t = re.sub(r"(?<=\d),(?=\d)", ".", t)

    def sem_zero_decimal(encontrado: re.Match) -> str:
        numero = float(encontrado.group(0))
        if numero == int(numero):
            return str(int(numero))
        return f"{numero:.1f}"

    t = re.sub(r"\d+\.\d+", sem_zero_decimal, t)
    t = re.sub(r"\bhoras\b", "h", t)
    t = re.sub(r"\bhora\b", "h", t)
    t = re.sub(r"(\d)\s+h\b", r"\1h", t)
    return t


def contem(texto: str, alvo: str) -> bool:
    """Procura o trecho já normalizado.

    "cabe" sozinho não pode aprovar "não cabe": seria a resposta contrária
    contando como certa. O alvo afirmativo exige a palavra inteira, sem a
    negação imediatamente antes.
    """
    if alvo == "cabe":
        return re.search(r"(?<!nao )\bcabe\b", texto) is not None
    return alvo in texto


def avaliar(resposta: str, consulta: dict) -> bool:
    """A resposta conta como correta se contiver cada trecho do gabarito."""
    texto = normalizar(resposta)
    return all(contem(texto, normalizar(alvo)) for alvo in consulta["deve_conter"])
