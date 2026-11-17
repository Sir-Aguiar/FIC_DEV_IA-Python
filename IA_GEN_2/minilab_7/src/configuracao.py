"""O que os módulos do Mini LAB compartilham: modelo, preços, caminhos e instrução.

Preço e modelo ficam só aqui. Os experimentos importam estas constantes em vez
de repetir o identificador do modelo dentro de cada medição.
"""

import pathlib

from dotenv import load_dotenv

RAIZ = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

# Mesmo modelo e os mesmos preços por milhão de tokens da Seção 3 da aula.
# reasoning_effort fica em "none" para a medição refletir o atendimento, e não
# um raciocínio extra que mudaria a conta de saída a cada turno.
MODELO = "gpt-5.6-luna"
REASONING_EFFORT = "none"
USD_ENTRADA = 0.20
USD_SAIDA = 1.20

PASTA_BANCOS = RAIZ / "bancos"
PASTA_DADOS = RAIZ / "dados"
PASTA_RESULTADOS = RAIZ / "resultados"
ARQUIVO_ROTEIRO = PASTA_DADOS / "roteiro_atendimento.json"
ARQUIVO_RESULTADO_MEMORIA = PASTA_RESULTADOS / "resultado_memoria.json"
ARQUIVO_TABELA_NECESSIDADE = PASTA_RESULTADOS / "tabela_necessidade.md"
ARQUIVO_ELIMINACAO = PASTA_RESULTADOS / "eliminacao.md"
ARQUIVO_VAZAMENTO = PASTA_RESULTADOS / "vazamento.md"

# Parte 2: o atendente usa o que a pessoa já disse nesta conversa. Sem essa
# instrução, uma configuração com histórico ainda pode pedir de novo o login.
INSTRUCAO = (
    "Você atende servidores no service desk da MTI, a Empresa Mato-grossense "
    "de Tecnologia da Informação, em pedidos de acesso aos sistemas do Estado "
    "de Mato Grosso. Seja objetivo e cordial. Use as informações que a pessoa "
    "já forneceu nesta conversa em vez de pedi-las de novo."
)
