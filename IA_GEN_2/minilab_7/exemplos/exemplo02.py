# ============================================================
# Aula 07 – Agentes com Memória Persistente
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 02: Quanto custa lembrar
# Seção 3 – Experimento: quanto custa lembrar
# Requisitos: pip install agno openai python-dotenv
# ============================================================
"""Executa o mesmo atendimento de doze turnos em cinco configurações de memória.

Cada configuração resolve de um jeito o problema de o agente não ter estado
próprio entre as chamadas. O experimento mede o que cada uma custa e o que
cada uma consegue lembrar, porque as duas coisas andam em direções opostas:
lembrar tudo é caro e lembrar pouco é inútil.
"""
import json
import pathlib
import shutil
import time
import warnings

warnings.filterwarnings("ignore")

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = "gpt-5.6-luna"
USD_ENTRADA, USD_SAIDA = 0.20, 1.20
PASTA_BANCOS = BASE / "bancos"

INSTRUCAO = (
    "Você atende contribuintes da Secretaria de Fazenda de Mato Grosso sobre "
    "IPVA. Seja objetivo e cordial. Use as informações que o contribuinte já "
    "forneceu nesta conversa em vez de pedi-las de novo."
)


def banco(nome: str) -> SqliteDb:
    PASTA_BANCOS.mkdir(exist_ok=True)
    return SqliteDb(db_file=str(PASTA_BANCOS / f"{nome}.db"))


# Cada entrada é (rótulo, argumentos extras do Agent). A configuração A não
# recebe banco algum e por isso não guarda nada entre as chamadas.
CONFIGURACOES = [
    ("A · sem memória", lambda n: {}),
    ("B · histórico completo", lambda n: {
        "db": banco(n), "add_history_to_context": True, "num_history_runs": 100}),
    ("C · janela de 3 execuções", lambda n: {
        "db": banco(n), "add_history_to_context": True, "num_history_runs": 3}),
    ("D · resumo + janela de 3", lambda n: {
        "db": banco(n), "add_history_to_context": True, "num_history_runs": 3,
        "enable_session_summaries": True}),
    ("E · memórias de usuário + janela de 3", lambda n: {
        "db": banco(n), "add_history_to_context": True, "num_history_runs": 3,
        "update_memory_on_run": True}),
]


def executar(rotulo: str, construir, roteiro: dict) -> dict:
    nome = rotulo.split("·")[0].strip()
    extras = construir(nome)
    agente = Agent(model=OpenAIChat(id=MODELO, reasoning_effort="none"),
                   instructions=INSTRUCAO, markdown=False,
                   user_id=roteiro["usuario"]["cpf"],
                   session_id=f"atendimento_{nome}", **extras)

    entradas, acertos, verificacoes = [], 0, 0
    total_entrada = total_saida = 0
    inicio = time.perf_counter()

    for turno in roteiro["turnos"]:
        try:
            resposta = agente.run(turno["texto"])
        except Exception as erro:
            print(f"    turno {turno['n']}: {type(erro).__name__} — {str(erro)[:60]}")
            entradas.append(0)
            continue
        metricas = resposta.metrics
        entradas.append(metricas.input_tokens)
        total_entrada += metricas.input_tokens
        total_saida += metricas.output_tokens

        if turno["verificacao"]:
            verificacoes += 1
            conteudo = str(resposta.content).lower().replace("*", "")
            if all(a.lower() in conteudo for a in turno["verificacao"]["deve_conter"]):
                acertos += 1

    # Chamadas extras de extração e de resumo entram no consumo total, mas não
    # aparecem no `metrics` de cada turno; a diferença é estimada pelo total.
    custo = total_entrada / 1e6 * USD_ENTRADA + total_saida / 1e6 * USD_SAIDA
    return {"rotulo": rotulo, "acertos": acertos, "verificacoes": verificacoes,
            "entrada_t1": entradas[0] if entradas else 0,
            "entrada_t6": entradas[5] if len(entradas) > 5 else 0,
            "entrada_t12": entradas[-1] if entradas else 0,
            "entrada_total": total_entrada, "saida_total": total_saida,
            "tempo": time.perf_counter() - inicio, "custo": custo}


def main() -> None:
    roteiro = json.loads((BASE / "roteiro_atendimento.json").read_text(encoding="utf-8"))
    if PASTA_BANCOS.exists():
        shutil.rmtree(PASTA_BANCOS)   # cada rodada começa do zero
    verificacoes = sum(1 for t in roteiro["turnos"] if t["verificacao"])
    print(f"{len(roteiro['turnos'])} turnos · {verificacoes} verificações de memória\n")

    resultados = []
    for rotulo, construir in CONFIGURACOES:
        print(f"[{rotulo}] executando...")
        resultados.append(executar(rotulo, construir, roteiro))

    print(f"\n{'Configuração':40} {'Lembrou':>9} {'T1':>7} {'T6':>7} {'T12':>7} "
          f"{'Acumulado':>11} {'Tempo':>8} {'US$':>9}")
    print("-" * 106)
    for r in resultados:
        print(f"{r['rotulo']:40} {r['acertos']:>4}/{r['verificacoes']:<4} "
              f"{r['entrada_t1']:>7} {r['entrada_t6']:>7} {r['entrada_t12']:>7} "
              f"{r['entrada_total']:>11} {r['tempo']:>7.1f}s {r['custo']:>9.5f}")

    destino = BASE / "resultado_memoria.json"
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados em {destino.name}")


if __name__ == "__main__":
    main()
