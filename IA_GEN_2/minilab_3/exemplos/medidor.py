# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Apoio: middleware que instrumenta o laço do agente
# Seção 5 – Experimento: quanto custa cada consulta, e por quê
# Requisitos: pip install langchain langchain-openai
# ============================================================
"""Middleware autoral que grava o que o agente fez em cada consulta.

Sem instrumentação, um agente é uma caixa que devolve texto e uma fatura no
fim do mês. Os dois ganchos abaixo interceptam cada chamada ao modelo e cada
chamada de ferramenta, registrando passos, nomes, argumentos e tokens. É esse
registro que transforma o comportamento do agente em número, e o número em
decisão de projeto.
"""
from dataclasses import dataclass, field

from langchain.agents.middleware import wrap_model_call, wrap_tool_call


@dataclass
class Registro:
    """Acumula o que aconteceu durante uma consulta."""

    chamadas_modelo: int = 0
    ferramentas: list[str] = field(default_factory=list)
    argumentos: list[dict] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_saida: int = 0

    def custo(self, usd_entrada: float, usd_saida: float) -> float:
        return (self.tokens_entrada / 1_000_000 * usd_entrada
                + self.tokens_saida / 1_000_000 * usd_saida)

    def zerar(self) -> None:
        self.chamadas_modelo = 0
        self.ferramentas.clear()
        self.argumentos.clear()
        self.tokens_entrada = self.tokens_saida = 0


def instrumentar(registro: Registro):
    """Devolve os dois middlewares que alimentam o registro."""

    @wrap_model_call
    def contar_modelo(request, handler):
        registro.chamadas_modelo += 1
        resposta = handler(request)
        # O objeto de resposta muda de forma entre versões; a leitura defensiva
        # abaixo evita que a instrumentação quebre o agente que ela observa.
        mensagem = getattr(resposta, "result", None) or getattr(resposta, "message", None)
        if isinstance(mensagem, list) and mensagem:
            mensagem = mensagem[0]
        uso = getattr(mensagem, "usage_metadata", None) or {}
        registro.tokens_entrada += uso.get("input_tokens", 0)
        registro.tokens_saida += uso.get("output_tokens", 0)
        return resposta

    @wrap_tool_call
    def contar_ferramenta(request, handler):
        chamada = getattr(request, "tool_call", {}) or {}
        registro.ferramentas.append(chamada.get("name", "?"))
        registro.argumentos.append(chamada.get("args", {}))
        return handler(request)

    return [contar_modelo, contar_ferramenta]
