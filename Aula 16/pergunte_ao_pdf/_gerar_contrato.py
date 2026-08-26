"""Gera pdfs/contrato_consultoria.pdf com texto em WinAnsi (acentos)."""
from pathlib import Path

PAGINAS = [
    [
        "CONTRATO DE PRESTACAO DE SERVICOS DE CONSULTORIA",
        "Contrato n. 2024/087",
        "",
        "Pelo presente instrumento particular, de um lado TECH SOLUCOES LTDA,",
        "inscrita no CNPJ sob o n. 12.345.678/0001-90, com sede na Rua das",
        "Palmeiras, 100, Sao Paulo/SP, doravante denominada CONTRATANTE, e de",
        "outro lado CONSULTORIA ALFA LTDA, inscrita no CNPJ sob o n.",
        "98.765.432/0001-10, com sede na Avenida Atlantica, 500, Rio de",
        "Janeiro/RJ, doravante denominada CONTRATADA, tem entre si justo e",
        "contratado o seguinte.",
        "",
        "CLAUSULA PRIMEIRA - DAS PARTES",
        "As partes declaram possuir plena capacidade para celebrar o presente",
        "contrato e assumir as obrigacoes nele previstas. Qualquer alteracao",
        "de endereco devera ser comunicada por escrito no prazo de 10 dias.",
        "",
        "CLAUSULA SEGUNDA - DO OBJETO",
        "O objeto deste contrato e a prestacao de servicos de consultoria em",
        "tecnologia da informacao, incluindo diagnostico de processos,",
        "elaboracao de relatorios tecnicos, capacitacao de equipes e apoio a",
        "implantacao de sistemas de gestao. A CONTRATADA devera executar os",
        "servicos com diligencia, observando as normas tecnicas aplicaveis e",
        "as orientacoes da CONTRATANTE. Os entregaveis incluem relatorio de",
        "diagnostico, plano de acao trimestral e workshops de capacitacao.",
    ],
    [
        "CLAUSULA TERCEIRA - DA VIGENCIA",
        "O presente contrato tem vigencia de 12 (doze) meses, contados a",
        "partir da data de assinatura, podendo ser prorrogado por iguais",
        "periodos mediante aditivo escrito assinado pelas partes.",
        "A vigencia inicia-se na data da ultima assinatura e encerra-se",
        "automaticamente ao termino do prazo, salvo renovacao expressa.",
        "Paragrafo primeiro. A prorrogacao nao e automatica. Qualquer das",
        "partes devera manifestar interesse com antecedencia minima de 60",
        "(sessenta) dias do termino.",
        "Paragrafo segundo. Em caso de prorrogacao, os valores poderao ser",
        "reajustados pelo IPCA acumulado no periodo, limitado a 10% ao ano.",
        "A data de assinatura prevista e 1 de marco de 2024, com termino em",
        "28 de fevereiro de 2025, salvo prorrogacao. O prazo de 12 meses e",
        "essencial para o planejamento orcamentario da CONTRATANTE.",
    ],
    [
        "CLAUSULA QUARTA - DO VALOR E DO PAGAMENTO",
        "O valor total do contrato e de R$ 120.000,00 (cento e vinte mil",
        "reais), pagos em doze parcelas mensais iguais de R$ 10.000,00.",
        "O pagamento sera realizado ate o quinto dia util de cada mes,",
        "mediante nota fiscal emitida pela CONTRATADA, desde que os servicos",
        "do mes anterior tenham sido atestados pela CONTRATANTE.",
        "Paragrafo primeiro. A nota fiscal devera ser enviada com",
        "antecedencia minima de 5 (cinco) dias uteis da data de vencimento,",
        "acompanhada do relatorio de atividades do periodo.",
        "Paragrafo segundo. Nao havera reajuste no primeiro ano de vigencia.",
        "Despesas de viagem somente serao reembolsadas se pre-aprovadas por",
        "escrito e comprovadas por documentos fiscais.",
        "O valor contempla todos os tributos, encargos e custos da CONTRATADA.",
    ],
    [
        "CLAUSULA QUINTA - DAS OBRIGACOES DA CONTRATADA",
        "Sao obrigacoes da CONTRATADA: prestar os servicos com qualidade",
        "tecnica; indicar um coordenador responsavel; cumprir os prazos do",
        "plano de trabalho; guardar sigilo sobre informacoes da CONTRATANTE;",
        "e substituir profissionais que nao atendam ao perfil acordado.",
        "A CONTRATADA nao podera subcontratar a totalidade dos servicos.",
        "A responsabilidade perante a CONTRATANTE permanece com a CONTRATADA.",
        "",
        "CLAUSULA SEXTA - DAS OBRIGACOES DA CONTRATANTE",
        "Sao obrigacoes da CONTRATANTE: fornecer informacoes e acessos",
        "necessarios; designar um gestor do contrato; atestar os servicos;",
        "efetuar os pagamentos nos prazos previstos; e comunicar mudancas de",
        "escopo. A CONTRATANTE disponibilizara ambiente de trabalho remoto ou",
        "presencial, conforme combinado, e acesso aos sistemas necessarios.",
    ],
    [
        "CLAUSULA SETIMA - DO ATRASO E DAS PENALIDADES",
        "Em caso de atraso no pagamento, incidirao juros de mora de 1% ao mes",
        "e multa de 2% sobre o valor da parcela em atraso. O atraso superior",
        "a 30 (trinta) dias autoriza a CONTRATADA a suspender os servicos,",
        "mediante notificacao previa de 5 (cinco) dias uteis, sem prejuizo da",
        "cobranca do debito e das penalidades.",
        "Paragrafo primeiro. A suspensao nao caracteriza rescisao automatica.",
        "Os servicos serao retomados em ate 3 dias uteis apos a quitacao.",
        "Paragrafo segundo. Atraso da CONTRATADA na entrega de relatorios,",
        "por culpa exclusiva sua, sujeita-a a multa de 0,5% do valor mensal",
        "por dia de atraso, limitada a 10% da parcela do mes.",
    ],
    [
        "CLAUSULA DECIMA - DA RESCISAO",
        "O presente contrato podera ser rescindido por qualquer das partes",
        "mediante notificacao escrita com antecedencia minima de 30 (trinta)",
        "dias. Em caso de rescisao imotivada pela CONTRATANTE antes do",
        "termino do prazo contratual, esta pagara a CONTRATADA multa",
        "equivalente a 20% do valor total remanescente do contrato.",
        "Paragrafo primeiro. Constitui justa causa para rescisao imediata:",
        "inadimplemento nao sanado em 15 dias; falencia ou dissolucao;",
        "violacao grave de confidencialidade; pratica de ato ilicito.",
        "Paragrafo segundo. Na rescisao por justa causa imputavel a",
        "CONTRATADA, nao sera devida a multa de 20% prevista no caput.",
        "Apos a rescisao, a CONTRATADA devolvera acessos e documentos em ate",
        "10 dias uteis e entregara relatorio de transicao.",
    ],
    [
        "CLAUSULA OITAVA - DA CONFIDENCIALIDADE",
        "Todas as informacoes tecnicas, comerciais, financeiras e",
        "estrategicas trocadas entre as partes sao confidenciais. E vedado",
        "divulgar, copiar ou utilizar tais informacoes para finalidade diversa",
        "da execucao deste contrato, durante a vigencia e por 24 (vinte e",
        "quatro) meses apos o encerramento, salvo obrigacao legal.",
        "A violacao desta clausula autoriza a rescisao por justa causa e a",
        "busca de perdas e danos.",
        "",
        "CLAUSULA NONA - DA PROPRIEDADE INTELECTUAL",
        "Os relatorios e materiais produzidos exclusivamente para a",
        "CONTRATANTE serao de titularidade da CONTRATANTE apos o pagamento.",
        "Ferramentas e know-how preexistentes da CONTRATADA permanecem de sua",
        "titularidade, com licenca de uso limitada ao objeto contratual.",
    ],
    [
        "CLAUSULA DECIMA PRIMEIRA - DO FORO",
        "Fica eleito o foro da Comarca de Sao Paulo/SP para dirimir quaisquer",
        "controversias oriundas deste contrato, com renuncia a qualquer outro.",
        "Antes de qualquer medida judicial, as partes envidarao esforcos para",
        "solucao amigavel no prazo de 15 dias uteis.",
        "",
        "CLAUSULA DECIMA SEGUNDA - DAS DISPOSICOES GERAIS",
        "Este contrato constitui o acordo integral entre as partes. Alteracoes",
        "somente serao validas por escrito. A tolerancia quanto ao",
        "descumprimento de qualquer clausula nao implicara novacao.",
        "Sao Paulo, 1 de marco de 2024.",
        "CONTRATANTE: TECH SOLUCOES LTDA",
        "CONTRATADA: CONSULTORIA ALFA LTDA",
    ],
]


