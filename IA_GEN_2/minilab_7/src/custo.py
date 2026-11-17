"""Parte 2: quanto custa lembrar neste roteiro da MTI.

Três configurações fecham o contraste. Sem memória é a linha de base: não
carrega nada e por isso não responde às verificações. Histórico completo
reenvia os turnos anteriores e, numa conversa curta de balcão, é a estratégia
que ainda cabe. Resumo com janela de três parte de um patamar mais alto,
porque cada chamada também resume a sessão. A conta do ponto de virada usa a
série de entrada do histórico completo e esse patamar.
"""

import time

from src.configuracao import USD_ENTRADA, USD_SAIDA
from src.fabrica import identificador_do_cidadao, montar_agente
from src.roteiro import conferir

# num_history_runs alto no histórico completo evita que a janela padrão do
# Agno (três execuções) descarte o começo do chamado. No resumo, a janela
# curta é proposital: o que deveria sobreviver do início é o resumo, não a
# mensagem original.
CONFIGURACOES = [
    {
        "rotulo": "sem memória",
        "banco": None,
        "estrategia": {},
    },
    {
        "rotulo": "histórico completo",
        "banco": "historico_completo",
        "estrategia": {
            "add_history_to_context": True,
            "num_history_runs": 100,
        },
    },
    {
        "rotulo": "resumo + janela de 3",
        "banco": "resumo_janela",
        "estrategia": {
            "add_history_to_context": True,
            "num_history_runs": 3,
            "enable_session_summaries": True,
        },
    },
]


def executar_configuracao(configuracao: dict, roteiro: dict) -> dict:
    """Percorre o roteiro uma vez e acumula tokens, acertos, tempo e dólares."""

    usuario = roteiro["usuario"]
    agente = montar_agente(
        configuracao["banco"],
        identificador_do_cidadao(usuario),
        f"atendimento_{configuracao['banco'] or 'sem_memoria'}",
        configuracao["estrategia"],
    )

    entradas = []
    acertos = 0
    verificacoes = 0
    total_entrada = 0
    total_saida = 0
    inicio = time.perf_counter()

    for turno in roteiro["turnos"]:
        resposta = agente.run(turno["texto"])
        metricas = resposta.metrics
        entradas.append(metricas.input_tokens)
        total_entrada += metricas.input_tokens
        total_saida += metricas.output_tokens

        if turno["verificacao"]:
            verificacoes += 1
            if conferir(resposta.content, turno["verificacao"]):
                acertos += 1

    meio = len(entradas) // 2
    return {
        "rotulo": configuracao["rotulo"],
        "acertos": acertos,
        "verificacoes": verificacoes,
        "entrada_t1": entradas[0],
        "entrada_meio": entradas[meio - 1],
        "turno_meio": meio,
        "entrada_fim": entradas[-1],
        "entrada_total": total_entrada,
        "saida_total": total_saida,
        "entradas": entradas,
        "tempo": time.perf_counter() - inicio,
        "custo": custo_em_dolares(total_entrada, total_saida),
    }


def custo_em_dolares(entrada: int, saida: int) -> float:
    """Converte tokens em dólares com os preços da configuração compartilhada."""

    return entrada / 1e6 * USD_ENTRADA + saida / 1e6 * USD_SAIDA


def crescimento_por_turno(entradas: list[int]) -> float:
    """Média das diferenças consecutivas da série de entrada.

    No histórico completo cada turno reenvia os anteriores, e a aula observa
    que esse acréscimo é aproximadamente linear. A média das diferenças é o
    crescimento por turno usado na conta do ponto de virada.
    """

    diferencas = [atual - anterior for anterior, atual in zip(entradas, entradas[1:])]
    return sum(diferencas) / len(diferencas)


def turnos_para_resumo_compensar(entradas_historico: list[int], patamar_resumo: int) -> float:
    """Estima o turno em que o histórico acumulado supera o custo do resumo.

    A Seção 3.3 trata o resumo como custo aproximadamente fixo por chamada e o
    histórico completo como uma reta: entrada(k) = t1 + g*(k-1). A soma dos
    n primeiros termos é n*t1 + g*n*(n-1)/2. Ela ultrapassa patamar*n quando

        n = 1 + 2*(patamar - t1) / g

    Com os números da aula (cerca de 80 tokens por turno e patamar de 1791 no
    fim da configuração D) essa conta cai perto de 44 turnos, na faixa de
    quarenta a cinquenta lida no gráfico. O patamar usado aqui é a entrada do
    último turno da configuração de resumo medida neste roteiro.
    """

    crescimento = crescimento_por_turno(entradas_historico)
    entrada_inicial = entradas_historico[0]
    if crescimento <= 0:
        return float("inf")
    return 1 + 2 * (patamar_resumo - entrada_inicial) / crescimento


def medir(roteiro: dict) -> dict:
    """Roda as três configurações e anexa a conta do ponto de virada."""

    configuracoes = [executar_configuracao(item, roteiro) for item in CONFIGURACOES]
    historico = next(item for item in configuracoes if item["rotulo"] == "histórico completo")
    resumo = next(item for item in configuracoes if item["rotulo"] == "resumo + janela de 3")
    crescimento = crescimento_por_turno(historico["entradas"])
    patamar = resumo["entrada_fim"]
    virada = turnos_para_resumo_compensar(historico["entradas"], patamar)

    return {
        "turnos": len(roteiro["turnos"]),
        "verificacoes": historico["verificacoes"],
        "configuracoes": configuracoes,
        "crescimento_entrada_por_turno": crescimento,
        "patamar_resumo": patamar,
        "turnos_para_resumo_compensar": virada,
    }
