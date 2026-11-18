# ============================================================
# Aula 05 – Orquestração de Equipes no CrewAI
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: Desvios com @router e junção com or_
# Seção 4.2 – O caminho que depende do resultado
# Requisitos: pip install crewai openai python-dotenv pydantic
# ============================================================
"""Um pedido de acesso à informação não tem um caminho único. Se a
informação é pública, ela é entregue; se contém dados de terceiros, é
entregue com os dados tarjados; se é sigilosa, o pedido é negado com o
fundamento legal e a indicação do recurso. O `@router` escolhe o ramo a
partir da classificação, e `or_` reúne os três ramos no registro final.
"""
from datetime import date, timedelta

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel, Field

from ouvidoria import MODELO, carregar_manifestacoes


class Pedido(BaseModel):
    texto: str = ""
    protocolo: str = ""
    prazo_resposta: str = ""
    classificacao: str = ""
    motivo: str = ""
    ramo: str = ""
    resposta: str = ""


class Classificacao(BaseModel):
    categoria: str = Field(description="publica, dado_pessoal ou sigilosa")
    motivo: str = Field(description="Uma frase com o fundamento da classificação")


def redigir(instrucao: str, estado: Pedido) -> str:
    return MODELO.call([{"role": "user", "content": (
        f"{instrucao} Use até 60 palavras. Protocolo {estado.protocolo}, prazo legal "
        f"{estado.prazo_resposta}. Pedido do cidadão: {estado.texto}")}])


class TriagemLAI(Flow[Pedido]):

    @start()
    def registrar(self) -> str:
        self.state.protocolo = f"LAI-{date.today():%Y}-{self.state.id[:6]}"
        self.state.prazo_resposta = (date.today() + timedelta(days=20)).strftime("%d/%m/%Y")
        return self.state.protocolo

    @router(registrar)
    def classificar(self) -> str:
        """Devolve um rótulo, e é o rótulo que escolhe o próximo método."""
        resultado = MODELO.call(
            [{"role": "user", "content": (
                "Classifique o pedido de acesso à informação em 'publica', 'dado_pessoal' "
                "(contém dados de terceiros) ou 'sigilosa' (documento preparatório ou "
                f"protegido por sigilo).\n\nPedido: {self.state.texto}")}],
            response_model=Classificacao,
        )
        self.state.classificacao = resultado.categoria
        self.state.motivo = resultado.motivo
        return resultado.categoria

    @listen("publica")
    def entregar(self) -> str:
        self.state.ramo = "entregar"
        self.state.resposta = redigir(
            "Redija a resposta informando que o pedido foi deferido e como a informação "
            "será disponibilizada.", self.state)
        return self.state.resposta

    @listen("dado_pessoal")
    def entregar_com_tarja(self) -> str:
        self.state.ramo = "entregar_com_tarja"
        self.state.resposta = redigir(
            "Redija a resposta informando que o acesso será concedido com os dados "
            "pessoais de terceiros tarjados, conforme o art. 31 da Lei nº 12.527/2011.",
            self.state)
        return self.state.resposta

    @listen("sigilosa")
    def negar_com_fundamento(self) -> str:
        self.state.ramo = "negar_com_fundamento"
        self.state.resposta = redigir(
            "Redija a negativa de acesso, fundamentada no art. 7º, § 3º, da Lei nº "
            "12.527/2011 (documento preparatório), informando o direito de recurso em "
            "dez dias, previsto no art. 15.", self.state)
        return self.state.resposta

    @listen(or_(entregar, entregar_com_tarja, negar_com_fundamento))
    def registrar_resposta(self, resposta: str) -> dict:
        """Qualquer um dos três ramos termina aqui."""
        return {"protocolo": self.state.protocolo, "ramo": self.state.ramo,
                "palavras": len(resposta.split())}


def main() -> None:
    pedidos = [m for m in carregar_manifestacoes() if m["id"] in ("M3", "M4", "M5")]
    print(f"{'Pedido':<8}{'Classificação':<16}{'Ramo executado':<24}{'Esperado':<14}{'Palavras':>9}")
    for p in pedidos:
        fluxo = TriagemLAI()
        registro = fluxo.kickoff(inputs={"texto": p["texto"]})
        print(f"{p['id']:<8}{fluxo.state.classificacao:<16}{registro['ramo']:<24}"
              f"{p['classificacao_esperada']:<14}{registro['palavras']:>9}")
        if p["id"] == "M5":
            print("\n  Negativa redigida para a M5:\n  " + fluxo.state.resposta.replace("\n", "\n  "))


if __name__ == "__main__":
    main()
