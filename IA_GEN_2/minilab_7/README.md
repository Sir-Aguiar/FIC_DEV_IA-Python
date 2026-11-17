# Mini LAB 7 — Memória no service desk da MTI

## Problema

No service desk da MTI, um retorno pelo mesmo bloqueio de acesso faz o atendente pedir de novo o que Ana Beatriz Costa já disse: nome, CPF, login `ana.costa` e a mensagem «usuário bloqueado». Sem estado, o assistente repete esse pedido a cada turno.

Dar memória a esse assistente tem dois custos. O pedido cresce a cada turno, porque o histórico volta inteiro para o modelo. O que foi guardado passa a ser dado pessoal sob a LGPD, inclusive o que não servia ao desbloqueio.

O laboratório responde quanto a memória custa neste roteiro e se a titular consegue apagá-la de fato.

## Como executar

As dependências estão em `requirements.txt`: `agno`, `sqlalchemy[asyncio]`, `openai` e `python-dotenv`. A chave fica em `.env`, na variável `OPENAI_API_KEY`.

Os quatro comandos, nesta ordem:

```bash
python executar/medir_custo.py
python executar/inspecionar.py
python executar/eliminar.py
python executar/reproduzir_falhas.py
```

Os bancos nascem em `bancos/`. Cada cenário usa um arquivo próprio. `eliminar.py` lê o banco que `inspecionar.py` acabou de gravar (`memorias_titular.db`); os outros três não compartilham arquivo.

## Roteiro

O atendimento é um chamado de desbloqueio do correio institucional e do SEI depois de um reset de senha. São 14 turnos e seis verificações. O gabarito amarra cada resposta a um turno anterior: `deve_conter` é o trecho exigido e `testa` nomeia a origem.

O turno 9 pede a mensagem de erro dita no turno 3.

```json
{
  "n": 9,
  "texto": "Qual mensagem de erro apareceu para mim hoje de manhã?",
  "verificacao": {
    "deve_conter": ["bloqueado"],
    "testa": "mensagem de erro relatada no turno 3"
  }
}
```

No turno 4 a cidadã informa a conta `45123-8` e o nome da mãe, Lúcia Costa. Nenhum dos dois serve ao desbloqueio. A Parte 3 procura esses trechos no banco. O roteiro está em [dados/roteiro_atendimento.json](dados/roteiro_atendimento.json).

## Quatro mecanismos, uma escolha

Os quatro resolvem o mesmo problema: o modelo não guarda o login de um turno para o outro. Num chamado de 14 turnos, lembrar `ana.costa` não distingue um mecanismo do outro. O que distingue é o custo, medido na seção seguinte. `montar_agente`, em `src/fabrica.py`, só repassa o dicionário de estratégia ao `Agent`.

O histórico reenvia as mensagens desta sessão. O argumento é `add_history_to_context=True`, com `num_history_runs` dizendo quantas execuções voltam. As memórias do usuário extraem fatos e atravessam sessões. O argumento é `update_memory_on_run=True`, usado na Parte 3. O resumo condensa a conversa. O argumento é `enable_session_summaries=True`, junto com uma janela de três. A memória agêntica deixaria o modelo decidir o que guardar, com `enable_agentic_memory=True`. Esta entrega não ligou esse quarto argumento, então não há número de custo para ele.

A escolha medida é o histórico completo. A lista está em `src/custo.py`.

```python
CONFIGURACOES = [
    {"rotulo": "sem memória", "banco": None, "estrategia": {}},
    {"rotulo": "histórico completo", "estrategia": {
        "add_history_to_context": True, "num_history_runs": 100}},
    {"rotulo": "resumo + janela de 3", "estrategia": {
        "add_history_to_context": True, "num_history_runs": 3,
        "enable_session_summaries": True}},
]
```

## Custo medido

O meio da tabela é o turno 7. Os números saem de `resultados/resultado_memoria.json`. A conta está em `src/custo.py`.

