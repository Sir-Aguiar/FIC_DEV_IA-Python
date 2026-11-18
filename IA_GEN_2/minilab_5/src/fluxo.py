# ============================================================
# Minilab 05 – Fluxo de tratamento da conta citada
# na manifestação do setor de tecnologia da informação
# ============================================================
"""Três desfechos para a mesma rotina, com conferência, equipe e assinatura.

Dois métodos de partida correm juntos: um abre o registro e o outro
confere o relato em código. and_ só libera o roteador quando os dois
terminaram. O incidente, que é o ramo mais trabalhoso, chama uma equipe
sequencial. A revogação não sai sem assinatura: o parecer humano escolhe
entre assinar e reter, e reter é o desfecho conservador.
"""
from datetime import date
from typing import Literal

from crewai import Crew, Process, Task
from crewai.flow.flow import Flow, and_, listen, or_, router, start
from crewai.flow.human_feedback import HumanFeedbackResult, human_feedback
from crewai.flow.persistence import SQLiteFlowPersistence, persist
from pydantic import BaseModel, Field

from setor_ti import MODELO, carregar_manifestacoes, seguranca, service_desk


# Rótulos que o roteador pode devolver. Cada um aciona um único ouvinte.
Rotulo = Literal["acompanhar_chamado", "revogar_acessos", "registrar_incidente"]

# Gabarito das três manifestações que cabem nesta rotina, fixado antes
# de qualquer execução do fluxo.
DESFECHO_ESPERADO = {
    "MTI1": "acompanhar_chamado",
    "MTI3": "registrar_incidente",
    "MTI6": "revogar_acessos",
}

# Termos que o relato precisa citar para a rotina de conta fazer sentido.
# A conferência é código: não chama o modelo.
TERMOS_DE_CONTA = ("conta", "acesso", "chamado", "perfil", "credencial")


class EstadoDoTratamento(BaseModel):
    """Estado compartilhado pelos métodos do fluxo.

    O framework acrescenta o identificador interno. O desfecho só é
    preenchido depois que o roteador escolhe o rótulo. token_usage guarda
    o consumo da equipe do incidente. pareceres guarda cada assinatura
    ou pedido de ajuste, para o estado gravado poder ser relido.
    """

    texto: str = ""
    canal: str = ""
    protocolo: str = ""
    requisitos_ok: bool = False
    pendencia: str = ""
    desfecho: str = ""
    motivo: str = ""
    ramo: str = ""
    resposta: str = ""
    token_usage: dict[str, int] = Field(default_factory=dict)
    assinada: bool = False
    revisoes: int = 0
    pareceres: list[dict[str, str]] = Field(default_factory=list)


class Decisao(BaseModel):
    """Saída estruturada do roteador. O modelo só pode escolher um rótulo."""

    desfecho: Rotulo = Field(
        description="acompanhar_chamado, revogar_acessos ou registrar_incidente"
    )
    motivo: str = Field(description="Uma frase com o fundamento da escolha")


class PareceresEmSequencia:
    """Entrega pareceres já escritos, na ordem, no lugar do teclado.

    O primeiro pede ajuste, então o fluxo retem a revogação. O segundo
    assina. Assim o histórico tem os dois pareceres quando a execução acaba.
    """

    def __init__(self) -> None:
        self._fila = [
            (
                "Não assino. Reter a revogação e ajustar a minuta: ela deve "
                "dizer que a conta só será desligada depois da assinatura, "
                "e não que já foi desligada."
            ),
            "Assino. Aprovo o envio da revogação.",
        ]

    def request_feedback(self, context, flow) -> str:
        if not self._fila:
            return "Assino. Aprovo o envio da revogação."
        return self._fila.pop(0)


PARECERES = PareceresEmSequencia()


def redigir(instrucao: str, estado: EstadoDoTratamento) -> str:
    """Pede a minuta do ramo simples, com o registro e o motivo da triagem."""
    return MODELO.call(
        [
            {
                "role": "user",
                "content": (
                    f"{instrucao} Use até 60 palavras. Registro {estado.protocolo}. "
                    f"Motivo da escolha: {estado.motivo}. "
                    f"Manifestação, recebida por {estado.canal}: {estado.texto}"
                ),
            }
        ]
    )