# Texto final com acentos (cp1252 / WinAnsi)
PAGINAS[0][0] = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE CONSULTORIA"
PAGINAS[0][3] = "Pelo presente instrumento particular, de um lado TECH SOLUÇÕES LTDA,"
PAGINAS[0][5] = "Palmeiras, 100, São Paulo/SP, doravante denominada CONTRATANTE, e de"
PAGINAS[0][7] = "98.765.432/0001-10, com sede na Avenida Atlântica, 500, Rio de"
PAGINAS[0][11] = "CLÁUSULA PRIMEIRA - DAS PARTES"
PAGINAS[0][13] = "contrato e assumir as obrigações nele previstas. Qualquer alteração"
PAGINAS[0][14] = "de endereço deverá ser comunicada por escrito no prazo de 10 dias."
PAGINAS[0][16] = "CLÁUSULA SEGUNDA - DO OBJETO"
PAGINAS[0][17] = "O objeto deste contrato é a prestação de serviços de consultoria em"
PAGINAS[0][18] = "tecnologia da informação, incluindo diagnóstico de processos,"
PAGINAS[0][19] = "elaboração de relatórios técnicos, capacitação de equipes e apoio à"
PAGINAS[0][20] = "implantação de sistemas de gestão. A CONTRATADA deverá executar os"
PAGINAS[0][21] = "serviços com diligência, observando as normas técnicas aplicáveis e"
PAGINAS[0][22] = "as orientações da CONTRATANTE. Os entregáveis incluem relatório de"
PAGINAS[0][23] = "diagnóstico, plano de ação trimestral e workshops de capacitação."

