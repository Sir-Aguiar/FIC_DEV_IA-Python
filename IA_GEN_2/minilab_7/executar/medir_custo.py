"""Roda o roteiro nas configurações da Parte 2 e grava o JSON medido.

A lógica de medição fica em src/custo.py. Este script só chama a função,
imprime a tabela e grava resultados/resultado_memoria.json.
"""

import json
import sys
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.configuracao import ARQUIVO_RESULTADO_MEMORIA
from src.custo import medir
from src.roteiro import carregar


def principal() -> None:
    roteiro = carregar()
    resultado = medir(roteiro)

    print(
        f"{'Configuração':<24} {'Lembrou':>8} {'Entrada T1':>11} "
        f"{'Meio':>8} {'Fim':>8} {'Acumulado':>11} {'US$':>10}"
    )
    for item in resultado["configuracoes"]:
        lembrou = f"{item['acertos']}/{item['verificacoes']}"
        print(
            f"{item['rotulo']:<24} {lembrou:>8} {item['entrada_t1']:>11} "
            f"{item['entrada_meio']:>8} {item['entrada_fim']:>8} "
            f"{item['entrada_total']:>11} {item['custo']:>10.5f}"
        )

    print()
    print(f"Crescimento de entrada por turno no histórico completo: {resultado['crescimento_entrada_por_turno']:.1f} tokens")
    print(f"Patamar de entrada do resumo no último turno: {resultado['patamar_resumo']} tokens")
    print(f"O resumo passaria a compensar por volta do turno {resultado['turnos_para_resumo_compensar']:.0f}")

    ARQUIVO_RESULTADO_MEMORIA.parent.mkdir(exist_ok=True)
    ARQUIVO_RESULTADO_MEMORIA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Resultados em {ARQUIVO_RESULTADO_MEMORIA}")


if __name__ == "__main__":
    principal()
