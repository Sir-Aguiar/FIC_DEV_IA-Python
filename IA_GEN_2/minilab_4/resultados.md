## O que foi feito

A diretoria da Empresa Mato-grossense de Tecnologia da Informação (MTI) precisa decidir o que o Relatório Anual de Gestão (RAG) de 2025 sustenta sobre o Programa 536, Tecnologia da Informação e Comunicação (TIC) para o governo. O relatório público mostra disponibilidade de 99,47% abaixo da meta de 99,80%, satisfação de 89,82% acima da meta de 75%, e duas apurações orçamentárias que não fecham a mesma conta. Um parecer útil separa o eixo técnico, o financeiro e o jurídico. Um parecer que funde as duas séries, ou que repete um número recebido da etapa anterior, leva a diretoria a decidir sobre um dado que o dossiê não confirma.

O material de trabalho é uma página, em `src/dados/dossie_projeto.md`, extraída do RAG publicado. O plano de negócios da empresa está classificado como sigiloso e fica de fora.

Sobre esse dossiê montei uma equipe de três agentes na biblioteca CrewAI, que organiza o trabalho em papéis. O analista técnico lê disponibilidade, satisfação e entregas. O analista financeiro lê a execução de 2025 e registra as duas séries oficiais, a do quadro e a do texto, sem escolher uma no lugar da outra. O parecerista recebe as duas análises e consolida um parecer com recomendação para a diretoria. A pergunta do experimento é se essa equipe, a história de cada agente e a saída estruturada melhoram o parecer em relação a uma única chamada ao mesmo modelo.

## Como foi feito

Foram comparadas quatro configurações, na mesma ordem, em duas rodadas.

A primeira é a chamada única. Uma mensagem ao gpt-5.6-luna, sem CrewAI. O pedido é um parecer técnico sobre o Programa 536, com os três eixos e uma recomendação explícita, e o dossiê vai inteiro na mesma mensagem.

As outras três são a mesma equipe, em sequência, sem delegação. O financeiro recebe a tarefa técnica em contexto. O parecerista recebe as duas. Os tetos são cinco iterações, dez requisições por minuto e cento e oitenta segundos por agente.

O que muda entre elas é o que o agente carrega. Sem a história profissional, que o CrewAI chama de backstory, cada um só ouve o papel: “você atua como analista técnico”, e o equivalente para os outros dois. Com backstory, cada um recebe a história profissional. O engenheiro confronta o realizado com a meta e nomeia o mês que puxou a média antes de falar em arquitetura. O contador já devolveu relatório em que o quadro e o texto não fechavam. O procurador só recomenda o que o RAG público sustenta e aponta contrato em tramitação e dado sigiloso. Na quarta configuração essa história continua, e a última tarefa devolve um objeto `Parecer`, com síntese, três aspectos, recomendação e pontos de atenção. Outro sistema lê esse objeto sem interpretar prosa.

A medição tem duas camadas, e as duas foram definidas antes de olhar o parecer. A rubrica, em `src/dados/rubrica.json`, tem seis itens e só procura termo ou número no texto: 99,47%, 99,80%, 89,82%, a dotação de R$ 101.311.882,00, a Lei Geral de Proteção de Dados (LGPD) ou o Selo Diamante, e a palavra recomendação. Cada item vale um ponto. A fidelidade, se a frase se apoia no dossiê, fica com o juiz. O juiz é o gpt-5.6-terra. Ele dá de 1 a 5 em fidelidade e em utilidade. Fidelidade 5 significa que toda afirmação se apoia no dossiê. Utilidade 5 significa que a diretoria decidiria com base naquele texto.

O custo da coluna em dólar cobre só a geração do parecer, no preço curto da aula: US$ 0,20 por milhão de tokens de entrada e US$ 1,20 por milhão de tokens de saída do gpt-5.6-luna. A chamada do juiz entra nas notas e fica de fora do dólar.

## Rodada 1

Na primeira rodada as quatro configurações fecharam a rubrica em 6 de 6. A chamada única e a equipe com backstory receberam 5 e 5 do juiz. A equipe sem história perdeu um ponto de fidelidade. A saída estruturada ficou em 4 e 4, e foi a mais rápida e a mais barata entre as equipes.

| Configuração                  | Rubrica | Fidelidade | Utilidade | Chamadas | Tokens | Tempo |     US$ |
| ----------------------------- | ------: | ---------: | --------: | -------: | -----: | ----: | ------: |
| Chamada única                 |     6/6 |          5 |         5 |        1 |   5272 | 38.9s | 0.00536 |
| Equipe sem backstory          |     6/6 |          4 |         5 |        9 |  22110 | 39.7s | 0.01664 |
| Equipe com backstory          |     6/6 |          5 |         5 |        9 |  24954 | 40.6s | 0.01928 |
| Backstory e saída estruturada |     6/6 |          4 |         4 |        9 |  20682 | 23.0s | 0.01180 |

A chamada única gastou uma chamada, 5.272 tokens e US$ 0,00536, em 38,9 segundos. O juiz disse que o parecer se apoia no dossiê, distingue a divergência financeira e o não atingimento da disponibilidade, e oferece condicionantes com que a diretoria decide.