PAGINAS[1][0] = "CLÁUSULA TERCEIRA - DA VIGÊNCIA"
PAGINAS[1][1] = "O presente contrato tem vigência de 12 (doze) meses, contados a"
PAGINAS[1][3] = "períodos mediante aditivo escrito assinado pelas partes."
PAGINAS[1][4] = "A vigência inicia-se na data da última assinatura e encerra-se"
PAGINAS[1][5] = "automaticamente ao término do prazo, salvo renovação expressa."
PAGINAS[1][6] = "Parágrafo primeiro. A prorrogação não é automática. Qualquer das"
PAGINAS[1][7] = "partes deverá manifestar interesse com antecedência mínima de 60"
PAGINAS[1][8] = "(sessenta) dias do término."
PAGINAS[1][9] = "Parágrafo segundo. Em caso de prorrogação, os valores poderão ser"
PAGINAS[1][10] = "reajustados pelo IPCA acumulado no período, limitado a 10% ao ano."
PAGINAS[1][11] = "A data de assinatura prevista é 1 de março de 2024, com término em"
PAGINAS[1][12] = "28 de fevereiro de 2025, salvo prorrogação. O prazo de 12 meses é"
PAGINAS[1][13] = "essencial para o planejamento orçamentário da CONTRATANTE."

