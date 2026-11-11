# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 06: Assistente jurídico com orçamento e conferência humana
# Seção 7 – Assistente jurídico com orçamento e conferência humana
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""O assistente da Procuradoria com as barreiras que um órgão exige.

As seções anteriores mostraram que o modelo atual resiste bem às falhas
clássicas. Este exemplo parte do princípio de que resistir na maior parte das
vezes não basta quando o resultado fundamenta um ato administrativo, e por
isso instala quatro barreiras: teto de passos, exigência de fundamento para
argumento numérico, registro de auditoria e sinalização do que precisa de
conferência humana antes de virar peça.
"""
import json
import pathlib
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware,
    wrap_model_call,
    wrap_tool_call,
)
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

from ferramentas import FERRAMENTAS

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

INSTRUCAO = (
    "Você assessora procuradores do Estado de Mato Grosso. Use as ferramentas "
    "para fundamentar suas respostas e cite sempre a norma aplicável. Se a "
    "pergunta não trouxer os dados necessários para um cálculo, peça os dados "
    "que faltam em vez de supor valores. Nunca afirme que um débito está "
    "quitado ou que nada é devido sem que a ferramenta tenha devolvido essa "
    "informação."
)

# Assuntos que, por decisão da chefia, nunca saem sem leitura de um procurador.
EXIGEM_CONFERENCIA = ("prescri", "decadênc", "quitad", "renúncia", "anistia")


class AssistenteJuridico:
    """Agente com orçamento, barreira de argumento e trilha de auditoria."""

    def __init__(self, teto_passos: int = 8) -> None:
        self.trilha: list[dict] = []
        self.modelo = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")
        self.teto_passos = teto_passos

    def _barreiras(self, pergunta: str) -> list:
        trilha = self.trilha

        @wrap_model_call
        def auditar_modelo(request, handler):
            resposta = handler(request)
            trilha.append({"evento": "consulta_modelo",
                           "instante": datetime.now().isoformat(timespec="seconds")})
            return resposta

        @wrap_tool_call
        def exigir_fundamento(request, handler):
            """Recusa argumento numérico que não apareça na pergunta do usuário."""
            chamada = getattr(request, "tool_call", {}) or {}
            nome, argumentos = chamada.get("name", "?"), chamada.get("args") or {}
            limpo = pergunta.replace(".", "").replace(",", "")
            for campo, valor in argumentos.items():
                if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                    continue
                if str(int(valor)) not in limpo:
                    trilha.append({"evento": "chamada_recusada", "ferramenta": nome,
                                   "campo": campo, "valor": valor})
                    # É preciso devolver uma ToolMessage, e não uma string: o
                    # modelo já emitiu o tool_call, e a API recusa a conversa em
                    # que um tool_call fique sem resposta correspondente.
                    return ToolMessage(
                        content=(f"CHAMADA RECUSADA: o argumento {campo}={valor} não "
                                 f"consta da pergunta. Solicite o dado ao usuário."),
                        tool_call_id=chamada.get("id", ""),
                        name=nome,
                    )
            trilha.append({"evento": "ferramenta", "nome": nome, "argumentos": argumentos})
            return handler(request)

        return [
            auditar_modelo,
            exigir_fundamento,
            ModelCallLimitMiddleware(thread_limit=self.teto_passos, exit_behavior="end"),
            ToolCallLimitMiddleware(thread_limit=6, exit_behavior="end"),
        ]

    def consultar(self, pergunta: str) -> dict:
        self.trilha = []
        agente = create_agent(model=self.modelo, tools=FERRAMENTAS,
                              system_prompt=INSTRUCAO,
                              middleware=self._barreiras(pergunta))
        saida = agente.invoke({"messages": [{"role": "user", "content": pergunta}]})
        resposta = str(saida["messages"][-1].content).strip()

        motivos = [termo for termo in EXIGEM_CONFERENCIA if termo in resposta.lower()]
        recusas = [e for e in self.trilha if e["evento"] == "chamada_recusada"]
        return {
            "pergunta": pergunta,
            "resposta": resposta,
            "ferramentas": [e["nome"] for e in self.trilha if e["evento"] == "ferramenta"],
            "consultas_modelo": sum(1 for e in self.trilha if e["evento"] == "consulta_modelo"),
            "chamadas_recusadas": len(recusas),
            "exige_conferencia": bool(motivos) or bool(recusas),
            "motivo_conferencia": motivos,
        }


def main() -> None:
    assistente = AssistenteJuridico()
    perguntas = [
        "Qual o prazo para interposição de recurso administrativo e, se a ciência "
        "ocorreu em 2026-04-06, qual a data limite?",
        "Calcule a atualização de um débito de R$ 18.000,00 com 9 meses de atraso "
        "e informe a norma que fundamenta o cálculo.",
        "O débito daquele processo antigo já prescreveu? Considere o prazo usual.",
    ]

    registros = []
    for pergunta in perguntas:
        resultado = assistente.consultar(pergunta)
        registros.append(resultado)
        marca = "CONFERÊNCIA HUMANA" if resultado["exige_conferencia"] else "liberada"
        print(f"\n{'=' * 72}\n{pergunta[:68]}\n{'=' * 72}")
        print(f"  {resultado['resposta'][:300]}")
        print(f"\n  ferramentas: {resultado['ferramentas'] or 'nenhuma'} · "
              f"consultas ao modelo: {resultado['consultas_modelo']} · "
              f"recusadas: {resultado['chamadas_recusadas']}")
        print(f"  situação: {marca}"
              + (f" ({', '.join(resultado['motivo_conferencia'])})"
                 if resultado["motivo_conferencia"] else ""))

    destino = pathlib.Path(__file__).parent / "trilha_auditoria.json"
    destino.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTrilha de auditoria gravada em {destino.name}")


if __name__ == "__main__":
    main()
