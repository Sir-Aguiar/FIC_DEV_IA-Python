"""Parte 3: o que o atendimento reteve e se isso excede a finalidade.

O atendimento roda com update_memory_on_run, que pede ao modelo um fato sobre
a pessoa a cada turno. Protocolo e situação não entram aqui: o que esta
rotina lê é a memória do framework e o texto bruto das tabelas do Agno. O
filtro de necessidade procura o dado pessoal desnecessário declarado no
roteiro. Um serviço real trocaria esse filtro por revisão humana, porque a
extração muda de uma execução para outra.
"""

import json
import sqlite3

from src.configuracao import ARQUIVO_TABELA_NECESSIDADE
from src.fabrica import caminho_do_banco, identificador_do_cidadao, montar_agente

NOME_BANCO = "memorias_titular"
TABELA_MEMORIAS = "agno_memories"
SESSAO_ATENDIMENTO = "atendimento_memorias"


def atender(roteiro: dict) -> None:
    """Percorre o roteiro gravando histórico e memórias de usuário.

    O histórico entra no contexto para o extrator ver o turno em que a
    cidadã falou a conta e o nome da mãe, e não só a última frase.
    """

    agente = montar_agente(
        NOME_BANCO,
        identificador_do_cidadao(roteiro["usuario"]),
        SESSAO_ATENDIMENTO,
        {
            "add_history_to_context": True,
            "num_history_runs": 100,
            "update_memory_on_run": True,
        },
    )
    for turno in roteiro["turnos"]:
        agente.run(turno["texto"])


def trechos_excedentes(roteiro: dict) -> list[str]:
    """Trechos do turno que não serve ao desbloqueio, vindos do próprio roteiro."""

    dado = roteiro["dado_desnecessario"]
    trechos = list(dado.get("trechos") or [])
    if dado["trecho"] not in trechos:
        trechos.insert(0, dado["trecho"])
    return trechos


def formas_do_identificador(cpf: str) -> list[str]:
    """O CPF como foi dito e só com os dígitos, para achar as duas grafias."""

    digitos = "".join(caractere for caractere in cpf if caractere.isdigit())
    formas = [cpf]
    if digitos and digitos not in formas:
        formas.append(digitos)
    return formas


def listar_tabelas(caminho) -> list[str]:
    conexao = sqlite3.connect(caminho)
    tabelas = [
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        )
    ]
    conexao.close()
    return tabelas


def ocorrencias(caminho, agulhas: list[str]) -> dict[str, int]:
    """Conta, em cada tabela, as linhas em que alguma agulha aparece.

    A varredura olha o registro inteiro, não uma coluna só. O identificador
    pode estar em user_id ou dentro do JSON da sessão, e o dado excedente
    pode ter sido copiado para a memória ou ter ficado só no turno bruto.
    """

    conexao = sqlite3.connect(caminho)
    encontrado = {}
    for tabela in listar_tabelas(caminho):
        try:
            linhas = conexao.execute(f'SELECT * FROM "{tabela}"').fetchall()
        except sqlite3.Error:
            continue
        total = sum(
            1 for linha in linhas if any(agulha in linha_legivel(linha) for agulha in agulhas)
        )
        if total:
            encontrado[tabela] = total
    conexao.close()
    return encontrado


def ler_memorias(caminho) -> list[str]:
    """Lê o texto de agno_memories. Lista vazia quando a extração não gravou nada."""

    if TABELA_MEMORIAS not in listar_tabelas(caminho):
        return []

    conexao = sqlite3.connect(caminho)
    linhas = conexao.execute(f'SELECT memory FROM "{TABELA_MEMORIAS}"').fetchall()
    conexao.close()
    return [texto_da_celula(linha[0]) for linha in linhas]


def texto_pesquisavel(valor) -> str:
    """Devolve o texto da célula com os escapes \\u00xx já resolvidos.

    O Agno grava parte do JSON da execução com unicode escapado. Sem essa
    leitura, o nome da mãe some da busca em agno_runs mesmo estando no turno.
    """

    if valor is None:
        return ""
    texto = valor.decode("utf-8", errors="replace") if isinstance(valor, bytes) else str(valor)
    try:
        carregado = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return texto
    return json.dumps(carregado, ensure_ascii=False)


def linha_legivel(linha) -> str:
    return " ".join(texto_pesquisavel(celula) for celula in linha)


def texto_da_celula(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except json.JSONDecodeError:
            return valor
    if isinstance(valor, dict):
        for chave in ("memory", "content", "text"):
            if isinstance(valor.get(chave), str):
                return valor[chave]
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)


