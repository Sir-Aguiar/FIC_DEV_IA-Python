# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 05: Os quatro modos de falha, provocados de propósito
# Seção 7 – Quando o LangChain atrapalha
# Requisitos: pip install langchain langchain-openai openai python-dotenv
# ============================================================
"""Provoca, uma a uma, as quatro falhas que aparecem ao migrar para 2026.

Cada função abaixo produz um erro real e o imprime. Executar este arquivo é
mais instrutivo do que ler a descrição das falhas, porque a mensagem de erro
que a biblioteca devolve é justamente o que o servidor vai encontrar quando o
código antigo parar de funcionar. Nenhuma das falhas é hipotética: todas
foram observadas na preparação desta aula.
"""
import os
import pathlib

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = "gpt-5.6-luna"


def falha_1_import_de_0x() -> None:
    """O código escrito para LangChain 0.x não encontra mais os símbolos."""
    print("\n[1] Importações que existiam na versão 0.x")
    for modulo, nome in (
        ("langchain.agents", "initialize_agent"),
        ("langchain.agents", "AgentExecutor"),
        ("langchain.agents", "create_tool_calling_agent"),
        ("langchain.chains", "LLMChain"),
    ):
        try:
            modulo_importado = __import__(modulo, fromlist=[nome])
            getattr(modulo_importado, nome)
            print(f"    {modulo}.{nome}: ainda existe")
        except (ImportError, AttributeError, ModuleNotFoundError) as erro:
            print(f"    {modulo}.{nome}: {type(erro).__name__} — {str(erro)[:70]}")


def falha_2_parametros_recusados() -> None:
    """A família GPT-5.6 recusa `temperature` e `max_tokens` — e o framework esconde.

    Esta é a falha mais instrutiva das quatro, porque o LangChain não se
    limita a repassar o pedido. Ele reescreve um dos parâmetros e descarta o
    outro, de modo que o mesmo código que estoura no SDK executa em silêncio
    aqui — com uma das duas configurações simplesmente não aplicada.
    """
    print("\n[2] Parâmetros que a família GPT-5.6 não aceita")
    cliente = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    mensagens = [{"role": "user", "content": "Responda apenas: ok"}]

    print("  a) direto no SDK da OpenAI:")
    for rotulo, parametros in (
        ("temperature=0.3", {"temperature": 0.3}),
        ("max_tokens=500", {"max_tokens": 500}),
        ("max_completion_tokens=500", {"max_completion_tokens": 500}),
    ):
        try:
            cliente.chat.completions.create(model=MODELO, messages=mensagens, **parametros)
            print(f"       {rotulo:26} aceito")
        except Exception as erro:
            mensagem = str(erro).split("message': ")[-1].replace("\n", " ")
            print(f"       {rotulo:26} {type(erro).__name__}: {mensagem[:88]}")

    print("  b) os mesmos parâmetros pelo LangChain:")
    modelo = init_chat_model(MODELO, model_provider="openai", temperature=0.3, max_tokens=500)
    enviados = modelo._default_params
    print(f"       construção aceita sem erro")
    print(f"       o que de fato vai para a API: "
          f"{ {k: v for k, v in enviados.items() if k != 'stream'} }")
    print(f"       atributo temperature no objeto: {getattr(modelo, 'temperature', None)!r}")

    print("  c) leitura: `max_tokens` foi traduzido para `max_completion_tokens`, "
          "e `temperature`\n     foi descartado. O código roda, e a temperatura "
          "que o programador\n     julgou ter definido nunca chegou ao modelo.")


def falha_3_json_que_nao_e_json() -> None:
    """Sem esquema declarado, o JSON é válido — e a forma dele depende do pedido.

    A falha que se descrevia em 2024 era o JSON sintaticamente quebrado, e ela
    praticamente desapareceu nos modelos atuais. A falha que restou é mais
    traiçoeira: o texto é JSON legítimo, o parser aceita sem reclamar, e as
    chaves não são as que o código seguinte espera. Este teste compara um
    pedido simples com um pedido ambíguo para mostrar onde a instabilidade
    de fato mora.
    """
    print("\n[3] Pedir JSON no prompt produz JSON — com a forma que o modelo quiser")
    modelo = init_chat_model(MODELO, model_provider="openai")

    casos = [
        ("pedido simples",
         "Extraia o número e a data do documento. Responda em JSON.",
         "OFÍCIO Nº OF-2026-0001, de 5 de janeiro de 2026, sobre licitação."),
        ("pedido ambíguo",
         "Extraia as informações relevantes do texto. Responda em JSON.",
         "OFÍCIO Nº OF-2026-0001, de 5 de janeiro de 2026, e MEMORANDO Nº "
         "MEM-2026-0002, de 7 de janeiro, ambos sobre a licitação do pregão 12/2026, "
         "no valor de R$ 40.000,00, com prazo até 20 de fevereiro."),
    ]

    for rotulo, instrucao, texto in casos:
        prompt = ChatPromptTemplate.from_messages([("system", instrucao), ("human", "{d}")])
        cadeia = prompt | modelo | JsonOutputParser()
        formas, invalidos = [], 0
        for _ in range(5):
            try:
                saida = cadeia.invoke({"d": texto})
                formas.append(tuple(sorted(saida.keys())) if isinstance(saida, dict)
                              else ("<lista, não objeto>",))
            except Exception:
                invalidos += 1
        print(f"  {rotulo}: {len(set(formas))} estrutura(s) distinta(s) em 5 execuções, "
              f"{invalidos} JSON inválido")
        for forma in sorted(set(formas)):
            print(f"       {formas.count(forma)}x  chaves: {list(forma)}")

    print("  leitura: o parser não reclamou nenhuma vez em nenhum dos dois casos.")
    print("  Quanto mais o pedido deixa a estrutura em aberto, mais a forma varia —")
    print("  e um código que leia saida['numero'] quebra longe da causa.")


def falha_4_prompt_invisivel() -> None:
    """A abstração esconde o que foi de fato enviado à API."""
    print("\n[4] O que a cadeia realmente envia")
    modelo = init_chat_model(MODELO, model_provider="openai")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você classifica documentos administrativos."),
        ("human", "Classifique: {documento}"),
    ])
    # `format_messages` revela o payload antes de ele sair pela rede, que é o
    # instrumento que devolve ao programador o controle sobre o que envia.
    mensagens = prompt.format_messages(documento="Ofício sobre licitação")
    for mensagem in mensagens:
        print(f"    {mensagem.type:9} → {mensagem.content!r}")

    sem_esquema = modelo.invoke(mensagens).usage_metadata["input_tokens"]

    from pydantic import BaseModel

    class Classificacao(BaseModel):
        categoria: str
        urgente: bool

    com_esquema = (
        modelo.with_structured_output(Classificacao, include_raw=True)
        .invoke(mensagens)["raw"].usage_metadata["input_tokens"]
    )
    print(f"    tokens de entrada sem esquema: {sem_esquema}")
    print(f"    tokens de entrada com esquema: {com_esquema} "
          f"(+{com_esquema - sem_esquema} que a abstração acrescenta)")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Defina OPENAI_API_KEY no arquivo .env da raiz do curso.")
    print("=" * 70)
    print("Quatro modos de falha do LangChain em 2026")
    print("=" * 70)
    falha_1_import_de_0x()
    falha_2_parametros_recusados()
    falha_3_json_que_nao_e_json()
    falha_4_prompt_invisivel()
    print()


if __name__ == "__main__":
    main()