PAGINAS[2][0] = "CLÁUSULA QUARTA - DO VALOR E DO PAGAMENTO"
PAGINAS[2][1] = "O valor total do contrato é de R$ 120.000,00 (cento e vinte mil"
PAGINAS[2][3] = "O pagamento será realizado até o quinto dia útil de cada mês,"
PAGINAS[2][4] = "mediante nota fiscal emitida pela CONTRATADA, desde que os serviços"
PAGINAS[2][5] = "do mês anterior tenham sido atestados pela CONTRATANTE."
PAGINAS[2][6] = "Parágrafo primeiro. A nota fiscal deverá ser enviada com"
PAGINAS[2][7] = "antecedência mínima de 5 (cinco) dias úteis da data de vencimento,"
PAGINAS[2][8] = "acompanhada do relatório de atividades do período."
PAGINAS[2][9] = "Parágrafo segundo. Não haverá reajuste no primeiro ano de vigência."
PAGINAS[2][10] = "Despesas de viagem somente serão reembolsadas se pré-aprovadas por"
PAGINAS[2][12] = "O valor contempla todos os tributos, encargos e custos da CONTRATADA."

PAGINAS[3][0] = "CLÁUSULA QUINTA - DAS OBRIGAÇÕES DA CONTRATADA"
PAGINAS[3][1] = "São obrigações da CONTRATADA: prestar os serviços com qualidade"
PAGINAS[3][2] = "técnica; indicar um coordenador responsável; cumprir os prazos do"
PAGINAS[3][3] = "plano de trabalho; guardar sigilo sobre informações da CONTRATANTE;"
PAGINAS[3][5] = "A CONTRATADA não poderá subcontratar a totalidade dos serviços."
PAGINAS[3][8] = "CLÁUSULA SEXTA - DAS OBRIGAÇÕES DA CONTRATANTE"
PAGINAS[3][9] = "São obrigações da CONTRATANTE: fornecer informações e acessos"
PAGINAS[3][10] = "necessários; designar um gestor do contrato; atestar os serviços;"
PAGINAS[3][11] = "efetuar os pagamentos nos prazos previstos; e comunicar mudanças de"
PAGINAS[3][12] = "escopo. A CONTRATANTE disponibilizará ambiente de trabalho remoto ou"
PAGINAS[3][13] = "presencial, conforme combinado, e acesso aos sistemas necessários."

PAGINAS[4][0] = "CLÁUSULA SÉTIMA - DO ATRASO E DAS PENALIDADES"
PAGINAS[4][1] = "Em caso de atraso no pagamento, incidirão juros de mora de 1% ao mês"
PAGINAS[4][3] = "a 30 (trinta) dias autoriza a CONTRATADA a suspender os serviços,"
PAGINAS[4][4] = "mediante notificação prévia de 5 (cinco) dias úteis, sem prejuízo da"
PAGINAS[4][5] = "cobrança do débito e das penalidades."
PAGINAS[4][6] = "Parágrafo primeiro. A suspensão não caracteriza rescisão automática."
PAGINAS[4][7] = "Os serviços serão retomados em até 3 dias úteis após a quitação."
PAGINAS[4][8] = "Parágrafo segundo. Atraso da CONTRATADA na entrega de relatórios,"
PAGINAS[4][10] = "por dia de atraso, limitada a 10% da parcela do mês."

PAGINAS[5][0] = "CLÁUSULA DÉCIMA - DA RESCISÃO"
PAGINAS[5][1] = "O presente contrato poderá ser rescindido por qualquer das partes"
PAGINAS[5][2] = "mediante notificação escrita com antecedência mínima de 30 (trinta)"
PAGINAS[5][3] = "dias. Em caso de rescisão imotivada pela CONTRATANTE antes do"
PAGINAS[5][4] = "término do prazo contratual, esta pagará à CONTRATADA multa"
PAGINAS[5][6] = "Parágrafo primeiro. Constitui justa causa para rescisão imediata:"
PAGINAS[5][7] = "inadimplemento não sanado em 15 dias; falência ou dissolução;"
PAGINAS[5][8] = "violação grave de confidencialidade; prática de ato ilícito."
PAGINAS[5][9] = "Parágrafo segundo. Na rescisão por justa causa imputável à"
PAGINAS[5][10] = "CONTRATADA, não será devida a multa de 20% prevista no caput."
PAGINAS[5][11] = "Após a rescisão, a CONTRATADA devolverá acessos e documentos em até"
PAGINAS[5][12] = "10 dias úteis e entregará relatório de transição."

