"""Ferramentas do assistente de encaixe de lote de processamento fiscal.

A primeira ferramenta usa o decorador @tool. A segunda é uma função anotada,
sem decorador, e só vira ferramenta na lista, com tool(). O modelo não vê
este código: vê o nome, a descrição e o tipo de cada argumento. O ritmo e as
horas da janela saem da consulta ou da pergunta, então o encaixe não pode
usar um rendimento que o modelo tenha inventado.
"""

import json
import pathlib
import unicodedata

from langchain_core.tools import tool


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


# A segunda forma não leva @tool na função. A conversão acontece aqui.
FERRAMENTAS = [consultar_rotina, tool(calcular_encaixe_lote)]
