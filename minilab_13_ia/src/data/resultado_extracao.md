# Parte 1 — Extração de PDF com rastreabilidade

Script: `src/exemplos/exemplos/exemplo01.py`  
Parâmetros de divisão: tamanho 600, sobreposição 100.

## Resultado

| Documento                   | Páginas no PDF | Páginas com texto | Trechos | Texto extraído? | Exige OCR? |
| --------------------------- | -------------: | ----------------: | ------: | --------------- | ---------- |
| `regimento_interno_mti.pdf` |             21 |                21 |     350 | Sim             | Não        |
| `processo_seletivo_mti.pdf` |             27 |                27 |     301 | Sim             | Não        |

## Observações

- Os dois arquivos são recortes do Diário Oficial e têm camada de texto. O `exemplo01.py` extraiu conteúdo em **todas** as páginas; nenhuma página vazia foi ignorada.
- Nenhum documento exigiria OCR nesta etapa: o PyMuPDF recuperou texto contínuo e legível (competências, cronograma, anexos, cláusulas).
- Cada página também contém 1 imagem de fundo (fac-símile da publicação). Isso aumenta o tamanho do arquivo — sobretudo o do processo seletivo — mas não impede a extração textual.
- Totais de caracteres extraídos: **160.742** no regimento interno e **130.030** no processo seletivo.

