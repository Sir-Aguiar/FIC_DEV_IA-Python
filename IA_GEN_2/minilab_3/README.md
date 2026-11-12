# Problema

Como impedir que um assistente que consulta, calcula e atualiza valores erre em silêncio, invente dados ou gaste sem controle depois de liberado para a equipe?

# Incidentes

> 3 incidentes em cinco dias de uso real — nenhum deles era erro de programação

1. Respondeu a um cálculo de débito sem chamar a ferramenta: número que parecia correto e não era.
2. Inventou o número de um processo para conseguir alimentar a ferramenta de busca.
3. Uma única consulta consumiu quarenta vezes o custo médio, sem explicação.

# Mini Lab

Construir o assistente do seu próprio setor, medi-lo e provocar as falhas nele.
A atividade usa apenas a OpenAI, provedor de referência do curso. (Chave em OPENAI_API_KEY)

## Parte 1 - Declaração de ferramentas

- Escolha um serviço do seu órgão que envolva consulta e cálculo, e defina três ferramentas para ele

### Encaixe de lote de processamento fiscal

Encaixe de lote de processamento fiscal

#### consultar_rotina(rotina: str)

> Busca na base a rotina que o lote vai usar. Devolve o ritmo em registros por hora, a duração da janela e as horas restantes. O argumento é o nome ou o código, como "processamento de NF-e" ou "RT-SPED". Se não achar, devolve que a rotina não existe. Isso impede o modelo de completar o encaixe com um ritmo que ele mesmo escolheu.

##### calcular_encaixe_lote(volume: int, registros_por_hora: int, horas_restantes: float)

> Recebe o volume do lote, o ritmo e as horas restantes. Devolve as horas necessárias (volume dividido pelo ritmo) e se o lote cabe na janela. Ritmo e horas restantes têm de vir da consulta anterior ou estar escritos na pergunta. A conta é de horas corridas da janela, sem calendário de dias úteis.

##### atualizar_consumo_janela

> Terceira ferramenta, StructuredTool com esquema Pydantic e descrição em todo campo. É a ferramenta sensível: grava na janela as horas que o lote vai consumir.
>
> - codigo_rotina (obrigatório): código devolvido pela consulta, como "RT-NFE"
> - horas_previstas (obrigatório): horas que o cálculo de encaixe disse que o lote precisa
>
> A descrição diz quando não usá-la: não grave consumo de um lote que ultrapasse as horas restantes, nem quando o volume não estiver escrito na pergunta.

# Observações

## Ao executar `example01.py`

No esquema impresso, atualizar_consumo_janela comunica ao modelo o significado dos dois argumentos.

As duas primeiras ferramentas chegam só com o tipo (rotina como string; volume, registros_por_hora e horas_restantes como número). A terceira, no JSON que iria para a API, leva descrição em cada campo:

- codigo_rotina: código devolvido pela consulta da rotina, como RT-NFE
- horas_previstas: horas que o cálculo de encaixe disse que o lote precisa
