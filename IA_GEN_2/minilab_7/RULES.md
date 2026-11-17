# Estrutura de arquivos

A solução do Mini LAB fica separada da pasta `exemplos/`. Os exemplos da aula permanecem como referência da Seção 1 à Seção 6. O código entregue vive em `src/`, os roteiros de entrada em `dados/`, os pontos de execução em `executar/` e as evidências medidas em `resultados/`.

Cada módulo responde a uma parte do enunciado. Quem lê o repositório encontra a parte do laboratório pelo nome do arquivo, sem precisar percorrer um script único.

```text
minilab_7/
├── README.md
├── RULES.md
├── requirements.txt
├── .env                          # OPENAI_API_KEY; fora do controle de versão
├── .gitignore                    # .env, bancos/*.db, __pycache__
│
├── dados/
│   └── roteiro_atendimento.json  # Parte 1: 10 a 15 turnos e o gabarito
│
├── src/
│   ├── __init__.py
│   ├── configuracao.py           # modelo, preços por milhão, caminhos, instrução
│   ├── fabrica.py                # monta o Agent: db, user_id, session_id, estratégia
│   ├── roteiro.py                # carrega turnos e confere deve_conter
│   ├── negocio.py                # tabela própria do órgão e ferramenta de consulta
│   ├── custo.py                  # Parte 2: configurações, métricas, ponto de virada
│   ├── memorias.py               # Parte 3: inspeção, necessidade, tabelas do titular
│   ├── eliminacao.py             # Parte 4: delete_session e delete_user_memories
│   ├── falhas.py                 # Parte 5: vazamento e regra de derivação
│   └── expurgo.py                # desafio opcional: retenção acima de 30 dias
│
├── executar/
│   ├── medir_custo.py            # roda o roteiro nas configurações e grava o JSON
│   ├── inspecionar.py            # lista memórias, necessidade e tabelas
│   ├── eliminar.py               # executa a rotina e pergunta de novo ao agente
│   └── reproduzir_falhas.py      # reproduz o vazamento da Seção 5.1
│
├── resultados/
│   ├── resultado_memoria.json    # números da Parte 2, gerados pela execução
│   ├── tabela_necessidade.md     # Parte 3: o que foi retido e se excede a finalidade
│   └── ficha_decisoes.md         # Parte 6: uma linha justificada por item
│
├── bancos/                       # SQLite gerado em execução; não versionar
└── exemplos/                     # material da aula; não alterar para “fazer caber” a entrega
```

## O que cada arquivo guarda

`dados/roteiro_atendimento.json` é a entrada da Parte 1. O objeto do cidadão traz nome e identificador. Cada turno tem `n`, `texto` e `verificacao`. Quando há verificação, `deve_conter` lista o que a resposta precisa incluir e `testa` nomeia o turno anterior que originou o fato. Pelo menos um turno informa um dado pessoal que não serve ao atendimento, para a Parte 3 poder procurar esse excedente no banco.

`src/configuracao.py` concentra o que os demais módulos compartilham: identificador do modelo, `reasoning_effort`, preços `USD_ENTRADA` e `USD_SAIDA`, caminho da pasta `bancos/` e o texto da instrução do atendente. Preço e modelo não se repetem dentro de cada experimento.

`src/fabrica.py` é o único lugar que instancia `Agent` e `SqliteDb`. Recebe o nome do arquivo de banco, `user_id`, `session_id` e os argumentos da estratégia (`add_history_to_context`, `num_history_runs`, `enable_session_summaries`, `update_memory_on_run`). A derivação do `user_id` também mora aqui: a função correta parte do identificador do cidadão; a função incorreta, usada só na Parte 5, parte de algo que não individualiza, como o guichê.

`src/roteiro.py` lê o JSON e aplica a verificação do enunciado: percorre `deve_conter` em minúsculas, sem depender de formatação markdown da resposta.

`src/negocio.py` separa dado de processo e memória do framework, como pede a Seção 4. Protocolo, situação e prazo ficam em tabela SQLite do órgão. Uma ferramenta do agente consulta essa tabela. Nome e preferência de tratamento podem permanecer na memória do Agno. Situação de protocolo, saldo e prazo em curso são respondidos pela ferramenta, porque mudam com o tempo.

`src/custo.py` implementa a Parte 2. Declara no mínimo três configurações, com `sem memória` e `histórico completo` obrigatórias. A terceira fecha o contraste útil do caso: janela curta, resumo com janela, ou memórias de usuário com janela. Para cada uma, percorre o roteiro, acumula tokens de entrada e de saída, conta acertos das verificações, mede o tempo e converte o total em dólares. Apaga o banco no início de cada configuração. A partir da série de entrada do histórico completo, calcula o crescimento por turno e estima em quantos turnos o resumo passaria a compensar.