def excede_finalidade(texto: str, trechos: list[str]) -> bool:
    """Verdadeiro quando o texto contém o dado pessoal desnecessário do roteiro.

    O critério é o trecho declarado no gabarito, comparado em minúsculas. Um
    serviço real trocaria este filtro por revisão humana: a frase extraída
    varia entre execuções e um filtro de substring não entende contexto.
    """

    minusculo = texto.lower()
    return any(trecho.lower() in minusculo for trecho in trechos)


def classificar(memorias: list[str], trechos: list[str]) -> list[dict]:
    return [
        {
            "texto": texto,
            "necessaria": not excede_finalidade(texto, trechos),
            "tabela": TABELA_MEMORIAS,
        }
        for texto in memorias
    ]


def redigir(resultado: dict) -> str:
    """Monta a tabela de necessidade com o que esta execução gravou."""

    linhas = [
        "# Necessidade do que ficou retido",
        "",
        "Atendimento do service desk da MTI com extração de memória ligada. "
        "A finalidade é desbloquear o acesso ao correio e ao SEI. Conta bancária "
        "e nome da mãe, ditos no turno 4, não servem a esse pedido.",
        "",
        "| Texto retido | Necessária ao atendimento | Tabela |",
        "| --- | --- | --- |",
    ]
    if not resultado["memorias"]:
        linhas.append("| Nenhuma memória extraída nesta execução | — | agno_memories |")
    for item in resultado["memorias"]:
        texto = " ".join(item["texto"].split()).replace("|", "/")
        necessaria = "sim" if item["necessaria"] else "não — excede a finalidade"
        linhas.append(f"| {texto} | {necessaria} | {item['tabela']} |")

    linhas.extend(["", "## Dado pessoal desnecessário", ""])
    if not resultado["por_trecho"]:
        linhas.append(
            "Nenhuma tabela desta execução contém os trechos do dado desnecessário do roteiro."
        )
    for trecho, tabelas in resultado["por_trecho"].items():
        no_texto = any(
            trecho.lower() in item["texto"].lower() and not item["necessaria"]
            for item in resultado["memorias"]
        )
        onde = ", ".join(f"`{tabela}` ({total})" for tabela, total in tabelas.items()) or "nenhuma tabela"
        destino = (
            "O texto extraído em `agno_memories` contém esse trecho."
            if no_texto
            else "O texto extraído não repetiu esse trecho; ele ficou no registro bruto."
        )
        linhas.append(f"- `{trecho}`: {destino} Tabelas: {onde}.")

    linhas.extend(["", "## Tabelas em que o identificador aparece", ""])
    if not resultado["tabelas_do_identificador"]:
        linhas.append("O CPF da cidadã não aparece em nenhuma tabela.")
    else:
        for tabela, total in resultado["tabelas_do_identificador"].items():
            linhas.append(f"- `{tabela}`: {total} registro(s)")

    linhas.extend(["", "## Tabelas do banco", ""])
    linhas.append(", ".join(f"`{tabela}`" for tabela in resultado["tabelas"]) or "nenhuma")
    linhas.append("")
    return "\n".join(linhas)


def examinar(roteiro: dict) -> dict:
    """Lê o banco do atendimento já gravado e grava a tabela de necessidade."""

    caminho = caminho_do_banco(NOME_BANCO)
    trechos = trechos_excedentes(roteiro)
    identificador = formas_do_identificador(roteiro["usuario"]["cpf"])
    memorias = classificar(ler_memorias(caminho), trechos)

    resultado = {
        "memorias": memorias,
        "trechos": trechos,
        "tabelas": listar_tabelas(caminho),
        "por_trecho": {trecho: ocorrencias(caminho, [trecho]) for trecho in trechos},
        "tabelas_do_identificador": ocorrencias(caminho, identificador),
    }
    ARQUIVO_TABELA_NECESSIDADE.parent.mkdir(exist_ok=True)
    ARQUIVO_TABELA_NECESSIDADE.write_text(redigir(resultado), encoding="utf-8")
    return resultado


def inspecionar(roteiro: dict) -> dict:
    """Roda o atendimento e, em seguida, lê o que ficou no SQLite.

    A extração é instável entre execuções. Quando agno_memories volta vazia,
    a varredura das outras tabelas continua: o turno bruto pode ter retido o
    dado mesmo sem um fato extraído.
    """

    atender(roteiro)
    return examinar(roteiro)