PAGINAS[6][0] = "CLÁUSULA OITAVA - DA CONFIDENCIALIDADE"
PAGINAS[6][1] = "Todas as informações técnicas, comerciais, financeiras e"
PAGINAS[6][2] = "estratégicas trocadas entre as partes são confidenciais. É vedado"
PAGINAS[6][3] = "divulgar, copiar ou utilizar tais informações para finalidade diversa"
PAGINAS[6][4] = "da execução deste contrato, durante a vigência e por 24 (vinte e"
PAGINAS[6][5] = "quatro) meses após o encerramento, salvo obrigação legal."
PAGINAS[6][6] = "A violação desta cláusula autoriza a rescisão por justa causa e a"
PAGINAS[6][9] = "CLÁUSULA NONA - DA PROPRIEDADE INTELECTUAL"
PAGINAS[6][10] = "Os relatórios e materiais produzidos exclusivamente para a"
PAGINAS[6][11] = "CONTRATANTE serão de titularidade da CONTRATANTE após o pagamento."
PAGINAS[6][12] = "Ferramentas e know-how preexistentes da CONTRATADA permanecem de sua"
PAGINAS[6][13] = "titularidade, com licença de uso limitada ao objeto contratual."

PAGINAS[7][0] = "CLÁUSULA DÉCIMA PRIMEIRA - DO FORO"
PAGINAS[7][1] = "Fica eleito o foro da Comarca de São Paulo/SP para dirimir quaisquer"
PAGINAS[7][2] = "controvérsias oriundas deste contrato, com renúncia a qualquer outro."
PAGINAS[7][3] = "Antes de qualquer medida judicial, as partes envidarão esforços para"
PAGINAS[7][4] = "solução amigável no prazo de 15 dias úteis."
PAGINAS[7][6] = "CLÁUSULA DÉCIMA SEGUNDA - DAS DISPOSIÇÕES GERAIS"
PAGINAS[7][7] = "Este contrato constitui o acordo integral entre as partes. Alterações"
PAGINAS[7][8] = "somente serão válidas por escrito. A tolerância quanto ao"
PAGINAS[7][9] = "descumprimento de qualquer cláusula não implicará novação."
PAGINAS[7][10] = "São Paulo, 1 de março de 2024."
PAGINAS[7][11] = "CONTRATANTE: TECH SOLUÇÕES LTDA"


def pdf_escape(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def content_stream(linhas: list[str]) -> bytes:
    partes = ["BT", "/F1 11 Tf"]
    y = 760
    for linha in linhas:
        partes.append(f"1 0 0 1 50 {y} Tm")
        partes.append(f"({pdf_escape(linha)}) Tj")
        y -= 14
    partes.append("ET")
    return "\n".join(partes).encode("cp1252", errors="replace")


def montar_pdf(paginas: list[list[str]]) -> bytes:
    n = len(paginas)
    font_id = 3 + 2 * n
    objetos: list[bytes] = []
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{3 + i} 0 R" for i in range(n))
    objetos.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    streams = [content_stream(p) for p in paginas]
    for i in range(n):
        cid = 3 + n + i
        objetos.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Contents {cid} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
            ).encode()
        )
    for s in streams:
        objetos.append(f"<< /Length {len(s)} >>\nstream\n".encode() + s + b"\nendstream")
    objetos.append(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objetos, 1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objetos) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode()
    return bytes(pdf)


def main() -> None:
    destino = Path(__file__).parent / "pdfs" / "contrato_consultoria.pdf"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(montar_pdf(PAGINAS))
    print(f"Gerado: {destino}")


if __name__ == "__main__":
    main()
