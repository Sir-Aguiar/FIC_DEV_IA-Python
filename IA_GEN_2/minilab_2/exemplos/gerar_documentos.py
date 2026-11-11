# ============================================================
# Aula 02 – Introdução ao LangChain
# Módulo: Agentes Autônomos | Curso: Formação em IA – UNEMAT/RISC
# Apoio: gera o conjunto de avaliação usado no experimento da Seção 6
# Seção 6 – O framework compensa? Uma medição contra o SDK cru
# Requisitos: nenhum (biblioteca padrão)
# ============================================================
"""Gera `documentos_2026.jsonl` com 20 documentos administrativos fictícios.

Cada linha traz o texto do documento e o gabarito dos seis campos que o
experimento da Seção 6 precisa extrair. Os documentos são fictícios, mas a
redação imita a variação real do expediente público: a data aparece por
extenso em alguns e em formato numérico em outros, o valor às vezes vem
grafado por extenso, e cinco documentos não têm valor algum. É essa variação
que torna a extração um problema de verdade, e não um exercício de recorte.
"""
import json
import pathlib

# Cada tupla descreve um documento: (tipo, numero, data_texto, data_iso,
# valor_texto, valor, partes, objeto, prioridade, corpo).
# O gabarito é escrito à mão junto com o texto, de modo que não há dúvida
# sobre qual é a resposta correta de cada campo.
DOCUMENTOS = [
    ("Ofício", "OF-SEPLAG-2026-0142", "15 de março de 2026", "2026-03-15",
     "R$ 125.000,00", 125000.00,
     ["Secretaria de Estado de Planejamento e Gestão", "Prefeitura de Sinop"],
     "Repasse para modernização do parque tecnológico da unidade de atendimento",
     "alta",
     "Senhor Prefeito, encaminho a Vossa Excelência a proposta de repasse no valor de "
     "R$ 125.000,00 destinada à modernização do parque tecnológico da unidade de "
     "atendimento ao cidadão. O prazo para manifestação encerra-se em 30 de março de "
     "2026, motivo pelo qual classificamos a matéria como de alta prioridade."),

    ("Memorando", "MEM-SEFAZ-2026-0087", "03/02/2026", "2026-02-03",
     None, None,
     ["Coordenadoria de Arrecadação", "Gerência de Tecnologia da Informação"],
     "Solicitação de acesso ao painel de indicadores de arrecadação",
     "media",
     "Solicito a essa Gerência a concessão de acesso de leitura ao painel de "
     "indicadores de arrecadação para dois servidores desta Coordenadoria. O acesso "
     "destina-se ao acompanhamento mensal das metas e não implica manipulação de "
     "dados. Permanecemos à disposição para os esclarecimentos necessários."),

    ("Despacho", "DESP-PGE-2026-0311", "22 de janeiro de 2026", "2026-01-22",
     "R$ 47.320,85", 47320.85,
     ["Procuradoria-Geral do Estado", "Construtora Vale Verde Ltda."],
     "Manifestação sobre pedido de reequilíbrio econômico-financeiro contratual",
     "alta",
     "Trata-se de pedido de reequilíbrio econômico-financeiro formulado pela "
     "contratada, no montante de R$ 47.320,85. A análise preliminar indica que a "
     "documentação apresentada atende ao disposto na Lei nº 14.133/2021. Encaminhe-se "
     "à Procuradoria Fiscal para parecer conclusivo no prazo de dez dias."),

    ("Requerimento", "REQ-SEDUC-2026-1904", "08/04/2026", "2026-04-08",
     None, None,
     ["Escola Estadual Rui Barbosa", "Superintendência de Gestão Escolar"],
     "Pedido de recomposição do quadro de professores para o segundo semestre",
     "alta",
     "A direção desta unidade escolar requer a recomposição do quadro docente para o "
     "segundo semestre letivo, tendo em vista a aposentadoria de três professores e o "
     "afastamento de outro por licença médica. A ausência de reposição compromete o "
     "cumprimento da carga horária mínima prevista em lei."),

    ("Ofício", "OF-SEMA-2026-0523", "17 de maio de 2026", "2026-05-17",
     "R$ 8.750,00", 8750.00,
     ["Secretaria de Estado de Meio Ambiente", "Instituto Água Viva"],
     "Termo de fomento para projeto de educação ambiental em escolas rurais",
     "media",
     "Comunicamos a aprovação do termo de fomento no valor de R$ 8.750,00 para "
     "execução do projeto de educação ambiental em escolas da zona rural. A prestação "
     "de contas deverá ser apresentada em até sessenta dias após o encerramento das "
     "atividades. A liberação dos recursos fica condicionada à assinatura do termo."),

    ("Nota Técnica", "NT-SECITECI-2026-0034", "29/06/2026", "2026-06-29",
     "R$ 312.400,00", 312400.00,
     ["Secretaria de Ciência e Tecnologia", "Comissão Permanente de Licitação"],
     "Análise de viabilidade para contratação de solução de armazenamento em nuvem",
     "media",
     "A presente nota examina a viabilidade técnica e econômica da contratação de "
     "solução de armazenamento em nuvem, estimada em R$ 312.400,00 para o período de "
     "vinte e quatro meses. O estudo comparou três arranjos possíveis e recomenda o "
     "modelo híbrido. A decisão final compete à autoridade competente."),

    ("Memorando", "MEM-SEPLAG-2026-0221", "11 de julho de 2026", "2026-07-11",
     None, None,
     ["Gerência de Recursos Humanos", "Todas as Coordenadorias"],
     "Orientação sobre o cronograma de avaliação de desempenho",
     "baixa",
     "Informamos que o ciclo de avaliação de desempenho terá início em primeiro de "
     "agosto e se estenderá até trinta de setembro. Cada chefia imediata deverá "
     "registrar as avaliações no sistema dentro do período indicado. O descumprimento "
     "do prazo impede a progressão funcional do servidor avaliado."),

    ("Despacho", "DESP-SEINFRA-2026-0778", "05/08/2026", "2026-08-05",
     "R$ 1.240.000,00", 1240000.00,
     ["Secretaria de Infraestrutura", "Consórcio Rodovias do Norte"],
     "Autorização para início da segunda etapa das obras de pavimentação",
     "alta",
     "Autorizo o início da segunda etapa das obras de pavimentação, no valor "
     "empenhado de R$ 1.240.000,00. A fiscalização deverá emitir relatório quinzenal "
     "de acompanhamento físico-financeiro. Qualquer alteração de projeto depende de "
     "aprovação prévia desta Secretaria."),

    ("Ofício", "OF-SES-2026-0092", "19 de fevereiro de 2026", "2026-02-19",
     "R$ 63.500,00", 63500.00,
     ["Secretaria de Estado de Saúde", "Hospital Regional de Cáceres"],
     "Repasse emergencial para aquisição de insumos hospitalares",
     "alta",
     "Encaminhamos a autorização de repasse emergencial no valor de R$ 63.500,00 "
     "destinado à aquisição de insumos hospitalares de uso contínuo. O repasse decorre "
     "da situação de desabastecimento relatada por essa unidade. A prestação de contas "
     "seguirá o rito simplificado previsto para despesas emergenciais."),

    ("Requerimento", "REQ-SEJUSP-2026-0455", "27/03/2026", "2026-03-27",
     None, None,
     ["Delegacia Regional de Rondonópolis", "Coordenadoria de Logística"],
     "Solicitação de renovação da frota de viaturas da unidade",
     "media",
     "Requeremos a inclusão desta unidade no cronograma de renovação da frota, tendo "
     "em vista que quatro das seis viaturas ultrapassaram duzentos mil quilômetros "
     "rodados. A manutenção corretiva tem consumido parcela crescente do orçamento "
     "local. Anexamos o relatório de custos dos últimos doze meses."),

    ("Nota Técnica", "NT-SEFAZ-2026-0118", "14 de abril de 2026", "2026-04-14",
     "R$ 89.900,00", 89900.00,
     ["Gerência de Tecnologia da Informação", "Coordenadoria de Contratos"],
     "Parecer sobre renovação do contrato de suporte ao sistema de protocolo",
     "media",
     "Analisamos a proposta de renovação do contrato de suporte ao sistema de "
     "protocolo, no valor anual de R$ 89.900,00. O histórico de atendimento registra "
     "cumprimento integral dos níveis de serviço pactuados. Recomendamos a renovação "
     "por mais doze meses, com reajuste limitado ao índice contratual."),

    ("Ofício", "OF-SETAS-2026-0267", "02/09/2026", "2026-09-02",
     "R$ 21.150,00", 21150.00,
     ["Secretaria de Assistência Social", "Centro de Referência de Várzea Grande"],
     "Custeio de oficinas de qualificação profissional para jovens",
     "media",
     "Comunicamos a liberação de R$ 21.150,00 para custeio das oficinas de "
     "qualificação profissional destinadas a jovens em situação de vulnerabilidade. "
     "As turmas deverão iniciar em até trinta dias da liberação. O relatório de "
     "execução é condição para novos repasses."),

    ("Memorando", "MEM-PGE-2026-0143", "23 de maio de 2026", "2026-05-23",
     None, None,
     ["Procuradoria Fiscal", "Procuradoria Administrativa"],
     "Encaminhamento de estudo sobre prescrição intercorrente em execuções fiscais",
     "baixa",
     "Encaminhamos o estudo elaborado por esta Procuradoria acerca da prescrição "
     "intercorrente em execuções fiscais estaduais. O documento sistematiza a "
     "jurisprudência consolidada e propõe uniformização de entendimento interno. "
     "Sugerimos a inclusão do tema na pauta da próxima reunião de coordenadores."),

    ("Despacho", "DESP-SEDUC-2026-2011", "31/07/2026", "2026-07-31",
     "R$ 476.800,00", 476800.00,
     ["Secretaria de Estado de Educação", "Comissão de Licitação"],
     "Homologação do resultado do pregão para aquisição de material escolar",
     "alta",
     "Homologo o resultado do certame para aquisição de material escolar, no valor "
     "total de R$ 476.800,00. A adjudicação recai sobre a proposta classificada em "
     "primeiro lugar, que atendeu integralmente ao edital. Publique-se e proceda-se à "
     "convocação para assinatura do contrato."),

    ("Ofício", "OF-SEMA-2026-0611", "09 de junho de 2026", "2026-06-09",
     None, None,
     ["Secretaria de Estado de Meio Ambiente", "Ministério Público Estadual"],
     "Resposta a requisição sobre licenciamento de empreendimento minerário",
     "alta",
     "Em resposta à requisição dessa Promotoria, informamos que o processo de "
     "licenciamento encontra-se em fase de análise técnica. A documentação apresentada "
     "pelo empreendedor está incompleta quanto ao estudo de impacto sobre recursos "
     "hídricos. Foi concedido prazo de quinze dias para complementação."),

    ("Requerimento", "REQ-SECITECI-2026-0088", "18/01/2026", "2026-01-18",
     "R$ 15.600,00", 15600.00,
     ["Coordenadoria de Inovação", "Gerência de Compras"],
     "Aquisição de licenças de software para o laboratório de dados",
     "baixa",
     "Requeremos a aquisição de doze licenças anuais de software estatístico para o "
     "laboratório de dados, no valor estimado de R$ 15.600,00. As licenças atuais "
     "expiram em dezembro deste ano. A ausência de renovação interrompe os projetos de "
     "pesquisa em andamento."),

    ("Nota Técnica", "NT-SEINFRA-2026-0205", "26 de agosto de 2026", "2026-08-26",
     "R$ 2.980.000,00", 2980000.00,
     ["Superintendência de Obras", "Secretaria de Planejamento"],
     "Estudo de custo para duplicação de trecho rodoviário estadual",
     "media",
     "O estudo estima em R$ 2.980.000,00 o custo de duplicação do trecho rodoviário "
     "de doze quilômetros entre os municípios indicados. O valor considera terraplenagem, "
     "pavimentação e sinalização, sem incluir desapropriações. A execução depende de "
     "previsão na lei orçamentária do exercício seguinte."),

    ("Memorando", "MEM-SES-2026-0330", "13/10/2026", "2026-10-13",
     "R$ 5.400,00", 5400.00,
     ["Coordenadoria de Vigilância Sanitária", "Gerência Administrativa"],
     "Custeio de diárias para ação de fiscalização em municípios do interior",
     "baixa",
     "Solicitamos o custeio de diárias no montante de R$ 5.400,00 para equipe de "
     "quatro fiscais em ação programada de vigilância sanitária. A ação abrange seis "
     "municípios ao longo de cinco dias úteis. O roteiro detalhado segue em anexo."),

    ("Despacho", "DESP-SEPLAG-2026-0499", "07 de novembro de 2026", "2026-11-07",
     None, None,
     ["Secretaria de Planejamento e Gestão", "Comitê de Governança Digital"],
     "Determinação de revisão da política de uso de inteligência artificial",
     "alta",
     "Determino a revisão da política interna de uso de ferramentas de inteligência "
     "artificial, à luz das obrigações da Lei Geral de Proteção de Dados. O comitê "
     "deverá apresentar minuta revisada em até quarenta e cinco dias. Fica vedado, até "
     "a conclusão, o envio de dados pessoais a serviços externos não homologados."),

    ("Ofício", "OF-SEJUSP-2026-0714", "21/12/2026", "2026-12-21",
     "R$ 158.000,00", 158000.00,
     ["Secretaria de Segurança Pública", "Prefeitura de Barra do Garças"],
     "Convênio para instalação de sistema de videomonitoramento urbano",
     "media",
     "Encaminhamos a minuta de convênio para instalação de sistema de "
     "videomonitoramento urbano, no valor de R$ 158.000,00, com contrapartida "
     "municipal de vinte por cento. A vigência proposta é de dezoito meses contados "
     "da assinatura. A minuta já recebeu parecer favorável da assessoria jurídica."),
]