`src/memorias.py` implementa a Parte 3. Depois de um atendimento com `update_memory_on_run=True`, abre o SQLite, lista as tabelas, conta em quais o identificador ou o nome do titular aparece e lê o texto de `agno_memories`. Marca como excedente o registro cujo texto contém o dado pessoal desnecessário do roteiro. O critério fica explícito no código, junto com o comentário de que um serviço real trocaria o filtro por revisão humana.

`src/eliminacao.py` implementa a Parte 4 em duas etapas encadeadas, porque na versão testada do Agno não há uma chamada única por titular. A etapa 1 chama `delete_session` no agente e mede o que restou. A etapa 2 lista as memórias com `get_user_memories`, extrai os identificadores e chama `delete_user_memories` no objeto de banco. Depois das duas, a função de contagem percorre todas as tabelas de novo e uma sessão nova pergunta ao agente algo que só a memória saberia.

`src/falhas.py` implementa a Parte 5. Reproduz as duas metades da Seção 5.1: mesma `session_id` com `user_id` distintos, e o mesmo identificador derivado do guichê para dois cidadãos. Registra o texto que o segundo cidadão recebeu. No mesmo módulo, a regra de derivação correta é uma função nomeada e comentada: o `user_id` sai do documento do titular, nunca do canal, do guichê ou do atendente.

`src/expurgo.py` fica reservado ao desafio opcional. Remove das tabelas de memória, de sessão e de execuções os atendimentos cuja data passa do prazo declarado, e demonstra um caso com mais de trinta dias.

`executar/` só orquestra. Cada script importa o módulo correspondente, chama uma função e imprime o veredito. A lógica de medição, inspeção e exclusão não é reescrita no script.

`resultados/` guarda o que o README cita. `resultado_memoria.json` sai de `medir_custo.py`. `tabela_necessidade.md` e `ficha_decisoes.md` são preenchidos com o que a execução mostrou, uma linha por decisão: estratégia de memória, origem do `user_id`, o que fica em tabela própria, prazo de retenção e se o modo de depuração fica ligado.

## Dependências entre módulos

```text
configuracao.py
    └── fabrica.py
            ├── roteiro.py
            ├── negocio.py
            ├── custo.py          → resultados/resultado_memoria.json
            ├── memorias.py       → resultados/tabela_necessidade.md
            ├── eliminacao.py
            ├── falhas.py
            └── expurgo.py
```

`fabrica.py` não importa os experimentos. Os experimentos não importam uns aos outros. Assim, medir custo não dispara eliminação, e reproduzir o vazamento não altera o banco do atendimento medido: cada cenário recebe o próprio arquivo em `bancos/`.

# Comentários

Toda solução e/ou decisão lógica deve ser devidamente comentada de maneira explicativa.

O comentário diz por que a decisão existe e a qual parte do Mini LAB ela responde. Um comentário útil nomeia o efeito observado na aula: o histórico completo cresce de forma aproximadamente linear; `delete_session` preserva `agno_memories`; `user_id` derivado do guichê vaza o atendimento anterior. O comentário fica junto da função ou do bloco que toma a decisão, em português, em frases completas.

# Estilo

Deve haver espaçamento satisfatório entre linhas de funções, entre classes, fluxos e funções.

Uma função por responsabilidade. Linha em branco entre funções, entre a assinatura e o corpo quando o docstring é longo, e entre os passos de um fluxo (montar agente, percorrer turnos, conferir gabarito, gravar resultado). Constantes de preço, modelo e caminhos ficam no topo de `configuracao.py`. Nomes de funções e de arquivos em português, alinhados às partes do enunciado.

# Como escrever o README.md

O README é o texto pelo qual a turma acompanha a solução sem abrir todos os arquivos de uma vez. Ele explica o problema, a decisão e a evidência, e aponta o arquivo em que a decisão está implementada. Números, tabelas e vereditos vêm de `resultados/` e da saída dos scripts em `executar/`. O README não antecipa um resultado que a execução ainda não produziu.

Escreva em português, em parágrafos curtos, na ordem das partes do Mini LAB. Cada seção abre com a decisão em uma frase e, em seguida, mostra como o código a realiza e o que a medição mostrou.

## Seções obrigatórias

1. **Problema.** Um atendimento de retorno em que o assistente, sem estado, pede de novo o que o cidadão já disse. Nomeie os dois custos de dar memória a esse assistente: o pedido cresce a cada turno, e o que foi guardado passa a ser dado pessoal sob a LGPD. Feche com a pergunta que o laboratório responde: quanto a memória custa neste roteiro e se o titular consegue apagá-la de fato.

2. **Como executar.** Liste `requirements.txt` (`agno`, `sqlalchemy[asyncio]`, `openai`, `python-dotenv`), a variável `OPENAI_API_KEY` e os quatro comandos, nesta ordem: `medir_custo.py`, `inspecionar.py`, `eliminar.py`, `reproduzir_falhas.py`. Diga que os bancos nascem em `bancos/` e que cada cenário usa um arquivo próprio.