| Configuração | Lembrou | Entrada T1 | Meio | Fim | Acumulado | US$ |
| --- | --- | --- | --- | --- | --- | --- |
| sem memória | 0/6 | 108 | 77 | 76 | 1.207 | 0,00094 |
| histórico completo | 6/6 | 108 | 927 | 1.595 | 12.601 | 0,00395 |
| resumo + janela de 3 | 5/6 | 409 | 1.480 | 1.647 | 18.835 | 0,00724 |

Sem memória é a linha de base: a entrada fica em torno de 80 tokens e nenhuma das seis verificações é respondida. O histórico completo é a estratégia que acerta o chamado inteiro enquanto a conversa cabe num atendimento de balcão, por US$ 0,00395. O resumo paga trabalho adicional já no primeiro turno, 409 tokens contra 108, acerta 5/6 e custa US$ 0,00724.

O roteiro reproduziu o crescimento aproximadamente linear da aula. A série de entrada do histórico completo vai de 108 a 1.595. O crescimento médio é (1.595 − 108) / 13 = 114,4 tokens por turno.

O patamar do resumo, medido no último turno, é 1.647. A soma da reta `108 + 114,4 × (k − 1)` passa de `1.647 × n` quando

```text
n = 1 + 2 × (1.647 − 108) / 114,4 = 27,9
```

O resumo passaria a compensar por volta do turno 28. Este chamado tem 14.

## O que ficou gravado

O que melhora a conversa pode ficar na memória do framework: o nome, o pedido de ser chamada de Ana, o login e a lotação. Protocolo, situação e prazo do desbloqueio mudam durante o chamado e, pela ficha, ficam na tabela do órgão, consultados por ferramenta. `src/negocio.py` não foi escrito nesta entrega, então a execução não gravou protocolo em tabela própria. O que a medição mostra é só o banco do Agno.

A extração, com `update_memory_on_run=True`, reteve quatro frases em `agno_memories`. O critério em `excede_finalidade` marca excedente o texto que contém o trecho desnecessário do roteiro. Um serviço real trocaria esse filtro por revisão humana, porque a frase muda de uma execução para outra.

| Texto retido | Necessária ao atendimento | Tabela |
| --- | --- | --- |
| A usuária se chama Ana Beatriz Costa e prefere ser chamada de Ana. | sim | agno_memories |
| O login institucional da Ana é ana.costa; ela teve problemas de acesso ao correio eletrônico e ao SEI. | sim | agno_memories |
| A mãe de Ana se chama Lúcia Costa e mora com ela. | não — excede a finalidade | agno_memories |
| Ana trabalha na Secretaria de Fazenda, na Coordenadoria de Arrecadação. | sim | agno_memories |

O dado desnecessário foi retido. «Lúcia Costa» entrou na frase extraída, em `agno_memories`, e reaparece em `agno_runs`. A conta `45123-8` não virou frase de memória; ficou no registro bruto, em `agno_memories` (1) e `agno_runs` (1).

O CPF `045.882.173-90` aparece em `agno_memories` (4), `agno_runs` (14) e `agno_sessions` (1). `agno_schema_versions` é a quarta tabela e não contém o identificador.

A extração é instável entre execuções. A rotina de eliminação percorre as duas etapas mesmo quando a lista de memórias vem vazia.

## Eliminação

Não há uma chamada única por titular. `src/eliminacao.py` encadeia as duas no banco da Parte 3.

A etapa 1 chama `delete_session`. Ela apagou `agno_sessions` e `agno_runs`. As 4 memórias continuaram em `agno_memories`. O roteiro reproduziu o efeito da aula: `delete_session` preserva `agno_memories`.

A etapa 2 lista `memory_id` com `get_user_memories` e chama `delete_user_memories` no banco. Foram apagadas 4 memórias.

```python
agente.delete_session(session_id=session_id, user_id=user_id)
banco.delete_user_memories(memory_ids=identificadores, user_id=user_id)
```

