# ============================================================
# Aula 13 – Construindo um Assistente de Documentos
# Módulo: IA Generativa | Curso: Formação em IA – UNEMAT/RISC
# Utilitário: gera o edital fictício usado nos exemplos da aula
# Seção 3 – Extração de Texto com Rastreabilidade
# Requisitos: pip install pymupdf
# Execução: python criar_pdf_teste.py
# ============================================================
"""Gera o arquivo edital_exemplo.pdf usado pelos exemplos da Aula 13.

O documento é inteiramente fictício e serve apenas para exercitar o
pipeline. Ele foi escrito com PDF de texto nativo (não digitalizado),
de modo que a extração direta funciona sem OCR.
"""

import pymupdf

doc = pymupdf.open()

# ------------------------------------------------------------------
# Página 1 — identificação, objeto, valor e prazos
# ------------------------------------------------------------------
pagina1 = doc.new_page()
pagina1.insert_text(
    (72, 72),
    "EDITAL DE PREGÃO ELETRÔNICO Nº 014/2026",
    fontsize=14,
    fontname="helv",
)
pagina1.insert_text(
    (72, 110),
    """PROCESSO ADMINISTRATIVO Nº 2026/SEPLAG/00412

REGIME LEGAL: Lei Federal nº 14.133, de 1º de abril de 2021.

OBJETO: Contratação de empresa especializada para fornecimento de
equipamentos de informática destinados à Secretaria de Estado de
Planejamento e Gestão de Mato Grosso.

VALOR ESTIMADO DA CONTRATAÇÃO: R$ 500.000,00 (quinhentos mil reais).

PRAZO PARA ENVIO DAS PROPOSTAS: até 30 (trinta) dias corridos contados
da publicação deste edital no Diário Oficial do Estado.

DATA DA SESSÃO PÚBLICA: 15/09/2026, às 09h00 (horário de Brasília).

CRITÉRIO DE JULGAMENTO: menor preço por item.

MODO DE DISPUTA: aberto, na forma do art. 56 da Lei nº 14.133/2021.""",
    fontsize=11,
    fontname="helv",
)

# ------------------------------------------------------------------
# Página 2 — habilitação e consórcio
# ------------------------------------------------------------------
pagina2 = doc.new_page()
pagina2.insert_text(
    (72, 72),
    "CAPÍTULO II - DA HABILITAÇÃO",
    fontsize=13,
    fontname="helv",
)
pagina2.insert_text(
    (72, 100),
    """Art. 5º - Para fins de habilitação técnica, a licitante deverá
apresentar:
I - atestado de capacidade técnica emitido por pessoa jurídica de
direito público ou privado, comprovando o fornecimento anterior de
equipamentos de informática em quantidade compatível com o objeto;
II - certidão negativa de débitos trabalhistas;
III - certidão de regularidade fiscal federal, estadual e municipal.

Art. 6º - A licitante deverá comprovar capital social mínimo de
R$ 50.000,00 (cinquenta mil reais), integralizado até a data de
apresentação da proposta.

Art. 7º - É permitida a participação de empresas reunidas em
consórcio, desde que o consórcio seja composto por no máximo 3 (três)
empresas e que a empresa líder possua sede no Estado de Mato Grosso.

Art. 8º - A documentação de habilitação será exigida apenas da
licitante vencedora, na forma do art. 63 da Lei nº 14.133/2021.""",
    fontsize=11,
    fontname="helv",
)

# ------------------------------------------------------------------
# Página 3 — especificações técnicas
# ------------------------------------------------------------------
pagina3 = doc.new_page()
pagina3.insert_text(
    (72, 72),
    "CAPÍTULO III - DAS ESPECIFICAÇÕES TÉCNICAS",
    fontsize=13,
    fontname="helv",
)
pagina3.insert_text(
    (72, 100),
    """Art. 9º - Os equipamentos deverão atender às seguintes
especificações mínimas:

ITEM 1 - Computador Desktop
- Processador: Intel Core i5 de 12ª geração ou superior
- Memória RAM: 16 GB DDR4
- Armazenamento: SSD 512 GB NVMe
- Sistema operacional: Windows 11 Pro
- Garantia: 36 meses on-site

ITEM 2 - Monitor LED
- Tamanho: 24 polegadas
- Resolução: Full HD (1920x1080)
- Conexões: HDMI e DisplayPort
- Garantia: 36 meses

ITEM 3 - Notebook
- Processador: Intel Core i7 de 12ª geração ou superior
- Memória RAM: 16 GB DDR4
- Armazenamento: SSD 512 GB NVMe
- Tela: 15,6 polegadas Full HD
- Garantia: 36 meses on-site

Art. 10 - O prazo de entrega dos equipamentos é de 45 (quarenta e
cinco) dias corridos, contados do recebimento da ordem de fornecimento.""",
    fontsize=11,
    fontname="helv",
)

doc.save("edital_exemplo.pdf")
doc.close()
print("PDF criado: edital_exemplo.pdf (3 páginas)")