def equipe_de_incidente() -> Crew:
    """Equipe sequencial do incidente: primeiro o fato, depois a resposta.

    O analista de segurança só registra. O analista da central de serviços
    redige a resposta a partir desse registro e não investiga a conta.
    """
    registrar_fato = Task(
        description=(
            "Registre o fato técnico da manifestação de registro {protocolo}, "
            "recebida por {canal}. Anote o horário, o que foi consultado e o "
            "sinal de uso fora do padrão. Não julgue autoria, não revele quem "
            "relatou além do que o texto já diz e não revogue a conta.\n\n"
            "Manifestação: {texto}"
        ),
        expected_output="Registro do fato em até 80 palavras, sem juízo de autoria.",
        agent=seguranca,
    )
    responder = Task(
        description=(
            "Com base no registro técnico recebido, redija a resposta do registro "
            "{protocolo}. Diga que o fato segue para o tratamento de incidente, "
            "que a identidade de quem relatou fica preservada e que a conta não "
            "foi revogada por esta resposta. Até 60 palavras. Motivo da triagem: "
            "{motivo}."
        ),
        expected_output="Resposta pronta para envio, em até 60 palavras.",
        agent=service_desk,
        context=[registrar_fato],
    )
    return Crew(
        agents=[seguranca, service_desk],
        tasks=[registrar_fato, responder],
        process=Process.sequential,
        verbose=False,
    )


def anotar_parecer(estado: EstadoDoTratamento, resultado: HumanFeedbackResult) -> None:
    """Acrescenta um parecer ao estado, sem repetir o último já gravado."""
    texto = resultado.feedback or ""
    if estado.pareceres and estado.pareceres[-1]["texto"] == texto:
        return
    estado.pareceres.append(
        {
            "texto": texto,
            "desfecho": resultado.outcome or "",
        }
    )


@persist()
class TratamentoDeConta(Flow[EstadoDoTratamento]):

    @start()
    def abrir(self) -> str:
        """Primeira partida: cria o número do registro."""
        self.state.protocolo = f"CONTA-{date.today():%Y}-{self.state.id[:6]}"
        return self.state.protocolo


    @start()
    def conferir_relato(self) -> bool:
        """Segunda partida, em paralelo à abertura. Só código, sem modelo.

        O relato precisa ter corpo e citar a conta. A pendência fica no
        estado mesmo quando a conferência passa, para a leitura posterior.
        """
        texto = self.state.texto.lower()
        menciona = any(termo in texto for termo in TERMOS_DE_CONTA)
        self.state.requisitos_ok = len(self.state.texto.split()) >= 12 and menciona
        if self.state.requisitos_ok:
            self.state.pendencia = ""
        elif not menciona:
            self.state.pendencia = (
                "o relato não menciona conta, acesso, chamado, perfil ou credencial"
            )
        else:
            self.state.pendencia = "relato curto demais para tratar a conta"
        return self.state.requisitos_ok


    @router(and_(abrir, conferir_relato))
    def decidir(self) -> Rotulo:
        """Só corre depois da abertura e da conferência. Devolve um rótulo."""
        resultado = MODELO.call(
            [
                {
                    "role": "user",
                    "content": (
                        "Uma manifestação do setor de tecnologia da informação fala "
                        "de uma conta. Escolha exatamente um rótulo.\n"
                        "acompanhar_chamado: já existe chamado aberto e a pessoa cobra "
                        "prazo ou andamento. Código que não chega no celular, enquanto "
                        "o pedido for de andamento, fica aqui.\n"
                        "revogar_acessos: há pedido formal para desligar conta ou perfil "
                        "de quem saiu. Contrato de terceirizado encerrado fica aqui.\n"
                        "registrar_incidente: a conta foi usada fora do expediente ou de "
                        "fora da rede, e o relato pede registro do fato. Este rótulo não "
                        "revoga a conta.\n\n"
                        f"Canal: {self.state.canal}\n"
                        f"Manifestação: {self.state.texto}"
                    ),
                }
            ],
            response_model=Decisao,
        )
        self.state.desfecho = resultado.desfecho
        self.state.motivo = resultado.motivo
        return resultado.desfecho


    @listen("acompanhar_chamado")
    def acompanhar(self) -> str:
        """O chamado já existe. A resposta informa o próximo retorno e não revoga conta."""
        self.state.ramo = "acompanhar"
        self.state.resposta = redigir(
            "Redija a resposta informando que o chamado já aberto será acompanhado, "
            "qual é o próximo retorno e o que a pessoa pode fazer enquanto espera. "
            "Não prometa revogação nem investigação.",
            self.state,
        )
        return self.state.resposta


    @listen("registrar_incidente")
    def anotar_incidente(self) -> str:
        """Ramo mais trabalhoso: a equipe sequencial registra o fato e redige a resposta.

        O método não se chama como o rótulo, para o ouvinte não escutar a si mesmo.
        Os dados entram por inputs. O consumo fica em token_usage.
        """
        antes = MODELO.get_token_usage_summary()
        resultado = equipe_de_incidente().kickoff(
            inputs={
                "texto": self.state.texto,
                "canal": self.state.canal,
                "protocolo": self.state.protocolo,
                "motivo": self.state.motivo,
            }
        )
        self.state.ramo = "registrar_incidente"
        self.state.resposta = resultado.raw
        self.state.token_usage = (
            MODELO.get_token_usage_summary().delta_since(antes).model_dump()
        )
        return self.state.resposta


    @human_feedback(
        message=(
            "A minuta acima desliga conta e perfil. Assina o envio ou pede "
            "para reter a revogação?"
        ),
        emit=["assinada", "reter"],
        llm="openai/gpt-5.6-luna",
        default_outcome="reter",
        provider=PARECERES,
    )
    @listen(or_("revogar_acessos", "reter"))
    def propor_revogacao(self) -> str:
        """Minuta da revogação. Sem assinatura clara, o desfecho conservador é reter.

        Quando o parecer anterior pediu ajuste, a minuta seguinte o incorpora.
        """
        orientacao = ""
        if self.last_human_feedback is not None:
            anotar_parecer(self.state, self.last_human_feedback)
            orientacao = (
                f" Incorpore esta orientação de quem assina: "
                f"{self.last_human_feedback.feedback}"
            )
            self.state.revisoes += 1
        self.state.ramo = "revogar"
        self.state.resposta = redigir(
            "Redija a minuta que pede assinatura para revogar a conta e o perfil. "
            "Diga que a conta só será desligada depois da assinatura. Não investigue "
            "uso indevido."
            + orientacao,
            self.state,
        )
        return self.state.resposta


    @listen("assinada")
    def efetivar(self, resultado: HumanFeedbackResult) -> str:
        """A revogação só é marcada como assinada depois do parecer de aprovação."""
        anotar_parecer(self.state, resultado)
        self.state.assinada = True
        return self.state.protocolo


    @listen(or_(acompanhar, anotar_incidente, efetivar))
    def encerrar(self, _retorno: str) -> dict:
        """Os três ramos se encontram aqui. Só um deles terá rodado."""
        return {
            "protocolo": self.state.protocolo,
            "desfecho": self.state.desfecho,
            "ramo": self.state.ramo,
            "palavras": len(self.state.resposta.split()),
            "chamadas": self.state.token_usage.get("successful_requests", 0),
            "assinada": self.state.assinada,
            "pareceres": len(self.state.pareceres),
        }


