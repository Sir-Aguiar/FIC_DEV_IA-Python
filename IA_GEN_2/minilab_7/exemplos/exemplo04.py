# ============================================================
# Aula 07 – Agentes com Memória Persistente
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 04: As falhas da memória, provocadas de propósito
# Seção 5 – Quando a memória atrapalha
# Requisitos: pip install agno sqlalchemy openai python-dotenv
# ============================================================
"""Provoca as falhas próprias de um agente que lembra.

As falhas anteriores do módulo eram de raciocínio ou de coordenação. Estas
são de estado: o agente passa a carregar informação entre chamadas, e isso
cria modos de erro que não existem em um agente sem memória. A mais grave
delas, em serviço público, é a troca de identificador de usuário.
"""
import pathlib
import shutil
import warnings

warnings.filterwarnings("ignore")

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = "gpt-5.6-luna"
PASTA = BASE / "bancos_falhas"
INSTRUCAO = ("Você atende contribuintes da Secretaria de Fazenda de Mato Grosso. "
             "Use as informações que o contribuinte já forneceu nesta conversa.")


def agente(nome: str, user_id: str, session_id: str, **extras) -> Agent:
    PASTA.mkdir(exist_ok=True)
    return Agent(model=OpenAIChat(id=MODELO, reasoning_effort="none"),
                 db=SqliteDb(db_file=str(PASTA / f"{nome}.db")),
                 instructions=INSTRUCAO, markdown=False,
                 user_id=user_id, session_id=session_id,
                 add_history_to_context=True, **{"num_history_runs": 10, **extras})


def falha_1_sessao_trocada() -> None:
    """Dois cidadãos no mesmo atendimento: o que o framework protege e o que não.

    O teste tem duas metades. Na primeira, os cidadãos partilham a sessão mas
    têm identificadores próprios; na segunda, o identificador é o mesmo para os
    dois, situação que ocorre quando o programador o deriva de algo que não
    individualiza — o guichê, o atendente ou o canal, em vez do cidadão.
    """
    print("\n[1] Quando um cidadão enxerga o atendimento de outro")

    print("\n  a) mesma sessão, identificadores diferentes")
    joao = agente("isolado", "111.222.333-44", "sessao_unica")
    joao.run("Sou João Silva, CPF 111.222.333-44, e meu carro é um Fiat Uno "
             "placa QBA-1234.")
    maria = agente("isolado", "555.666.777-88", "sessao_unica")
    conteudo = str(maria.run("Bom dia, qual o nome e a placa do meu atendimento?").content)
    vazou = "João" in conteudo or "QBA-1234" in conteudo
    print(f"     a resposta a Maria contém dados de João? "
          f"{'SIM — VAZAMENTO' if vazou else 'não — o framework isolou'}")

    print("\n  b) mesmo identificador para os dois, por erro de derivação")
    # O erro: o user_id foi derivado do guichê, e não do cidadão.
    joao2 = agente("vazamento", "guiche_03", "guiche_03")
    joao2.run("Sou João Silva, CPF 111.222.333-44, Fiat Uno placa QBA-1234.")
    maria2 = agente("vazamento", "guiche_03", "guiche_03")
    conteudo2 = str(maria2.run("Bom dia, qual o nome e a placa do meu atendimento?").content)
    vazou2 = "João" in conteudo2 or "QBA-1234" in conteudo2
    print(f"     a resposta a Maria contém dados de João? "
          f"{'SIM — VAZAMENTO' if vazou2 else 'não'}")
    print(f"     resposta: {conteudo2.strip()[:150]}")

    print("\n     O `user_id` separa as memórias e a `session_id` separa o histórico.")
    print("     O framework cumpre a separação que lhe for declarada — e não tem")
    print("     como saber que 'guiche_03' não identifica uma pessoa.")


def falha_2_memoria_desatualizada() -> None:
    """O agente responde pela memória em vez de consultar de novo."""
    print("\n[2] A memória que envelhece")
    contribuinte = agente("desatualizada", "999.888.777-66", "sessao_status")
    contribuinte.run("Meu protocolo 2026009012 está aguardando documentação, "
                     "conforme me informaram na semana passada.")
    resposta = contribuinte.run("E agora, qual a situação do meu protocolo?")
    conteudo = str(resposta.content)
    repetiu = "aguardando" in conteudo.lower()
    print(f"    o cidadão informou uma situação na primeira mensagem")
    print(f"    ao ser perguntado de novo, o agente repete o que foi dito? "
          f"{'SIM' if repetiu else 'não'}")
    print(f"    resposta: {conteudo.strip()[:170]}")
    print("    Sem ferramenta de consulta, a memória vira fonte de verdade — e ela")
    print("    guarda o que era verdade quando foi gravada, não o que é agora.")


def falha_3_crescimento_sem_limite() -> None:
    """A entrada cresce a cada turno quando o histórico é completo."""
    print("\n[3] A conta que cresce sozinha")
    contribuinte = agente("crescimento", "222.333.444-55", "sessao_longa",
                          num_history_runs=100)
    entradas = []
    for i in range(6):
        resposta = contribuinte.run(
            f"Pergunta {i + 1}: preciso de informação sobre IPVA, parcelamento, "
            f"isenção e restituição. Detalhe cada ponto.")
        entradas.append(resposta.metrics.input_tokens)
    print(f"    tokens de entrada por turno: {entradas}")
    if entradas[0]:
        print(f"    crescimento do 1º ao 6º turno: {entradas[-1] / entradas[0]:.1f}×")
    print("    Cada turno reenvia todos os anteriores. O crescimento é previsível")
    print("    e precisa de teto, seja por janela, seja por resumo.")


if __name__ == "__main__":
    if PASTA.exists():
        shutil.rmtree(PASTA)
    print("=" * 74)
    print("Quando a memória atrapalha")
    print("=" * 74)
    for funcao in (falha_1_sessao_trocada, falha_2_memoria_desatualizada,
                   falha_3_crescimento_sem_limite):
        try:
            funcao()
        except Exception as erro:
            print(f"    interrompida: {type(erro).__name__} — {str(erro)[:100]}")
    print()
