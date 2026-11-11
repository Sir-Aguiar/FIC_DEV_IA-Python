# ============================================================
# Aula 03 – Um Agente LangChain com Acesso a Ferramentas
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Apoio: as três ferramentas do assistente jurídico, usadas por vários exemplos
# Seção 2 – Três formas de declarar uma ferramenta em 1.x
# Requisitos: pip install langchain python-dateutil
# ============================================================
"""As ferramentas do assistente jurídico da Procuradoria-Geral do Estado.

Cada uma exemplifica uma forma diferente de declaração, e as três são
importadas pelos demais exemplos da aula. A base de legislação é local e
fictícia, o que mantém os exemplos executáveis sem depender de serviço
externo e sem introduzir a variabilidade de uma busca na web.
"""
import json
import pathlib
from datetime import date, timedelta
from typing import Optional

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field

BASE = pathlib.Path(__file__).parent / "legislacao_mt.json"

# Índices do Decreto Estadual nº 987/2023 (fictício), fixados para que o
# resultado do cálculo seja reproduzível em qualquer execução.
IPCA_MENSAL = 0.0042
JUROS_MENSAL = 0.01
MULTA = 0.02


# --- Forma 1: o decorador @tool sobre uma função anotada ---------------
@tool
def buscar_legislacao(assunto: str) -> str:
    """Busca normas estaduais e federais por assunto na base da Procuradoria.

    Use para localizar a norma aplicável a um tema, como licitação, dados
    pessoais, prazo de processo administrativo ou atualização de débito.
    Devolve o título da norma, a ementa e os artigos pertinentes.
    """
    dados = json.loads(BASE.read_text(encoding="utf-8"))
    termo = assunto.lower().strip()
    achados = []
    for norma in dados["normas"]:
        alvo = " ".join(norma["assuntos"]) + " " + norma["ementa"].lower()
        if any(palavra in alvo for palavra in termo.split() if len(palavra) > 3):
            artigos = "; ".join(f"Art. {n}: {t}" for n, t in norma["artigos"].items())
            achados.append(f"{norma['titulo']} — {norma['ementa']} {artigos}")
    if not achados:
        return f"Nenhuma norma encontrada para o assunto '{assunto}'."
    return "\n\n".join(achados[:2])


# --- Forma 2: função anotada, sem decorador, convertida na criação -----
def calcular_prazo(data_inicial: str, dias: int, uteis: bool = True) -> str:
    """Calcula a data final de um prazo em dias úteis ou corridos.

    A data inicial deve vir no formato AAAA-MM-DD. Use `uteis=True` para
    prazos processuais e `uteis=False` para prazos contratuais em dias
    corridos. Não considera feriados estaduais.
    """
    try:
        inicio = date.fromisoformat(data_inicial)
    except ValueError:
        return f"Data inválida: '{data_inicial}'. Use o formato AAAA-MM-DD."
    if not uteis:
        fim = inicio + timedelta(days=dias)
        return f"Prazo de {dias} dias corridos a partir de {data_inicial}: vence em {fim.isoformat()}."
    atual, restantes = inicio, dias
    while restantes > 0:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            restantes -= 1
    return (f"Prazo de {dias} dias úteis a partir de {data_inicial}: vence em "
            f"{atual.isoformat()} (feriados não considerados).")


# --- Forma 3: StructuredTool com esquema Pydantic explícito -----------
class AtualizacaoDebito(BaseModel):
    """Argumentos do cálculo de atualização de débito com a Fazenda Estadual."""

    valor_principal: float = Field(description="Valor original do débito, em reais")
    meses_atraso: int = Field(description="Número de meses inteiros de atraso")
    aplicar_multa: bool = Field(default=True, description="Se incide a multa de mora de 2%")


def _atualizar_debito(valor_principal: float, meses_atraso: int,
                      aplicar_multa: bool = True) -> str:
    if valor_principal <= 0 or meses_atraso < 0:
        return "Valores inválidos: o principal deve ser positivo e o atraso não negativo."
    corrigido = valor_principal * ((1 + IPCA_MENSAL) ** meses_atraso)
    juros = corrigido * JUROS_MENSAL * meses_atraso
    multa = corrigido * MULTA if aplicar_multa else 0.0
    total = corrigido + juros + multa
    return (f"Principal R$ {valor_principal:,.2f} · corrigido R$ {corrigido:,.2f} · "
            f"juros R$ {juros:,.2f} · multa R$ {multa:,.2f} · "
            f"TOTAL R$ {total:,.2f} (Decreto Estadual nº 987/2023, arts. 2º, 3º e 6º)")


calcular_atualizacao_debito = StructuredTool.from_function(
    func=_atualizar_debito,
    name="calcular_atualizacao_debito",
    description=("Calcula a atualização monetária de um débito com a Fazenda Estadual, "
                 "aplicando IPCA, juros de mora de 1% ao mês e multa de 2%. Use apenas "
                 "quando o valor principal e o número de meses de atraso forem "
                 "informados explicitamente."),
    args_schema=AtualizacaoDebito,
)

# A conversão da forma 2 acontece aqui, na montagem da lista.
FERRAMENTAS = [buscar_legislacao, tool(calcular_prazo), calcular_atualizacao_debito]


if __name__ == "__main__":
    for ferramenta in FERRAMENTAS:
        print(f"\n{ferramenta.name}")
        print(f"  descrição: {ferramenta.description.splitlines()[0]}")
        print(f"  esquema  : {json.dumps(ferramenta.args, ensure_ascii=False)}")