def historico_completo(gravado: dict, fluxo: TratamentoDeConta) -> bool:
    """O estado relido contém cada parecer da execução, e o último assina."""
    pareceres = gravado.get("pareceres") or []
    historico = fluxo.human_feedback_history
    if not pareceres or len(pareceres) != len(historico):
        return False
    if not gravado.get("assinada"):
        return False
    if pareceres[-1].get("desfecho") != "assinada":
        return False
    for parecer, item in zip(pareceres, historico):
        if parecer.get("texto") != item.feedback:
            return False
        if parecer.get("desfecho") != item.outcome:
            return False
    return True


def main() -> None:
    # O gabarito é lido agora, antes do kickoff, e não entra no inputs.
    manifestacoes = [
        m for m in carregar_manifestacoes() if m["id"] in DESFECHO_ESPERADO
    ]
    print(
        f"{'Manifestação':<14}{'Desfecho':<24}{'Esperado':<24}"
        f"{'Ramo':<22}{'Chamadas':>9}{'Pareceres':>10}"
    )
    for manifestacao in manifestacoes:
        fluxo = TratamentoDeConta()
        registro = fluxo.kickoff(
            inputs={"texto": manifestacao["texto"], "canal": manifestacao["canal"]}
        )
        print(
            f"{manifestacao['id']:<14}{registro['desfecho']:<24}"
            f"{DESFECHO_ESPERADO[manifestacao['id']]:<24}"
            f"{registro['ramo']:<22}{registro['chamadas']:>9}{registro['pareceres']:>10}"
        )
        if manifestacao["id"] != "MTI6":
            continue

        banco = SQLiteFlowPersistence()
        gravado = banco.load_state(fluxo.state.id)
        completo = gravado is not None and historico_completo(gravado, fluxo)
        print("\nEstado gravado da revogação, relido depois da assinatura")
        print(f"  banco: {banco.db_path}")
        print(f"  histórico completo: {completo}")
        if gravado is not None:
            for parecer in gravado["pareceres"]:
                print(f"  - {parecer['desfecho']}: {parecer['texto']}")


if __name__ == "__main__":
    main()
