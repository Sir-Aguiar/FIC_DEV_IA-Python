# ============================================================
# Aula 07 – Agentes com Memória Persistente
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 03: O que o agente guardou, e se a exclusão apaga mesmo
# Seção 4 e 6 – A memória sob a LGPD
# Requisitos: pip install agno sqlalchemy openai python-dotenv
# ============================================================
"""Inspeciona o que o agente reteve sobre a pessoa e testa a eliminação.

A LGPD assegura ao titular o direito de obter a eliminação dos seus dados. Em
um agente com memória persistente esse direito só é exercível se duas
condições forem verdadeiras: é preciso saber o que foi guardado, e é preciso
que apagar realmente apague. Este exemplo verifica as duas.
"""
import json
import pathlib
import shutil
import sqlite3
import warnings

warnings.filterwarnings("ignore")

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

BASE = pathlib.Path(__file__).parent
load_dotenv(BASE.parents[2] / ".env")

MODELO = "gpt-5.6-luna"
ARQUIVO = BASE / "atendimento_lgpd.db"
CPF = "111.222.333-44"

INSTRUCAO = ("Você atende contribuintes da Secretaria de Fazenda de Mato Grosso "
             "sobre IPVA. Seja objetivo e cordial.")


def montar() -> Agent:
    return Agent(model=OpenAIChat(id=MODELO, reasoning_effort="none"),
                 db=SqliteDb(db_file=str(ARQUIVO)),
                 instructions=INSTRUCAO, markdown=False,
                 user_id=CPF, session_id=f"atendimento_{CPF}",
                 add_history_to_context=True, num_history_runs=10,
                 update_memory_on_run=True)


def conversar() -> None:
    """Um atendimento curto, em que o cidadão diz mais do que precisaria."""
    print("\n[1] O atendimento")
    agente = montar()
    falas = [
        f"Bom dia. Sou João Silva, CPF {CPF}. Meu Fiat Uno placa QBA-1234 está com "
        "IPVA em aberto mesmo depois de eu ter pago.",
        "Estou passando por dificuldade financeira e preciso muito resolver isso "
        "antes do fim do mês.",
        "Pode abrir um protocolo para acompanhamento?",
    ]
    for fala in falas:
        resposta = agente.run(fala)
        print(f"    cidadão : {fala[:76]}...")
        print(f"    agente  : {str(resposta.content).strip()[:110]}\n")


