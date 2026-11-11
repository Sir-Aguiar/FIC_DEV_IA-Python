# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Exemplo 06: Assistente de redação oficial com metadados
# Seção 8 – Assistente de redação oficial, ponta a ponta
# Requisitos: pip install langchain langchain-openai python-dotenv
# ============================================================
"""Reúne as peças da aula em um assistente que redige e cataloga documentos.

O assistente recebe o tipo de documento e os dados do caso, redige a peça com
o template adequado e devolve, na mesma execução, os metadados estruturados
que o setor de protocolo precisa para arquivá-la. As duas saídas vêm de
etapas distintas: a redação usa texto livre, e os metadados usam esquema
declarado, porque são eles que alimentam um sistema e não podem variar de
forma.
"""
import json
import pathlib
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

RAIZ = pathlib.Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = "gpt-5.6-luna"

# Cada tipo de documento tem exigências próprias de estrutura e de tratamento.
# Mantê-las em um dicionário, e não espalhadas em condicionais, é o que permite
# acrescentar um tipo novo sem tocar no restante do código.
FORMATOS = {
    "ofício": "Documento externo, dirigido a autoridade de outro órgão. Abre com "
              "vocativo, traz a exposição em parágrafos numerados e fecha com fecho "
              "de cortesia.",
    "memorando": "Comunicação interna entre setores do mesmo órgão. Dispensa "
                 "vocativo cerimonioso e vai direto ao assunto.",
    "despacho": "Ato decisório lavrado no próprio processo. Expõe o fundamento e "
                "conclui com a determinação, em voz ativa.",
}


class Metadados(BaseModel):
    """Os campos que o setor de protocolo precisa para arquivar a peça."""

    tipo: Literal["ofício", "memorando", "despacho"]
    destinatario: str = Field(description="Órgão ou setor a que se dirige")
    assunto: str = Field(description="Assunto em até dez palavras")
    prioridade: Literal["alta", "media", "baixa"]
    exige_resposta: bool = Field(description="Se o documento pede manifestação do destinatário")


class AssistenteRedacao:
    """Redige o documento e extrai os metadados de arquivamento."""

    def __init__(self, modelo: str = MODELO) -> None:
        self.modelo = init_chat_model(modelo, model_provider="openai")

        self.redator = ChatPromptTemplate.from_messages([
            ("system", "Você redige documentos oficiais do Governo de Mato Grosso em "
                       "registro formal. {formato} Não deixe lacunas entre colchetes: "
                       "use apenas os dados fornecidos e, se algum faltar, redija de "
                       "modo que a ausência não apareça."),
            ("human", "Tipo: {tipo}\nDestinatário: {destinatario}\nDados do caso: {dados}"),
        ]) | self.modelo | StrOutputParser()

        self.catalogador = ChatPromptTemplate.from_messages([
            ("system", "Extraia os metadados de arquivamento do documento abaixo."),
            ("human", "{documento}"),
        ]) | self.modelo.with_structured_output(Metadados)

    def redigir(self, tipo: str, destinatario: str, dados: str) -> tuple[str, Metadados]:
        if tipo not in FORMATOS:
            raise ValueError(f"Tipo não previsto: {tipo}. Use um de {list(FORMATOS)}.")
        documento = self.redator.invoke({
            "formato": FORMATOS[tipo], "tipo": tipo,
            "destinatario": destinatario, "dados": dados,
        })
        metadados = self.catalogador.invoke({"documento": documento})
        return documento, metadados


def main() -> None:
    assistente = AssistenteRedacao()
    casos = [
        ("ofício", "Prefeitura Municipal de Sinop",
         "Prorrogação por 90 dias do prazo de execução do convênio 12/2026, "
         "solicitada em razão do período chuvoso. Resposta necessária em 15 dias."),
        ("despacho", "Coordenadoria de Recursos Humanos",
         "Indeferimento de pedido de licença-prêmio por não cumprimento do "
         "interstício de cinco anos, conforme o estatuto do servidor."),
    ]

    for tipo, destinatario, dados in casos:
        documento, metadados = assistente.redigir(tipo, destinatario, dados)
        print(f"\n{'=' * 68}\n{tipo.upper()} → {destinatario}\n{'=' * 68}")
        print(documento.strip()[:520])
        print(f"\n  metadados: {json.dumps(metadados.model_dump(), ensure_ascii=False)}")
        # Uma conferência barata que evita arquivar peça com lacuna por preencher.
        if "[" in documento:
            print("  ATENÇÃO: o documento contém lacuna entre colchetes e precisa de revisão.")


if __name__ == "__main__":
    main()