A equipe com backstory repetiu 5 e 5. Foram nove chamadas, 24.954 tokens e US$ 0,01928, cerca de 3,6 vezes o custo da chamada única, em 40,6 segundos. O parecer reproduziu as duas séries e propôs encaminhamento para disponibilidade, metodologia de aferição e conciliação orçamentária. O tempo de parede ficou perto do da chamada única. O que cresceu foi o número de chamadas e o token.

Sem a história, a utilidade continuou em 5 e a fidelidade caiu para 4. O juiz apontou conclusões que o dossiê não comprova por inteiro: adequação da arquitetura, admissibilidade jurídica da continuidade e suplementações tratadas como fato.

Com saída estruturada, as notas caíram para 4 e 4. O texto acertou indicadores, valores e riscos, e em parte tratou a conformidade com a LGPD e o Selo Diamante como não comprovada, embora o RAG os vincule, e condicionou a aprovação a documento que o material não exige. O custo caiu para US$ 0,01180 e o tempo para 23 segundos, o menor da rodada.

## Rodada 2

Repeti as quatro configurações na mesma ordem. A rubrica continuou em 6 de 6. As notas do juiz se moveram.

| Configuração                  | Rubrica | Fidelidade | Utilidade | Chamadas | Tokens | Tempo |     US$ |
| ----------------------------- | ------: | ---------: | --------: | -------: | -----: | ----: | ------: |
| Chamada única                 |     6/6 |          5 |         3 |        1 |   4991 | 34.9s | 0.00502 |
| Equipe sem backstory          |     6/6 |          5 |         5 |        9 |  23727 | 40.6s | 0.01758 |
| Equipe com backstory          |     6/6 |          5 |         4 |        9 |  22734 | 34.2s | 0.01687 |
| Backstory e saída estruturada |     6/6 |          4 |         5 |        9 |  23931 | 29.5s | 0.01501 |

A chamada única manteve fidelidade 5 e a utilidade caiu de 5 para 3. O parecer reproduziu dados, metas, incidentes e a divergência, e parou truncado na análise orçamentária, sem um dispositivo final com que a diretoria decida. Custou US$ 0,00502, uma chamada, 34,9 segundos.

Sem backstory, a equipe subiu para 5 e 5: reproduziu resultados, distinguiu as duas apurações e ofereceu condicionantes. Com backstory, a fidelidade ficou em 5 e a utilidade caiu para 4, porque o trecho da análise jurídica terminou incompleto, sem deliberação final consolidada. Com saída estruturada, a utilidade subiu para 5 e a fidelidade ficou em 4: o encaminhamento é claro, e o texto em parte liga o sigilo do plano de negócios à impossibilidade de verificar LGPD e conformidade, além de exigir documento que o dossiê não descreve.

## O que muda de uma rodada para a outra

A tabela seguinte é a nota da rodada 2 menos a nota da rodada 1. Zero é a mesma nota.

| Configuração                  | Fidelidade | Utilidade |
| ----------------------------- | ---------: | --------: |
| Chamada única                 |         +0 |        -2 |
| Equipe sem backstory          |         +1 |        +0 |
| Equipe com backstory          |         +0 |        -1 |
| Backstory e saída estruturada |         +0 |        +1 |

A rubrica não se mexeu. O juiz se mexeu, e o sinal trocou conforme a configuração. A maior queda foi a utilidade da chamada única, dois pontos, porque o texto da segunda rodada chegou incompleto. Com história, a utilidade foi 5 e depois 4. Sem história, a fidelidade foi 4 e depois 5. Saída estruturada ganhou um ponto de utilidade e manteve fidelidade 4.

## O que os números sustentam

A rubrica em 6 de 6, nas quatro configurações e nas duas rodadas, vem da saída esperada de cada tarefa, o campo `expected_output`. Ele já exige 99,47%, 99,80%, 89,82% e a dotação de R$ 101.311.882,00. A história do agente não altera essa busca por termo. Quem mede se o parecer inventou fato é o juiz, e essa nota oscila de uma execução para a outra. A história pessoal, nesta medição, não aparece como ganho estável.

Na primeira rodada, a chamada única e a equipe com backstory empataram em 5 e 5. A chamada custou US$ 0,00536. A equipe custou US$ 0,01928, nove chamadas em vez de uma. Para a diretoria ler prosa, a chamada única chega na mesma nota máxima e custa menos. O que a equipe entrega a mais é o objeto `Parecer`, que outro sistema consome sem reinterpretar o texto, e o ponto em que um guardrail consegue recusar um número.

A conferência humana continua obrigatória na saída do parecerista, antes da assinatura, sobre as duas séries de indicadores e sobre cada valor em reais. O Planejamento e Programação da Despesa (PPD) compara o que foi executado com a dotação inicial. A Capacidade Operacional Financeira da Despesa (COFD) compara o que foi executado com a dotação final. No ensaio da Seção 7.3, registrado em `falhas.md`, a primeira tarefa recebeu a dotação inicial trocada para R$ 201.311.882,00. A última repetiu esse valor e tratou o número como a dotação extraída. O guardrail recusou essa saída uma vez e só aceitou a dotação da Lei Orçamentária Anual (LOA), R$ 101.311.882,00. A assinatura ainda depende de alguém conferir o RAG.
