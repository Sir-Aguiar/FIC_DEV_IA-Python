# Parte 1 — Bateria de auditoria (`exemplo03.py`)

Acervo: `processo_seletivo_mti.pdf` (301 trechos) e `regimento_interno_mti.pdf` (350 trechos).  
Páginas anotadas = número no **arquivo PDF**, não o número impresso no Diário Oficial.

A bateria tem dez perguntas: sete com resposta no acervo e três sem resposta alguma.

## Limiar 0,25

| Pergunta                                                                          | Esperado  | Obtido    | Página esperada | Página citada |
| --------------------------------------------------------------------------------- | --------- | --------- | --------------: | ------------: |
| Há cobrança de taxa de inscrição no processo seletivo da MTI?                     | responder | respondeu |               1 |             1 |
| Qual a remuneração do perfil Analista de TI - Gerente de Projeto?                 | responder | respondeu |               2 |             2 |
| Qual o percentual de vagas reservadas às pessoas com deficiência?                 | responder | respondeu |               3 |             3 |
| Qual o período de inscrições previsto no cronograma do edital?                    | responder | respondeu |               4 |             4 |
| O exame admissional é obrigatório na contratação?                                 | responder | recusou   |               5 |             — |
| Qual a multa aplicada se o contratado não cumprir o aviso prévio de 30 dias?      | responder | respondeu |              27 |            27 |
| A Gerência de Aquisições realiza procedimentos licitatórios de quais modalidades? | responder | respondeu |              10 |            10 |
| Qual o capital social mínimo exigido para participar do certame?                  | recusar   | recusou   |               — |             — |
| Quem é o pregoeiro responsável pela sessão pública?                               | recusar   | recusou   |               — |             — |
| Qual a alíquota do IPVA em Mato Grosso em 2026?                                   | recusar   | recusou   |               — |             — |

Resultado: **9 de 10** comportamentos corretos. **1** pergunta legítima recusada (exame admissional). As três perguntas sem resposta no acervo foram recusadas.

## Limiar 0,45

O limiar de similaridade do `AssistenteDocumentos` foi alterado de 0,25 para 0,45 e a bateria foi executada de novo.

| Pergunta                                                                          | Esperado  | Obtido    | Página esperada | Página citada |
| --------------------------------------------------------------------------------- | --------- | --------- | --------------: | ------------: |
| Há cobrança de taxa de inscrição no processo seletivo da MTI?                     | responder | respondeu |               1 |             1 |
| Qual a remuneração do perfil Analista de TI - Gerente de Projeto?                 | responder | respondeu |               2 |             2 |
| Qual o percentual de vagas reservadas às pessoas com deficiência?                 | responder | respondeu |               3 |             3 |
| Qual o período de inscrições previsto no cronograma do edital?                    | responder | respondeu |               4 |             4 |
| O exame admissional é obrigatório na contratação?                                 | responder | recusou   |               5 |             — |
| Qual a multa aplicada se o contratado não cumprir o aviso prévio de 30 dias?      | responder | respondeu |              27 |            27 |
| A Gerência de Aquisições realiza procedimentos licitatórios de quais modalidades? | responder | respondeu |              10 |            10 |
| Qual o capital social mínimo exigido para participar do certame?                  | recusar   | recusou   |               — |             — |
| Quem é o pregoeiro responsável pela sessão pública?                               | recusar   | recusou   |               — |             — |
| Qual a alíquota do IPVA em Mato Grosso em 2026?                                   | recusar   | recusou   |               — |             — |

## Efeito do limiar

**Perguntas legítimas que passaram a ser recusadas ao subir o limiar para 0,45: 0.**

O quadro ficou idêntico. A única recusa indevida (exame admissional, p. 5 do processo seletivo) já ocorria com 0,25. Na auditoria, os trechos recuperados vieram sobretudo da p. 4 (requisitos e documentos da contratação), com similaridade 0,57 — acima dos dois cortes. O item 10.1.5 (“Será obrigatório a realização de exame admissional…”) não entrou no contexto; o modelo recusou por falta de trecho, não por limiar.

As seis demais perguntas com resposta conhecida continuaram fundamentadas e com a página certa. As três perguntas fora do acervo continuaram recusadas.