def inspecionar_tabelas() -> None:
    """Mostra onde o Agno guardou o quê, lendo o banco diretamente."""
    print("[2] O que o Agno gravou, e em quais tabelas")
    if not ARQUIVO.exists():
        print("    banco não encontrado")
        return
    conexao = sqlite3.connect(ARQUIVO)
    tabelas = [linha[0] for linha in conexao.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for tabela in tabelas:
        total = conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        print(f"    {tabela:32} {total:>4} registro(s)")
    conexao.close()
    print("    Cada uma dessas tabelas é um lugar onde um dado pessoal pode estar,")
    print("    e o direito de eliminação alcança todas elas.")


def listar_memorias() -> list:
    """O que o agente decidiu, por conta própria, guardar sobre a pessoa."""
    print("\n[3] O que o agente reteve sobre a pessoa")
    agente = montar()
    memorias = []
    for metodo in ("get_user_memories", "get_memories"):
        if hasattr(agente, metodo):
            try:
                memorias = getattr(agente, metodo)(user_id=CPF) or []
                break
            except Exception:
                continue
    if not memorias:
        print("    nenhuma memória de usuário registrada")
        return []
    print(f"    {len(memorias)} memória(s) extraída(s) automaticamente:\n")
    for memoria in memorias:
        texto = str(getattr(memoria, "memory", memoria))
        # Critério da necessidade, aplicado ao texto integral da memória: o dado
        # serve para resolver o pedido, ou excede a finalidade do atendimento?
        excede = any(p in texto.lower() for p in
                     ("dificuldade", "financeir", "problema pessoal", "saúde", "doen"))
        print(f"    · {texto}")
        print(f"      necessária ao atendimento? "
              f"{'NÃO — excede a finalidade' if excede else 'sim'}")
    return memorias


def testar_exclusao(antes: list) -> None:
    """Apaga os dados do titular em duas etapas e verifica o que sobreviveu.

    O objeto `Agent` oferece a exclusão da sessão, que remove o registro da
    conversa e das execuções. As memórias extraídas sobre a pessoa ficam em
    outra tabela e só são removidas pelo objeto de banco, com uma chamada que
    recebe os identificadores das memórias e não o do usuário. A eliminação
    completa exige, portanto, as duas etapas — e o teste mostra o que resta
    entre uma e outra.
    """
    print("\n[4] O teste de eliminação")
    banco = SqliteDb(db_file=str(ARQUIVO))

    print("    métodos de exclusão no objeto Agent  :",
          [m for m in dir(Agent) if "delete" in m.lower()] or "nenhum")
    print("    métodos de exclusão no objeto do banco:",
          [m for m in dir(banco) if m.startswith("delete_user") or m == "delete_sessions"])
    print(f"\n    antes da exclusão, o titular aparece em: {ocorrencias_do_titular()}")

    # Etapa 1 — exclusão da sessão pelo próprio agente.
    montar().delete_session(session_id=f"atendimento_{CPF}")
    print("\n    etapa 1: agent.delete_session(session_id)")
    print(f"    o titular ainda aparece em: {ocorrencias_do_titular() or 'nenhuma tabela'}")
    restantes = banco.get_user_memories(user_id=CPF) or []
    print(f"    memórias remanescentes: "
          f"{[str(getattr(m, 'memory', m))[:60] for m in restantes] or 'nenhuma'}")
    perguntar("após a etapa 1")

    # Etapa 2 — exclusão das memórias pelo objeto de banco. O método recebe a
    # lista de identificadores, e não o usuário: é preciso listar para apagar.
    ids = [getattr(m, "memory_id", None) or getattr(m, "id", None) for m in restantes]
    ids = [i for i in ids if i]
    if ids:
        banco.delete_user_memories(memory_ids=ids, user_id=CPF)
    print(f"\n    etapa 2: banco.delete_user_memories(memory_ids=[{len(ids)} id(s)])")
    print(f"    o titular ainda aparece em: {ocorrencias_do_titular() or 'nenhuma tabela'}")
    perguntar("após a etapa 2")


def perguntar(momento: str) -> None:
    """Pergunta ao agente, em sessão nova, o que ele ainda sabe sobre o titular."""
    resposta = montar().run("Qual é o meu nome e o meu CPF?")
    conteudo = str(resposta.content)
    print(f"    pergunta {momento}: o agente sabe o nome? "
          f"{'SIM' if 'João' in conteudo else 'não'} · sabe o CPF? "
          f"{'SIM' if '111' in conteudo else 'não'}")
    # A própria pergunta cria nova sessão; ela é apagada para não contaminar
    # a medição seguinte.
    montar().delete_session(session_id=f"atendimento_{CPF}")


def ocorrencias_do_titular() -> dict:
    """Conta em quantos registros de cada tabela aparecem o CPF ou o nome."""
    conexao = sqlite3.connect(ARQUIVO)
    encontrado = {}
    for (tabela,) in conexao.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        try:
            linhas = conexao.execute(f"SELECT * FROM {tabela}").fetchall()
        except sqlite3.Error:
            continue
        total = sum(1 for linha in linhas if CPF in str(linha) or "João Silva" in str(linha))
        if total:
            encontrado[tabela] = total
    conexao.close()
    return encontrado


if __name__ == "__main__":
    if ARQUIVO.exists():
        ARQUIVO.unlink()
    print("=" * 78)
    print("A memória do agente sob a Lei Geral de Proteção de Dados")
    print("=" * 78)
    conversar()
    inspecionar_tabelas()
    memorias = listar_memorias()
    testar_exclusao(memorias)
    print()
