"""Parte 4: eliminar o titular das tabelas em que o identificador apareceu.

Na versão testada do Agno não há uma chamada única por pessoa. delete_session
apaga a sessão e as execuções e preserva agno_memories. As memórias só saem
com delete_user_memories no banco, e esse método pede os memory_id, não o
CPF: é preciso listar para apagar. A contagem percorre de novo todas as
tabelas, inclusive quando a lista de memórias vem vazia.
"""

from src.configuracao import ARQUIVO_ELIMINACAO
from src.fabrica import (
    caminho_do_banco,
    conectar_banco,
    identificador_do_cidadao,
    montar_agente,
)
from src.memorias import (
    NOME_BANCO,
    SESSAO_ATENDIMENTO,
    formas_do_identificador,
    ocorrencias,
    trechos_excedentes,
)

PERGUNTA = "Sem que eu repita nada: qual é o meu nome completo, o meu login institucional e o nome da minha mãe?"


def tabelas_do_identificador(caminho, cpf: str) -> dict[str, int]:
    """As tabelas do item 9: onde o CPF da cidadã aparece nesta leitura."""

    return ocorrencias(caminho, formas_do_identificador(cpf))


def rastros(caminho, roteiro: dict) -> dict[str, dict[str, int]]:
    """Procura identificador, nome, login e o dado desnecessário em toda tabela."""

    usuario = roteiro["usuario"]
    alvos = {
        "identificador": formas_do_identificador(usuario["cpf"]),
        "nome": [usuario["nome"]],
        "login": [usuario["login"]],
        "dado_desnecessario": trechos_excedentes(roteiro),
    }
    return {rotulo: ocorrencias(caminho, agulhas) for rotulo, agulhas in alvos.items()}


def nada_restou(leitura: dict[str, dict[str, int]]) -> bool:
    return not any(leitura.values())


def agente(user_id: str, session_id: str, estrategia: dict):
    return montar_agente(NOME_BANCO, user_id, session_id, estrategia, reaproveitar=True)


def excluir_sessao(user_id: str, session_id: str) -> None:
    """Etapa 1, também usada para apagar a sessão criada pela pergunta de prova.

    A pergunta grava um atendimento novo com o mesmo CPF. Sem este apagamento,
    a conferência final veria a prova e concluiria que o titular restou.
    """

    agente(user_id, session_id, {}).delete_session(session_id=session_id, user_id=user_id)


def excluir_memorias(user_id: str) -> list[str]:
    """Etapa 2: lista memory_id e apaga no objeto de banco.

    A chamada acontece mesmo com a lista vazia no sentido de que a etapa não
    é pulada: listar e só então apagar é o que a versão testada do Agno exige.
    """

    banco = conectar_banco(NOME_BANCO)
    memorias = banco.get_user_memories(user_id=user_id) or []
    identificadores = []
    for memoria in memorias:
        identificador = getattr(memoria, "memory_id", None) or getattr(memoria, "id", None)
        if identificador:
            identificadores.append(identificador)
    if identificadores:
        banco.delete_user_memories(memory_ids=identificadores, user_id=user_id)
    return identificadores


def perguntar(user_id: str, session_id: str) -> str:
    """Pergunta, numa sessão nova, o que só a memória da pessoa saberia.

    Histórico desligado e sessão nova: a resposta não pode vir do turno
    anterior. Memórias de usuário ligadas: se a etapa 2 não tiver apagado,
    o nome, o login e o nome da mãe ainda entram no contexto.
    """

    atendente = agente(
        user_id,
        session_id,
        {
            "add_memories_to_context": True,
            "add_history_to_context": False,
            "update_memory_on_run": False,
        },
    )
    try:
        resposta = atendente.run(PERGUNTA)
        return str(resposta.content).strip()
    finally:
        excluir_sessao(user_id, session_id)


def redigir(resultado: dict) -> str:
    linhas = [
        "# Eliminação dos dados do titular",
        "",
        "A rotina percorre as tabelas em que o identificador apareceu na Parte 3. "
        "A etapa 1 apaga sessão e execuções. A etapa 2 apaga as memórias extraídas.",
        "",
        "## Contagem",
        "",
        "| Momento | Identificador | Nome | Login | Dado desnecessário |",
        "| --- | --- | --- | --- | --- |",
    ]
    for momento, leitura in resultado["contagens"].items():
        linhas.append(
            "| {momento} | {identificador} | {nome} | {login} | {excedente} |".format(
                momento=momento,
                identificador=_resumo(leitura["identificador"]),
                nome=_resumo(leitura["nome"]),
                login=_resumo(leitura["login"]),
                excedente=_resumo(leitura["dado_desnecessario"]),
            )
        )

    linhas.extend([
        "",
        f"Memórias apagadas na etapa 2: {len(resultado['memorias_apagadas'])}.",
        "",
        "## Resposta depois da etapa 1",
        "",
        "Encerrar aqui deixaria o agente sabendo o que estava em `agno_memories`.",
        "",
        f"> {resultado['resposta_apos_etapa_1']}",
        "",
        "## Resposta depois da exclusão completa",
        "",
        f"Pergunta: {PERGUNTA}",
        "",
        f"> {resultado['resposta_apos_etapa_2']}",
        "",
        "Conferência no banco depois das duas etapas e da limpeza da pergunta: "
        + ("nada do titular restou." if resultado["nada_restou"] else "ainda há registro do titular."),
        "",
    ])
    return "\n".join(linhas)


def _resumo(tabelas: dict[str, int]) -> str:
    if not tabelas:
        return "nenhuma tabela"
    return ", ".join(f"{tabela} ({total})" for tabela, total in tabelas.items())


def eliminar(roteiro: dict) -> dict:
    """Executa as duas etapas no banco do atendimento e registra a resposta."""

    caminho = caminho_do_banco(NOME_BANCO)
    if not caminho.exists():
        raise FileNotFoundError(f"Banco do atendimento não encontrado: {caminho}")

    user_id = identificador_do_cidadao(roteiro["usuario"])
    contagens = {"antes": rastros(caminho, roteiro)}

    excluir_sessao(user_id, SESSAO_ATENDIMENTO)
    contagens["depois da etapa 1"] = rastros(caminho, roteiro)
    resposta_etapa_1 = perguntar(user_id, "pergunta_apos_etapa_1")

    memorias_apagadas = excluir_memorias(user_id)
    contagens["depois da etapa 2"] = rastros(caminho, roteiro)
    resposta_etapa_2 = perguntar(user_id, "pergunta_apos_etapa_2")
    contagens["depois da limpeza da pergunta"] = rastros(caminho, roteiro)

    resultado = {
        "contagens": contagens,
        "memorias_apagadas": memorias_apagadas,
        "resposta_apos_etapa_1": resposta_etapa_1,
        "resposta_apos_etapa_2": resposta_etapa_2,
        "nada_restou": nada_restou(contagens["depois da limpeza da pergunta"]),
        "tabelas_do_item_9": list(contagens["antes"]["identificador"]),
    }
    ARQUIVO_ELIMINACAO.parent.mkdir(exist_ok=True)
    ARQUIVO_ELIMINACAO.write_text(redigir(resultado), encoding="utf-8")
    return resultado