3. **Roteiro.** Descreva o atendimento do órgão em poucas linhas. Mostre um turno de verificação completo, com `deve_conter` e `testa`, e explique que o gabarito amarra a resposta a um turno anterior específico. Aponte o turno em que o cidadão informa um dado pessoal desnecessário e diga que esse dado será procurado na Parte 3. Link para `dados/roteiro_atendimento.json`.

4. **Quatro mecanismos, uma escolha.** Explique, em linguagem de atendimento, o que cada mecanismo faz: o histórico reenvia as mensagens da sessão; as memórias do usuário extraem fatos e atravessam sessões; o resumo condensa a conversa; a memória agêntica deixa o modelo decidir o que guardar. Relacione cada um ao argumento do `Agent` usado em `fabrica.py`. Deixe claro que, numa conversa curta, lembrar a placa não distingue os mecanismos: o que os distingue é o custo, medido na seção seguinte.

5. **Custo medido.** Reproduza a tabela gerada, com as colunas do enunciado: configuração, lembranças, entrada no primeiro turno, no meio, no fim, acumulado e dólares. Interprete três fatos a partir dos números próprios: a configuração sem memória como linha de base; o histórico completo como a estratégia que mais acerta enquanto a conversa cabe num atendimento; a configuração extra como o contraste que mostra janela curta esquecendo o início, ou resumo e memórias de usuário pagando trabalho adicional já no primeiro turno. Em seguida, mostre o crescimento de entrada por turno e a conta do ponto em que o resumo passaria a compensar. A conta fica em `src/custo.py` e os números em `resultados/resultado_memoria.json`.

6. **O que ficou gravado.** Explique a distinção da Seção 4 com o caso concreto: o que melhora a conversa pode ficar na memória do framework; protocolo, situação e decisão ficam na tabela de `negocio.py` e entram por ferramenta. Cole a tabela de necessidade: texto retido, se é necessário ao atendimento e em qual tabela apareceu. Diga se o dado desnecessário do roteiro foi retido e liste todas as tabelas em que o identificador do cidadão aparece. Reforce que a extração é instável entre execuções, então a rotina de eliminação percorre todas as etapas mesmo quando a lista de memórias vem vazia.

7. **Eliminação.** Descreva as duas etapas na ordem em que o código as executa. A primeira, `delete_session`, apaga sessão e execuções e deixa as memórias extraídas. A segunda lista `memory_id` e chama `delete_user_memories` no banco. Mostre a contagem do titular antes, depois da etapa 1 e depois da etapa 2. Feche com a pergunta feita numa sessão nova e com a resposta registrada. O leitor precisa ver que encerrar na etapa 1 deixaria o agente ainda sabendo o nome ou o documento.

8. **Vazamento e identificador.** Conte as duas metades da Parte 5. Na primeira, a mesma sessão com identificadores distintos isola os cidadãos. Na segunda, o `user_id` derivado do guichê faz o segundo cidadão receber dado do primeiro: cite o trecho da resposta. Em seguida, escreva a regra correta em uma frase e aponte a função em `fabrica.py` ou `falhas.py`. Trate essa regra como controle de acesso: o framework separa o que foi declarado, e não adivinha que um guichê não é uma pessoa.

9. **Ficha de decisões.** Reproduza `resultados/ficha_decisoes.md`. Cada linha justifica a escolha com um número da seção de custo ou com uma norma (necessidade e eliminação, LGPD art. 18). Os cinco itens são: estratégia de memória, origem do `user_id`, dados que ficam em tabela própria, prazo de retenção e modo de depuração. Se o desafio opcional foi feito, um parágrafo mostra que um atendimento com mais de trinta dias some das três tabelas pela rotina de `expurgo.py`.

10. **O que a turma deve conseguir defender.** Feche com quatro frases que um colega conseguiria repetir: a memória adotada e por que o experimento a sustentou; de onde sai o `user_id`; onde mora o dado de processo; e quais chamadas a eliminação precisa encadear para o titular deixar de aparecer no banco e na resposta do agente.

## Tom e evidência

Escreva como quem apresenta o desenho a uma auditoria da turma: decisão, medida, arquivo. Evite descrever o Agno em abstrato sem amarrar ao roteiro do órgão. Quando um comportamento da aula se repetir na execução (crescimento linear, memória que sobrevive a `delete_session`, vazamento por identificador de guichê), diga que o roteiro próprio reproduziu esse comportamento e mostre o número ou o trecho. Quando não se repetir, registre o que saiu na execução, porque a extração de memórias varia entre rodadas.

Trechos de código no README são curtos e servem para localizar a decisão: a lista de configurações, o critério de necessidade, as duas chamadas de exclusão e a função que deriva o `user_id`. O restante da leitura fica no arquivo indicado, com o comentário explicativo ao lado da função.
