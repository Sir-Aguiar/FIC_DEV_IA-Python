# Parte 1 — Verificação das fontes citadas (`exemplo02.py`)

Documento usado: `src/data/processo_seletivo_mti.pdf`  
Script: `src/exemplos/exemplos/exemplo02.py`  
Auditoria: `consultas.jsonl` (raiz do projeto)

As três perguntas padrão do exemplo são de um **edital de licitação** (propostas, consórcio, multa por atraso). O PDF carregado é um **processo seletivo simplificado** da MTI. O modelo recusou as três.

As “fontes” impressas pelo script são os **trechos recuperados** (similaridade ≥ 0,25), não citações escritas na resposta. Nas recusas, a resposta não traz `(documento, p. X)`.

Numeração: o assistente cita a **página do arquivo PDF** (1–27), não o número impresso no Diário Oficial (21–47). A conferência abaixo usa a página do PDF.

## Conferência

| #   | Pergunta                                          | Resposta do modelo | Fontes recuperadas                                 | O que está na página do PDF                                                                                                                                                           | Divergência?                                                                                                                                                 |
| --- | ------------------------------------------------- | ------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Qual o prazo para envio das propostas?            | Recusa padrão      | p. 1 (0,535 e 0,525); p. 5 (0,529); p. 4 (0,516)   | p. 1, item 2.1: inscrições das 08:00 de 15/06/2026 às 23:59 de 16/06/2026. p. 4, item 7: o mesmo período no cronograma. Não há “envio de propostas”.                                  | **Não no mérito da resposta.** Recusa correta. As fontes falam de _inscrição_ e _prazos_, não de propostas.                                                  |
| 2   | A empresa pode participar em consórcio?           | Recusa padrão      | p. 27 (0,500 e 0,461); p. 5 (0,478); p. 26 (0,472) | p. 26–27: minuta de contrato temporário (CLT / LC 600/2017). p. 5: convocação e contratação do candidato. A palavra “consórcio” não aparece no PDF.                                   | **Não.** Recusa correta. Fontes só passaram no limiar por vocabulário de contrato/empresa.                                                                   |
| 3   | Qual o percentual da multa por atraso na entrega? | Recusa padrão      | p. 27 (0,459; 0,428; 0,425; 0,408)                 | p. 27, cláusula 12.1.3: multa de **1 (um) mês de remuneração** se o contratado **não cumprir o aviso prévio de 30 dias** (inciso II). Não é percentual e não é por atraso de entrega. | **Parcial, só na recuperação.** A multa existe na página citada, mas **não responde à pergunta**. A recusa do modelo está certa (não inventar equivalência). |

## Observações

1. **Perguntas do exemplo vs. acervo.** O `exemplo02.py` não adapta as perguntas ao PDF informado. Com este edital, o comportamento esperado é recusar.
2. **Página 4 tem prazo, mas de inscrição.** Quem abrisse só o cronograma poderia achar que o assistente “errou” ao recusar a pergunta 1. No documento, o prazo é de inscrição no SIES/MT, não de propostas.
3. **Página 27 tem multa, mas outra.** Quem lesse só o item 12.1.3 poderia achar que a pergunta 3 deveria ter sido respondida. O texto não traz percentual nem atraso na entrega; responder “1 mês de remuneração” seria extrapolar.
4. **Limiar de similaridade (0,25).** Todas as consultas trouxeram 4 trechos acima do corte, mesmo sem cobrir a pergunta. A barreira que evitou alucinação foi a instrução ao modelo, não o filtro de recuperação.
5. **Número impresso no Diário Oficial.** PDF p. 1 = DO p. 21; PDF p. 4 = DO p. 24; PDF p. 27 = DO p. 47. Abrir “página 27” no jornal (e não no arquivo) não localiza a multa.

## Conclusão

Não houve invenção de prazo, consórcio ou percentual. As recusas batem com o PDF. As divergências são de **encaixe das perguntas** e de **trechos recuperados próximos, porém off-topic**.
