# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 06: Aprovação humana e estado persistente
# Seção 5 – Conferência humana e retomada
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Uma negativa de acesso à informação não sai da Ouvidoria sem a leitura
de quem assina. O `@human_feedback` interrompe o fluxo, mostra a minuta
e espera o parecer da pessoa; um modelo converte o que ela escreveu em
um dos desfechos declarados, e o desfecho escolhe o próximo método.
Enquanto não aprovam, a minuta volta para revisão.

O `@persist` grava o estado em SQLite a cada etapa, de modo que um fluxo
interrompido pode ser retomado pelo seu identificador.
"""
from datetime import date, timedelta

from crewai.flow.flow import Flow, listen, or_, start
from crewai.flow.human_feedback import HumanFeedbackResult, human_feedback
from crewai.flow.persistence import SQLiteFlowPersistence, persist
from pydantic import BaseModel

from ouvidoria import MODELO, carregar_manifestacoes


class Negativa(BaseModel):
    texto: str = ""
    protocolo: str = ""
    prazo_recurso: str = ""
    minuta: str = ""
    revisoes: int = 0
    enviada: bool = False


@persist()   # estado gravado em SQLite após cada método
class NegativaDeAcesso(Flow[Negativa]):

    @start()
    def abrir(self) -> str:
        self.state.protocolo = f"LAI-{date.today():%Y}-{self.state.id[:6]}"
        self.state.prazo_recurso = (date.today() + timedelta(days=10)).strftime("%d/%m/%Y")
        return self.state.protocolo

    @human_feedback(
        message="A negativa acima será enviada ao cidadão. Aprova o envio ou pede ajuste?",
        emit=["aprovada", "ajustar"],
        llm="openai/gpt-5.6-luna",
        default_outcome="ajustar",
    )
    @listen(or_(abrir, "ajustar"))
    def redigir_minuta(self) -> str:
        """Executa na abertura e de novo a cada pedido de ajuste."""
        orientacao = ""
        if self.last_human_feedback is not None:
            orientacao = f" Incorpore esta orientação do revisor: {self.last_human_feedback.feedback}"
            self.state.revisoes += 1
        self.state.minuta = MODELO.call([{"role": "user", "content": (
            "Redija, em até 70 palavras, a negativa de acesso à informação para o "
            f"protocolo {self.state.protocolo}, fundamentada no art. 7º, § 3º, da Lei nº "
            f"12.527/2011, com direito de recurso até {self.state.prazo_recurso} (art. 15)."
            f"{orientacao}\n\nPedido: {self.state.texto}")}])
        return self.state.minuta

    @listen("aprovada")
    def enviar(self, resultado: HumanFeedbackResult) -> str:
        self.state.enviada = True
        print(f"\n[enviar] protocolo {self.state.protocolo} enviado após "
              f"{self.state.revisoes} revisão(ões). Parecer final: \"{resultado.feedback}\"")
        return self.state.protocolo


def main() -> None:
    pedido = [m for m in carregar_manifestacoes() if m["id"] == "M5"][0]
    fluxo = NegativaDeAcesso()
    fluxo.kickoff(inputs={"texto": pedido["texto"]})

    print("\n" + "=" * 72)
    print("histórico de pareceres humanos:")
    for item in fluxo.human_feedback_history:
        print(f"  - {item.feedback!r} -> desfecho {item.outcome!r}")

    # O estado gravado sobrevive ao processo: outro programa, em outro dia,
    # recupera-o pelo identificador. Um `kickoff(inputs={"id": ...})` reexecutaria
    # o fluxo partindo desse estado.
    banco = SQLiteFlowPersistence()
    gravado = banco.load_state(fluxo.state.id)
    print(f"\nestado gravado em {banco.db_path}")
    print(f"  protocolo={gravado['protocolo']}  enviada={gravado['enviada']}  "
          f"revisoes={gravado['revisoes']}")


if __name__ == "__main__":
    main()
