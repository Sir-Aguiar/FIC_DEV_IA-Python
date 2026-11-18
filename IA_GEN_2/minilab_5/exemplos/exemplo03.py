# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: O primeiro Flow, com estado tipado e diagrama
# Seção 4.1 – Etapas, estado e diagrama de um Flow
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Um pedido de acesso à informação percorre três etapas em um Flow: é
registrado, classificado e respondido. Não há equipe aqui ainda, apenas
chamadas diretas ao modelo, porque o objetivo é mostrar a mecânica do Flow:
o método de partida, os ouvintes, o estado compartilhado e o diagrama.
"""
from datetime import date, timedelta

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from ouvidoria import MODELO, carregar_manifestacoes


class Pedido(BaseModel):
    """O estado do fluxo. Todo método lê e escreve aqui, e o campo `id` é
    acrescentado pelo próprio CrewAI."""
    texto: str = ""
    protocolo: str = ""
    prazo_resposta: str = ""
    classificacao: str = ""
    motivo: str = ""
    resposta: str = ""


class Classificacao(BaseModel):
    categoria: str = Field(description="publica, dado_pessoal ou sigilosa")
    motivo: str = Field(description="Uma frase com o fundamento da classificação")


class PedidoDeInformacao(Flow[Pedido]):

    @start()
    def registrar(self) -> str:
        # A Lei nº 12.527/2011, art. 11, dá vinte dias para responder.
        self.state.protocolo = f"LAI-{date.today():%Y}-{self.state.id[:6]}"
        self.state.prazo_resposta = (date.today() + timedelta(days=20)).strftime("%d/%m/%Y")
        print(f"[registrar]   protocolo {self.state.protocolo}, prazo {self.state.prazo_resposta}")
        return self.state.protocolo

    @listen(registrar)
    def classificar(self, protocolo: str) -> str:
        resultado = MODELO.call(
            [{"role": "user", "content": (
                "Classifique o pedido de acesso à informação abaixo em uma de três "
                "categorias: 'publica' (informação que pode ser entregue), 'dado_pessoal' "
                "(contém dados de terceiros que exigem tratamento) ou 'sigilosa' "
                "(documento preparatório ou protegido por sigilo).\n\n"
                f"Pedido: {self.state.texto}")}],
            response_model=Classificacao,
        )
        self.state.classificacao = resultado.categoria
        self.state.motivo = resultado.motivo
        print(f"[classificar] {resultado.categoria}: {resultado.motivo}")
        return resultado.categoria

    @listen(classificar)
    def responder(self, categoria: str) -> str:
        self.state.resposta = MODELO.call(
            [{"role": "user", "content": (
                f"Redija, em até 80 palavras, a resposta ao cidadão para o pedido "
                f"{self.state.protocolo}, classificado como '{categoria}' porque "
                f"{self.state.motivo}. Prazo legal de resposta: {self.state.prazo_resposta}. "
                f"Pedido: {self.state.texto}")}]
        )
        print(f"[responder]   {len(self.state.resposta.split())} palavras")
        return self.state.resposta


def main() -> None:
    pedido = [m for m in carregar_manifestacoes() if m["id"] == "M3"][0]
    fluxo = PedidoDeInformacao()

    # O diagrama descreve a estrutura, não a execução, e por isso pode ser
    # gerado antes do kickoff. Com show=True (o padrão) ele abre no navegador.
    diagrama = fluxo.plot("fluxo_basico", show=False)

    resultado = fluxo.kickoff(inputs={"texto": pedido["texto"]})

    print("\n" + "=" * 72)
    print(f"estado final: id={fluxo.state.id}")
    print(f"  protocolo      : {fluxo.state.protocolo}")
    print(f"  classificação  : {fluxo.state.classificacao}")
    print(f"  resposta       : {resultado[:200]}...")
    print(f"diagrama gravado em {diagrama}")


if __name__ == "__main__":
    main()
