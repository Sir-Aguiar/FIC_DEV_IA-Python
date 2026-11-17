"""Parte 5: o vazamento da Seção 5.1 e a regra que o evita.

O framework separa o que foi declarado. Ele não adivinha que um guichê não é
uma pessoa. A primeira metade usa o mesmo session_id com um user_id por CPF.
A segunda deriva o user_id do guichê e entrega o atendimento da primeira
pessoa à segunda. A regra correta está em identificador_do_cidadao.
"""

from src.configuracao import ARQUIVO_VAZAMENTO
from src.fabrica import identificador_do_cidadao, identificador_do_guiche, montar_agente

# Histórico ligado de propósito: é ele que reenvia o turno anterior quando a
# sessão e o identificador são os mesmos. Sem isso, o vazamento do guichê
# não apareceria na resposta.
ESTRATEGIA = {"add_history_to_context": True, "num_history_runs": 10}

ANA = {
    "nome": "Ana Beatriz Costa",
    "cpf": "045.882.173-90",
    "login": "ana.costa",
}
CARLOS = {
    "nome": "Carlos Eduardo Mendes",
    "cpf": "390.441.228-06",
    "login": "carlos.mendes",
}
GUICHE = "guiche_02"
PERGUNTA = "Pode me confirmar o meu nome completo e o login institucional que eu já informei?"
FALA_DA_ANA = (
    "Sou Ana Beatriz Costa, CPF 045.882.173-90. "
    "Meu login institucional é ana.costa e o SEI está bloqueado."
)


def falar(banco: str, user_id: str, session_id: str, texto: str, reaproveitar: bool) -> str:
    atendente = montar_agente(banco, user_id, session_id, ESTRATEGIA, reaproveitar=reaproveitar)
    return str(atendente.run(texto).content).strip()


def recebeu_dado_da_ana(texto: str) -> bool:
    return any(marca in texto for marca in ("Ana", "ana.costa", "045.882"))


def mesma_sessao_identificadores_distintos() -> dict:
    """Metade em que o framework isola: uma sessão, um CPF por pessoa.

    O session_id é o mesmo de propósito. O que muda é o user_id, derivado
    do documento. Carlos não deve receber o login da Ana.
    """

    sessao = "sessao_balcao"
    falar(
        "falhas_isolado",
        identificador_do_cidadao(ANA),
        sessao,
        FALA_DA_ANA,
        reaproveitar=False,
    )
    resposta = falar(
        "falhas_isolado",
        identificador_do_cidadao(CARLOS),
        sessao,
        PERGUNTA,
        reaproveitar=True,
    )
    return {"resposta": resposta, "vazou": recebeu_dado_da_ana(resposta)}


def identificador_derivado_do_guiche() -> dict:
    """Metade que vaza: as duas pessoas herdam o identificador do guichê.

    guiche_02 não individualiza. Quem passou por esse balcão fica com o
    mesmo user_id e a mesma sessão, e o histórico da Ana entra na resposta
    ao Carlos.
    """

    identificador = identificador_do_guiche(GUICHE)
    falar("falhas_guiche", identificador, identificador, FALA_DA_ANA, reaproveitar=False)
    resposta = falar("falhas_guiche", identificador, identificador, PERGUNTA, reaproveitar=True)
    return {"resposta": resposta, "vazou": recebeu_dado_da_ana(resposta)}


def redigir(isolado: dict, guiche: dict) -> str:
    regra = (
        "O user_id do service desk da MTI sai do CPF do servidor, "
        "pela função identificador_do_cidadao. O CPF individualiza porque "
        "há um por pessoa. Guichê, canal e atendente são compartilhados por "
        "todos os chamados daquele balcão, então não separam um titular do outro."
    )
    return "\n".join([
        "# Vazamento por identificador",
        "",
        "## Mesma sessão, CPFs distintos",
        "",
        "O framework isolou." if not isolado["vazou"] else "Houve vazamento mesmo com CPFs distintos.",
        "",
        f"> {isolado['resposta']}",
        "",
        "## Mesmo identificador, derivado do guichê",
        "",
        "O segundo cidadão recebeu dado da Ana." if guiche["vazou"] else "O guichê não vazou nesta execução.",
        "",
        f"> {guiche['resposta']}",
        "",
        "## Regra correta",
        "",
        regra,
        "",
    ])


def reproduzir() -> dict:
    """Roda as duas metades e grava o texto que Carlos recebeu."""

    isolado = mesma_sessao_identificadores_distintos()
    guiche = identificador_derivado_do_guiche()
    ARQUIVO_VAZAMENTO.parent.mkdir(exist_ok=True)
    ARQUIVO_VAZAMENTO.write_text(redigir(isolado, guiche), encoding="utf-8")
    return {"isolado": isolado, "guiche": guiche}
