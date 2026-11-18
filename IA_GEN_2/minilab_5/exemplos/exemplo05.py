# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 05: Uma equipe dentro do Flow e a junção com and_
# Seção 4.3 – A equipe como etapa do fluxo
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Duas etapas de código correm em paralelo ao abrir o pedido: o registro
do protocolo e a conferência dos requisitos mínimos. Só quando as duas
terminam, `and_` libera a etapa seguinte, que chama uma equipe inteira:
o analista jurídico fundamenta e o analista de atendimento redige. A
equipe é uma etapa do fluxo como qualquer outra, e o fluxo guarda o que
ela devolveu.
"""
import json
from datetime import date, timedelta

from crewai import Crew, Process, Task
from crewai.flow.flow import Flow, and_, listen, start
from pydantic import BaseModel

from ouvidoria import BASE, atendente, carregar_manifestacoes, custo, juridico


class Pedido(BaseModel):
    texto: str = ""
    protocolo: str = ""
    prazo_resposta: str = ""
    requisitos_ok: bool = False
    pendencia: str = ""
    resposta: str = ""
    chamadas: int = 0


def equipe_de_resposta() -> Crew:
    fundamentar = Task(
        description=(
            "Indique o fundamento legal para responder ao pedido de acesso à informação "
            "abaixo, citando os artigos da Lei nº 12.527/2011 aplicáveis e dizendo se há "
            "dados pessoais de terceiros a proteger.\n\nPedido: {texto}"
        ),
        expected_output="Fundamento legal em até 80 palavras, com os artigos citados.",
        agent=juridico,
    )
    redigir = Task(
        description=(
            "Com base no fundamento jurídico recebido, redija a resposta ao cidadão para "
            "o protocolo {protocolo}, com prazo legal {prazo_resposta}, em até 80 palavras."
        ),
        expected_output="Resposta ao cidadão pronta para envio.",
        agent=atendente,
        context=[fundamentar],
    )
    return Crew(agents=[juridico, atendente], tasks=[fundamentar, redigir],
                process=Process.sequential)


class RespostaComEquipe(Flow[Pedido]):

    @start()
    def registrar(self) -> str:
        self.state.protocolo = f"LAI-{date.today():%Y}-{self.state.id[:6]}"
        self.state.prazo_resposta = (date.today() + timedelta(days=20)).strftime("%d/%m/%Y")
        print(f"[registrar]          {self.state.protocolo}")
        return self.state.protocolo

    @start()
    def conferir_requisitos(self) -> bool:
        """Roda em paralelo ao registro: é código comum, sem modelo."""
        self.state.requisitos_ok = len(self.state.texto.split()) >= 8
        self.state.pendencia = "" if self.state.requisitos_ok else "pedido genérico demais"
        print(f"[conferir_requisitos] ok={self.state.requisitos_ok}")
        return self.state.requisitos_ok

    @listen(and_(registrar, conferir_requisitos))
    def redigir_com_a_equipe(self) -> str:
        """Só executa quando os dois métodos de partida terminaram."""
        resultado = equipe_de_resposta().kickoff(inputs={
            "texto": self.state.texto,
            "protocolo": self.state.protocolo,
            "prazo_resposta": self.state.prazo_resposta,
        })
        self.state.resposta = resultado.raw
        self.state.chamadas = resultado.token_usage.successful_requests
        print(f"[redigir_com_a_equipe] {self.state.chamadas} chamadas, "
              f"US$ {custo(resultado.token_usage):.5f}")
        return resultado.raw

    @listen(redigir_com_a_equipe)
    def arquivar(self, resposta: str) -> str:
        destino = BASE / f"{self.state.protocolo}.json"
        destino.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")
        print(f"[arquivar]           {destino.name}")
        return str(destino)


def main() -> None:
    pedido = [m for m in carregar_manifestacoes() if m["id"] == "M4"][0]
    fluxo = RespostaComEquipe()
    fluxo.plot("fluxo_equipe", show=False)
    fluxo.kickoff(inputs={"texto": pedido["texto"]})
    print("\n" + "=" * 72)
    print(fluxo.state.resposta.strip())


if __name__ == "__main__":
    main()
