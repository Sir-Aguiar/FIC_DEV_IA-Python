"""Ferramentas do assistente de encaixe de lote de processamento fiscal.

A primeira ferramenta usa o decorador @tool. A segunda é uma função anotada
e só vira ferramenta na lista, com tool(). A terceira usa StructuredTool e um
esquema Pydantic com descrição em cada campo. O modelo não vê este código:
vê o nome, a descrição e o significado de cada argumento. O ritmo e as horas
da janela saem da consulta ou da pergunta, então o encaixe não pode usar um
rendimento que o modelo tenha inventado.
"""

import json
import pathlib
import unicodedata

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field


# A base fica ao lado do código para a consulta funcionar sem serviço externo.
ROTINAS = pathlib.Path(__file__).parent / "dados" / "rotinas.json"


def _normalizar(texto: str) -> str:
    """Junta espaços, ignora maiúsculas e acentos, e elimina o hífen.

    "NF-e" e "nfe" precisam achar a mesma rotina. O hífen sai do texto em vez
    de virar espaço: se virasse, "nfe" não apareceria dentro de "nf e".
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(
        caractere for caractere in sem_acento if not unicodedata.combining(caractere)
    )
    sem_hifen = sem_acento.lower().replace("-", "")
    return " ".join(sem_hifen.split())


def _compactar(texto: str) -> str:
    """Tira os espaços que separam um código, como em "RT NFE"."""
    return _normalizar(texto).replace(" ", "")


def _horas(valor: float) -> str:
    """Escreve hora com vírgula, no formato usado pela equipe."""
    return f"{valor:.1f}".replace(".", ",")


def _formatar_rotina(rotina: dict) -> str:
    """Devolve ritmo, tamanho da janela e o quanto dela ainda está livre.

    As horas restantes são a conta desta consulta: janela menos o que já foi
    consumido. O encaixe do volume fica para a ferramenta de cálculo.
    """
    restantes = rotina["janela_horas"] - rotina["horas_consumidas"]
    ritmo = f"{rotina['registros_por_hora']:,}".replace(",", ".")
    return (
        f"{rotina['codigo']} — {rotina['nome']}. "
        f"Ritmo: {ritmo} registros por hora. "
        f"Janela: {_horas(rotina['janela_horas'])} h. "
        f"Já consumidas: {_horas(rotina['horas_consumidas'])} h. "
        f"Horas restantes: {_horas(restantes)} h."
    )


@tool
def consultar_rotina(rotina: str) -> str:
    """Busca a rotina de processamento fiscal que o lote vai usar.

    Use quando a pergunta trouxer o nome ou o código da rotina, como
    "processamento de NF-e" ou "RT-SPED".
    Devolve o ritmo em registros por hora, a duração da janela e as horas que ainda restam. 
    Se a rotina não estiver na base, informe que ela não existe e não estime ritmo nem janela.
    """
    # Cada chamada relê o arquivo. A base é pequena e assim as horas restantes
    # acompanham o que está escrito em disco, sem cache desatualizado.
    dados = json.loads(ROTINAS.read_text(encoding="utf-8"))
    termo = _normalizar(rotina)

    if not termo:
        return "Informe o nome ou o código da rotina. Sem isso ela não pode ser consultada."

    correspondencias = []
    
    for item in dados["rotinas"]:
        codigo = _normalizar(item["codigo"])
        nome = _normalizar(item["nome"])

        # Código casa inteiro, com ou sem espaço. Nome aceita o texto ou um
        # trecho com pelo menos três caracteres, para uma palavra como "de"
        # não devolver a base toda.
        codigo_ou_nome = _compactar(termo) == _compactar(codigo) or termo == nome
        trecho_do_nome = len(termo) >= 3 and (termo in nome or nome in termo)
        if codigo_ou_nome or trecho_do_nome:
            correspondencias.append(item)

    if not correspondencias:
        return (
            f"A rotina '{rotina}' não existe na base de processamento. "
            "Não há ritmo nem horas de janela para este lote."
        )

    if len(correspondencias) > 1:
        lista = "\n".join(_formatar_rotina(item) for item in correspondencias)
        return (
            "Há mais de uma rotina compatível. Use o código para escolher uma antes de encaixar o lote:\n"
            + lista
        )

    return _formatar_rotina(correspondencias[0])


def calcular_encaixe_lote(volume: int, registros_por_hora: int, horas_restantes: float) -> str:
    """Calcula se um lote cabe nas horas que ainda restam na janela.

    O volume é a quantidade de registros do lote. O ritmo, em registros por
    hora, e as horas restantes têm de vir da consulta da rotina ou estar
    escritos na pergunta. A conta divide o volume pelo ritmo e compara o
    resultado com as horas restantes. São horas corridas da janela, sem
    calendário de dias úteis.
    """
    # Ritmo zero quebraria a divisão. Volume ou ritmo negativo, e horas
    # restantes negativas, não existem na janela: a ferramenta recusa em vez
    # de devolver um encaixe com cara de certo.
    if volume <= 0 or registros_por_hora <= 0 or horas_restantes < 0:
        return (
            "Valores inválidos: o volume e o ritmo precisam ser positivos, "
            "e as horas restantes não podem ser negativas."
        )

    horas_necessarias = volume / registros_por_hora
    volume_fmt = f"{volume:,}".replace(",", ".")
    ritmo_fmt = f"{registros_por_hora:,}".replace(",", ".")
    cabe = horas_necessarias <= horas_restantes
    decisao = "o lote cabe na janela" if cabe else "o lote não cabe na janela"

    return (
        f"Lote de {volume_fmt} registros a {ritmo_fmt} por hora "
        f"precisa de {_horas(horas_necessarias)} h. "
        f"A janela tem {_horas(horas_restantes)} h restantes: {decisao}."
    )


class ConsumoJanela(BaseModel):
    """Argumentos para gravar o consumo de um lote na janela da rotina."""

    codigo_rotina: str = Field(
        description="Código devolvido pela consulta da rotina, como RT-NFE"
    )
    horas_previstas: float = Field(
        description="Horas que o cálculo de encaixe disse que o lote precisa"
    )


def _atualizar_consumo_janela(codigo_rotina: str, horas_previstas: float) -> str:
    """Soma as horas previstas ao consumo da rotina, se elas ainda couberem."""
    dados = json.loads(ROTINAS.read_text(encoding="utf-8"))
    codigo = _compactar(codigo_rotina)

    if not codigo:
        return "Informe o código da rotina devolvido pela consulta. Nada foi gravado."

    # Hora prevista nula ou negativa não é consumo: gravar isso apagaria a conta.
    if horas_previstas <= 0:
        return "As horas previstas precisam ser positivas. Nada foi gravado."

    rotina = next(
        (item for item in dados["rotinas"] if _compactar(item["codigo"]) == codigo),
        None,
    )
    if rotina is None:
        return f"A rotina '{codigo_rotina}' não existe na base. Nada foi gravado."

    restantes = rotina["janela_horas"] - rotina["horas_consumidas"]

    # A descrição pede para não chamar neste caso. Se a chamada chegar mesmo
    # assim, a janela fica como está: estourar a hora restante não pode ser gravado.
    if horas_previstas > restantes:
        return (
            f"{rotina['codigo']} tem {_horas(restantes)} h restantes e o lote pede "
            f"{_horas(horas_previstas)} h. O consumo não foi gravado."
        )

    # Uma casa decimal acompanha o que já está na base, como 2,5 h.
    rotina["horas_consumidas"] = round(rotina["horas_consumidas"] + horas_previstas, 1)
    ROTINAS.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    novas_restantes = rotina["janela_horas"] - rotina["horas_consumidas"]
    return (
        f"Consumo gravado em {rotina['codigo']}: {_horas(horas_previstas)} h. "
        f"Horas consumidas agora: {_horas(rotina['horas_consumidas'])} h. "
        f"Horas restantes: {_horas(novas_restantes)} h."
    )


atualizar_consumo_janela = StructuredTool.from_function(
    func=_atualizar_consumo_janela,
    name="atualizar_consumo_janela",
    description=(
        "Grava na janela da rotina as horas que o lote vai consumir. "
        "Não use quando o lote ultrapassar as horas restantes, nem quando "
        "o volume do lote não estiver escrito na pergunta."
    ),
    args_schema=ConsumoJanela,
)


# A segunda forma entra com tool(). A terceira já é um StructuredTool.
FERRAMENTAS = [consultar_rotina, tool(calcular_encaixe_lote), atualizar_consumo_janela]