def montar(doc: tuple) -> dict:
    """Monta o registro com o texto do documento e o gabarito dos seis campos."""
    tipo, numero, data_texto, data_iso, _valor_texto, valor, partes, objeto, prioridade, corpo = doc
    texto = (
        f"{tipo.upper()} Nº {numero}\n"
        f"Cuiabá, {data_texto}.\n\n"
        f"De: {partes[0]}\n"
        f"Para: {partes[1]}\n\n"
        f"Assunto: {objeto}.\n\n"
        f"{corpo}\n\n"
        "Atenciosamente,\n"
        "Chefia da Unidade"
    )
    return {
        "id": numero,
        "texto": texto,
        "gabarito": {
            "numero": numero,
            "data": data_iso,
            "valor": valor,
            "partes": partes,
            "objeto": objeto,
            "prioridade": prioridade,
        },
    }


def main() -> None:
    destino = pathlib.Path(__file__).parent / "documentos_2026.jsonl"
    registros = [montar(d) for d in DOCUMENTOS]
    with destino.open("w", encoding="utf-8") as saida:
        for registro in registros:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    com_valor = sum(1 for r in registros if r["gabarito"]["valor"] is not None)
    print(f"{len(registros)} documentos gravados em {destino.name}")
    print(f"{len(registros) * 6} campos no gabarito, dos quais {len(registros) - com_valor} com valor nulo")


if __name__ == "__main__":
    main()
