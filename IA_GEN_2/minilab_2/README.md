# Minilab 2 — LangChain compensa na extração de protocolo?

Medição de 10 de novembro de 2026, com a `OPENAI_API_KEY` do `.env` deste minilab. Conjunto, gabarito e código estão em `src/documentos.jsonl` e `src/main.py`.

## Condição da medição

Não há `GROQ_API_KEY` nem `HF_TOKEN`. As três implementações rodaram na OpenAI, no modelo `gpt-5.6-luna`, com a mesma instrução e os mesmos dez documentos. A chamada de aquecimento foi descartada antes do cronômetro. A latência da tabela é a mediana das dez chamadas.

Preço usado, o do exemplo 04 da aula para esse modelo: US$ 0,20 por milhão de tokens de entrada e US$ 1,20 por milhão de tokens de saída.

## Conjunto

Dez documentos anonimizados da Gerência de Tecnologia da Informação da Secretaria de Estado de Fazenda. O gabarito foi escrito antes de qualquer chamada. São seis campos: número, data (`AAAA-MM-DD`), valor, solicitante, objeto e prioridade. Sessenta campos no total.

Casos difíceis incluídos de propósito:

- `DESP-GTI-2026-0077`: valor só por extenso (“duzentos e quinze mil reais” = 215000).
- `MEM-GTI-2026-0310`: data por extenso (“quatorze de julho de 2026” = 2026-07-14).
- Quatro documentos sem valor (`MEM-GTI-2026-0044`, `NT-GTI-2026-0012`, `MEM-GTI-2026-0310`, `REQ-GTI-2026-0275`).

O objeto aceita similaridade de 60%. Os demais campos exigem igualdade, e o valor aceita diferença menor que um centavo.

## Destinos

Pergunta única sobre dispensa e inexigibilidade na Lei nº 14.133/2021, depois do aquecimento.

| Destino               |      Tempo | Entrada | Saída |
| --------------------- | ---------: | ------: | ----: |
| OpenAI · gpt-5.6-luna |     1,21 s |      51 |    37 |
| Groq · gpt-oss-20b    | sem medida |       — |     — |
| Hugging Face          | sem medida |       — |     — |

A OpenAI respondeu: na dispensa a licitação é possível, mas a lei autoriza não realizá-la; na inexigibilidade a competição é inviável. Groq e Hugging Face não foram chamados por falta de chave.

## Parâmetro descartado

No SDK, com `gpt-5.6-luna`:

- `temperature=0.3` gera `BadRequestError`: o modelo só aceita o valor padrão.
- `max_tokens=500` gera `BadRequestError`: o parâmetro não existe; o nome aceito é `max_completion_tokens`.
- `max_completion_tokens=500` é aceito.

Os mesmos `temperature=0.3` e `max_tokens=500`, passados ao LangChain, não geram erro. O que segue para a API é `{'model': 'gpt-5.6-luna', 'max_completion_tokens': 500}`. O atributo `temperature` no objeto fica `None`. O limite foi traduzido. A temperatura escrita no código não entra no pedido.

## Tabela

Dez documentos, modelo `gpt-5.6-luna`.

| Implementação                      | Campos corretos | Entrada | Saída | Latência |     US$ |
| ---------------------------------- | --------------: | ------: | ----: | -------: | ------: |
| SDK openai puro                    |           60/60 |   3.190 |   770 |   1,49 s | 0,00156 |
| LangChain + JsonOutputParser       |           60/60 |   2.440 | 1.129 |   1,74 s | 0,00184 |
| LangChain + with_structured_output |           60/60 |   4.010 |   741 |   1,39 s | 0,00169 |

JSON inválido: zero nos três caminhos. Valor por extenso, data por extenso e ausência de valor foram acertados nas três.

O esquema declarado consumiu 4.010 tokens de entrada contra 3.190 do SDK, 26% a mais, para o mesmo acerto. O parser gastou menos entrada e mais saída. Como o token de saída custa seis vezes o de entrada, o parser ficou o mais caro dos três.

## Troca de destino

Os três empataram em 60/60. O desempate pelo menor custo aponta o SDK. Sem chave da Groq, a repetição troca só o identificador do modelo, de `gpt-5.6-luna` para `gpt-5.6-sol`, na mesma função. Uma linha.

Nessa segunda execução o SDK manteve 60/60, zero JSON inválido, mediana de 1,63 s, 3.190 tokens de entrada e 668 de saída. O dólar dessa segunda corrida não entra na tabela: a tarifa aplicada acima é a do `gpt-5.6-luna`.

## Análise

A exatidão não escolhe. As três implementações acertaram os sessenta campos, inclusive o valor por extenso e os documentos sem valor. O custo dos dez documentos ficou entre US$ 0,00156 e US$ 0,00184.

Premissa de volume, não série medida do órgão: 800 documentos por mês na triagem da gerência. O mês ficaria em US$ 0,12 (SDK), US$ 0,14 (esquema declarado) e US$ 0,15 (parser). Em 5.000 documentos por mês a distância entre o SDK e o esquema ainda fica abaixo de US$ 0,07. O acréscimo de 26% na entrada do `with_structured_output` não altera a decisão nessa escala.

A coluna que pesa na gerência é o custo só enquanto o provedor permanece a OpenAI: o SDK é o mais barato e a troca de modelo dentro da mesma API também coube em uma linha. A vantagem de portabilidade do LangChain não foi exercida, porque não havia segundo provedor autenticado. Se a troca passar a ser de fornecedor, o caminho com esquema declarado preserva instrução e classe; o sobrepreço medido aqui é pequeno demais para impedir essa reserva.

## Modo de falha

O maior risco no processo de extração para autuação é o descarte silencioso de `temperature`. O SDK recusa `0.3` com erro. O LangChain aceita a construção, conclui a chamada e envia o pedido sem temperatura. Um despacho de configuração registraria o controle, o sistema responderia com sucesso e o controle não teria chegado ao modelo. Falha de importação da linha 0.x derruba o serviço na hora. Token extra aparece na fatura, como as 820 tokens de entrada a mais do esquema declarado.

Em produção, a garantia é conferir o payload antes do envio: ler `_default_params` (ou o corpo equivalente no SDK) e recusar a subida se `temperature` ou o limite de saída pedidos não estiverem no dicionário que vai à API.