| Momento | Identificador |
| --- | --- |
| antes | agno_memories (4), agno_runs (14), agno_sessions (1) |
| depois da etapa 1 | agno_memories (4) |
| depois da etapa 2 | nenhuma tabela |

Encerrar na etapa 1 deixaria o agente sabendo o caso. Numa sessão nova, a pergunta «qual é o meu nome completo, o meu login institucional e o nome da minha mãe?» recebeu: «Seu nome completo é Ana Beatriz Costa, seu login institucional é ana.costa e o nome da sua mãe é Lúcia Costa.»

Depois das duas etapas, a mesma pergunta recebeu: «Ainda não tenho essas informações nesta conversa. Por favor, informe seu nome completo, login institucional e nome da sua mãe.» A consulta seguinte ao banco não encontrou CPF, nome, login nem o dado do turno 4.

## Vazamento e identificador

A Parte 5, em `src/falhas.py`, reproduz as duas metades da Seção 5.1. Carlos Eduardo Mendes pergunta o nome e o login já informados. Antes, Ana tinha dito que o login é `ana.costa`.

Na primeira metade, a sessão é a mesma e os `user_id` são os CPFs. O framework isolou. Carlos recebeu: «Não consigo visualizar nesta conversa o seu nome completo nem o login institucional informados anteriormente.»

Na segunda, o `user_id` é `guiche_02` para os dois. O roteiro reproduziu o vazamento da aula. Carlos recebeu: «Seu nome completo informado é Ana Beatriz Costa e seu login institucional é ana.costa.»

A regra correta é controle de acesso: o `user_id` sai do CPF do servidor, em `identificador_do_cidadao` (`src/fabrica.py`). O framework separa o identificador que lhe foi declarado e não adivinha que um guichê não é uma pessoa.

```python
def identificador_do_cidadao(cidadao: dict) -> str:
    return cidadao["cpf"]
```

## Ficha de decisões

Reprodução de `resultados/ficha_decisoes.md`.

Estratégia de memória: histórico completo com teto de 15 execuções, porque neste roteiro de 14 turnos ele acertou 6/6 por US$ 0,00395, enquanto o resumo acertou 5/6 por US$ 0,00724 e a entrada do histórico só superaria o patamar do resumo por volta do turno 28.

Origem do user_id: o CPF do servidor, em `identificador_do_cidadao`, porque o mesmo `guiche_02` fez Carlos receber «Ana Beatriz Costa» e «ana.costa»; com um CPF por pessoa, a mesma sessão não entregou o atendimento da Ana.

Dados em tabela própria: protocolo, situação e prazo do desbloqueio ficam na tabela do órgão, porque mudam durante o chamado; nome e preferência de tratamento podem ficar na memória do framework, e conta bancária e nome da mãe não ficam em nenhuma das duas.

Prazo de retenção: 30 dias para sessão, execuções e memórias do framework, porque a finalidade se esgota com o chamado e o art. 18 da LGPD só se cumpriu quando `delete_session` e `delete_user_memories` rodaram em sequência — a primeira deixou as 4 memórias, inclusive o nome da mãe.

Modo de depuração: desligado, porque o prompt e o log passariam a guardar o CPF, o login e o dado desnecessário do turno 4, que a Parte 3 já encontrou em `agno_memories` e `agno_runs`.

O desafio opcional não foi executado. Não há medição de um atendimento com mais de trinta dias saindo das três tabelas por `expurgo.py`.

## O que a turma deve conseguir defender

A memória adotada é o histórico completo com teto de 15 execuções, porque em 14 turnos ele acertou 6/6 por US$ 0,00395 e o resumo só compensaria por volta do turno 28.

O `user_id` sai do CPF do servidor, em `identificador_do_cidadao`.

O dado de processo — protocolo, situação e prazo — mora na tabela do órgão; nome e tratamento podem ficar na memória do framework.

A eliminação precisa encadear `delete_session` e `delete_user_memories`. Só depois das duas o titular some do banco e da resposta do agente.
