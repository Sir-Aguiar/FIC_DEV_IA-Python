"""Único lugar que instancia Agent e SqliteDb.

A Parte 2 pede o mesmo atendimento em estratégias diferentes. A estratégia
chega pronta, em argumentos do Agent. A derivação do user_id também mora
aqui: a função correta parte do documento do cidadão; a incorreta, usada só
na Parte 5, parte do guichê.
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

from src.configuracao import (
    INSTRUCAO,
    MODELO,
    PASTA_BANCOS,
    REASONING_EFFORT,
)


def identificador_do_cidadao(cidadao: dict) -> str:
    """O user_id sai do CPF do titular.

    O framework separa memória e histórico pelo identificador que recebe. Um
    documento individualiza a pessoa; canal, guichê e atendente não.
    """

    return cidadao["cpf"]


def identificador_do_guiche(guiche: str) -> str:
    """Derivação incorreta, restrita à reprodução do vazamento na Parte 5.

    Na aula, user_id igual ao guichê fez o segundo cidadão receber o
    atendimento do primeiro. Esta função existe para esse experimento, e não
    para o atendimento medido.
    """

    return guiche


def caminho_do_banco(nome: str):
    """Caminho do SQLite de um cenário. Cada experimento usa o próprio arquivo."""

    return PASTA_BANCOS / f"{nome}.db"


def conectar_banco(nome: str) -> SqliteDb:
    """Abre um banco já gravado, sem apagar o atendimento.

    Eliminação e releitura usam o arquivo que o atendimento acabou de gravar.
    Passar de novo por abrir_banco apagaria a sessão antes da conferência.
    """

    return SqliteDb(db_file=str(caminho_do_banco(nome)))


def abrir_banco(nome: str) -> SqliteDb:
    """Cria o SQLite da configuração e apaga o arquivo anterior.

    A Parte 2 compara estratégias. Um banco reaproveitado carregaria memória
    de outra rodada e misturaria o custo medido com um atendimento velho.
    """

    PASTA_BANCOS.mkdir(exist_ok=True)
    caminho = caminho_do_banco(nome)
    for sufixo in ("", "-wal", "-shm"):
        candidato = pathlib_do(caminho, sufixo)
        if candidato.exists():
            candidato.unlink()
    return SqliteDb(db_file=str(caminho))


def pathlib_do(caminho, sufixo: str):
    return caminho.parent / f"{caminho.name}{sufixo}"


def montar_agente(
    nome_banco: str | None,
    user_id: str,
    session_id: str,
    estrategia: dict,
    reaproveitar: bool = False,
) -> Agent:
    """Monta o atendente com a estratégia recebida.

    Sem banco, o agente não tem onde guardar a sessão: é a configuração sem
    memória. Com banco, os argumentos da estratégia ligam histórico, janela
    ou resumo. reaproveitar abre o arquivo que já existe; a Parte 4 precisa
    disso, porque abrir_banco apagaria o atendimento antes de excluí-lo.
    """

    argumentos = dict(estrategia)
    if nome_banco is not None:
        argumentos["db"] = conectar_banco(nome_banco) if reaproveitar else abrir_banco(nome_banco)

    return Agent(
        model=OpenAIChat(id=MODELO, reasoning_effort=REASONING_EFFORT),
        instructions=INSTRUCAO,
        markdown=False,
        user_id=user_id,
        session_id=session_id,
        **argumentos,
    )
