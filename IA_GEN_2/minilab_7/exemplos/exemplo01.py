# ============================================================
# Aula 07 – Agentes com Memória Persistente
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 01: Os quatro tipos de memória, lado a lado
# Seção 1 e 2 – Quatro coisas que se chamam memória
# Requisitos: pip install agno sqlalchemy openai python-dotenv
# ============================================================
"""Distingue os quatro mecanismos que o Agno chama de memória.

O termo memória cobre coisas diferentes, com custos e riscos diferentes, e
tratá-las como uma só é a origem de boa parte da confusão sobre o assunto.
Este exemplo liga cada uma isoladamente e mostra onde o dado fica gravado.
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
PASTA = BASE / "bancos_tipos"
CPF = "111.222.333-44"
INSTRUCAO = "Você atende contribuintes da Secretaria de Fazenda sobre IPVA."

# Os quatro mecanismos, com o argumento que liga cada um.
TIPOS = [
    ("1 · histórico da sessão",
     "reenvia as mensagens anteriores desta conversa",
     {"add_history_to_context": True, "num_history_runs": 10}),
    ("2 · memórias do usuário",
     "extrai fatos sobre a pessoa e os guarda entre sessões",
     {"add_history_to_context": True, "num_history_runs": 10,
      "update_memory_on_run": True}),
    ("3 · resumo da sessão",
     "condensa a conversa em um resumo reaproveitado depois",
     {"add_history_to_context": True, "num_history_runs": 3,
      "enable_session_summaries": True}),
    ("4 · memória agêntica",
     "deixa o próprio modelo decidir o que guardar",
     {"add_history_to_context": True, "num_history_runs": 10,
      "enable_agentic_memory": True}),
]


def montar(nome: str, extras: dict) -> Agent:
    PASTA.mkdir(exist_ok=True)
    return Agent(model=OpenAIChat(id=MODELO, reasoning_effort="none"),
                 db=SqliteDb(db_file=str(PASTA / f"{nome}.db")),
                 instructions=INSTRUCAO, markdown=False,
                 user_id=CPF, session_id=f"sessao_{nome}", **extras)


def main() -> None:
    if PASTA.exists():
        shutil.rmtree(PASTA)

    print("=" * 76)
    print("Quatro mecanismos que se chamam memória")
    print("=" * 76)

    for rotulo, descricao, extras in TIPOS:
        nome = rotulo.split("·")[0].strip()
        agente = montar(nome, extras)
        agente.run(f"Sou João Silva, CPF {CPF}. Meu Fiat Uno placa QBA-1234 "
                   f"está com IPVA em aberto.")
        resposta = agente.run("Qual a placa que eu informei?")
        lembrou = "QBA-1234" in str(resposta.content)
        entrada = resposta.metrics.input_tokens

        print(f"\n{rotulo}")
        print(f"    {descricao}")
        print(f"    argumentos: {', '.join(f'{k}={v}' for k, v in extras.items())}")
        print(f"    lembrou a placa? {'sim' if lembrou else 'não'} · "
              f"entrada no 2º turno: {entrada} tokens")

    print("\nOs quatro resolvem o mesmo problema — o modelo não tem estado entre")
    print("chamadas — por caminhos com custos distintos. A Seção 3 mede cada um.")


if __name__ == "__main__":
    main()
