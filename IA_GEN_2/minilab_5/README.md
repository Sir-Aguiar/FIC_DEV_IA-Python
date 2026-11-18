# O que a forma do gerente mudou na triagem

Seis manifestações do setor de TI da Empresa Mato-grossense de Tecnologia da Informação (MTI) chegaram sem especialista marcado. A área esperada de cada uma já estava registrada e não entrou no texto da tarefa. A equipe foi montada duas vezes no processo hierárquico do CrewAI. Nas duas, as tarefas não nomeavam agente: quem escolhe o especialista é o gerente.

Na primeira execução, o parâmetro `manager_llm` pede ao framework que crie o gerente a partir do modelo, com a história genérica que o próprio framework traz. Na segunda, o parâmetro `manager_agent` recebe um gerente escrito por nós. A história dele traz a regra do setor: cada manifestação vai a um único especialista, escolhido pelo assunto, e a minuta desse especialista é a resposta final.

A regra separa os assuntos assim: Prazo de chamado já aberto fica com a central de serviços. Queda de conexão fica com infraestrutura e redes. Uso indevido de credencial fica com segurança da informação. Falha de tela, de módulo ou de anexo fica com sustentação de sistemas. Número de outro órgão no painel fica com dados. Revogação de conta ou de perfil fica com gestão de acessos.

O gerente criado pelo framework fez 26 chamadas ao modelo. O gerente escrito fez 18. A contagem é o quanto o contador do modelo subiu do início ao fim de cada execução. Cada área abaixo é o papel de um analista da empresa.

## Gerente criado pelo framework

| Manifestação | Área esperada           | Consultas, na ordem                                                  |
| ------------ | ----------------------- | -------------------------------------------------------------------- |
| MTI1         | central de serviços     | central de serviços; central de serviços; infraestrutura e redes     |
| MTI2         | infraestrutura e redes  | infraestrutura e redes; sustentação de sistemas; central de serviços |
| MTI3         | segurança da informação | segurança da informação                                              |
| MTI4         | sustentação de sistemas | sustentação de sistemas; central de serviços; infraestrutura e redes |
| MTI5         | dados e banco de dados  | sustentação de sistemas; dados e banco de dados                      |
| MTI6         | gestão de acessos       | sustentação de sistemas; gestão de acessos; segurança da informação  |

26 chamadas ao modelo.

A repetição da central de serviços na primeira manifestação conta como um único especialista. A ida seguinte, à infraestrutura, é o que torna a consulta múltipla. Com esse critério, o gerente automático consultou mais de um especialista em 5 das 6 manifestações: MTI1, MTI2, MTI4, MTI5 e MTI6. Só o relato de uso indevido de credencial ficou com um único especialista.

## Gerente escrito com a regra do setor

| Manifestação | Área esperada           | Consulta                |
| ------------ | ----------------------- | ----------------------- |
| MTI1         | central de serviços     | central de serviços     |
| MTI2         | infraestrutura e redes  | infraestrutura e redes  |
| MTI3         | segurança da informação | segurança da informação |
| MTI4         | sustentação de sistemas | sustentação de sistemas |
| MTI5         | dados e banco de dados  | dados e banco de dados  |
| MTI6         | gestão de acessos       | gestão de acessos       |

18 chamadas ao modelo.

Cada manifestação foi a um único especialista, e esse especialista era o da área esperada. As duas fronteiras da regra apareceram aqui: o chamado atrasado sobre o código que não chega no celular foi para a central de serviços, e o desligamento formal de conta foi para a gestão de acessos.

## Leitura

O gerente automático consultou mais de um especialista em 5 manifestações. O gerente com a regra do setor na história consultou um em todas as seis, acertou a área esperada nas seis e gastou 18 chamadas, contra 26 da execução anterior.

## Tratamento da conta citada na manifestação

A rotina decide o que fazer quando a manifestação fala de uma conta. O estado é a classe `EstadoDoTratamento`. Dois métodos de partida correm ao mesmo tempo: um abre o registro e o outro confere, em código, se o relato tem corpo e cita conta, acesso, chamado, perfil ou credencial. `and_` só libera o roteador quando os dois terminaram. O roteador devolve um de três rótulos, e `or_` junta os ramos no encerramento.

`acompanhar_chamado` vale quando já existe chamado e a pessoa cobra prazo. `registrar_incidente` vale quando a conta foi usada fora do padrão. `revogar_acessos` vale quando há pedido formal para desligar conta ou perfil.

O incidente é o ramo mais trabalhoso. O método chama uma equipe sequencial e passa o relato, o canal, o registro e o motivo por entradas da equipe. O analista de segurança registra o fato. O analista da central de serviços redige a resposta a partir desse registro. O consumo dessa equipe fica no campo `token_usage` do estado. Na manifestação MTI3 foram 2 chamadas, uma para cada analista.

A revogação é o desfecho que exige assinatura. O parecer humano tem dois resultados, `assinada` e `reter`, e o conservador, `reter`, é o resultado usado quando não há um parecer claro. O estado é gravado a cada etapa. Na manifestação MTI6 o primeiro parecer reteve a revogação e pediu ajuste. O segundo assinou. O estado foi relido depois da assinatura, e o histórico está completo: os dois pareceres, na mesma ordem, com a assinatura por último.

| Manifestação | Desfecho            | Esperado            | Ramo                | Chamadas da equipe | Pareceres |
| ------------ | ------------------- | ------------------- | ------------------- | ------------------ | --------- |
| MTI1         | acompanhar_chamado  | acompanhar_chamado  | acompanhar          | 0                  | 0         |
| MTI3         | registrar_incidente | registrar_incidente | registrar_incidente | 2                  | 0         |
| MTI6         | revogar_acessos     | revogar_acessos     | revogar             | 0                  | 2         |

Na triagem das manifestações não se sabia qual especialista receberia cada uma, e isso pediu o processo hierárquico, em que um gerente escolhe quem executa. Na abertura do tratamento da conta, o registro e a conferência do relato podiam correr juntos, e a etapa seguinte só começava com os dois prontos, o que pediu o fluxo com `and_`. No tratamento da conta não se sabia se o desfecho seria acompanhamento, incidente ou revogação, e isso pediu o roteador, que escolhe um único ramo. No incidente, depois de escolhido o ramo, a ordem era conhecida, primeiro o fato e depois a resposta, e isso pediu a equipe sequencial. Na revogação não se sabia se a minuta seria assinada ou retida, e isso pediu o parecer humano do fluxo, que devolve a minuta quando o desfecho é reter.

A regra escrita na história do gerente é que cada manifestação vai a um único especialista. Na execução das seis manifestações, o gerente criado pelo framework fez 26 chamadas e o gerente com essa regra fez 18. A diferença medida é de 8 chamadas por execução.

A conferência humana é obrigatória na minuta que desliga conta e perfil, antes de a revogação ser marcada como assinada. O `@human_feedback` do fluxo serve melhor nesse ponto porque o texto da pessoa vira um de dois caminhos, assinar ou reter, a falta de um parecer claro cai no caminho conservador, e o estado gravado permite reler o histórico depois. O `human_input` da tarefa pede apenas que a pessoa aceite o texto daquela tarefa antes de ela terminar, e a resposta permanece dentro da tarefa, sem escolher o método seguinte do fluxo.

## Como executar

Os comandos partem da pasta do minilab, com o ambiente virtual já criado em `.venv`. A versão do Python desse ambiente é a 3.12, porque a versão atual do CrewAI exige uma anterior à 3.14. A chave do provedor do modelo fica no arquivo `.env`, na variável `OPENAI_API_KEY`.

No PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python src\main.py
python src\fluxo.py
```

`src\main.py` compara os dois gerentes da triagem. Roda as seis manifestações duas vezes e imprime, para cada uma, a área esperada, os especialistas consultados e o total de chamadas daquela execução. `src\fluxo.py` trata as manifestações MTI1, MTI3 e MTI6. Imprime o desfecho, o ramo, as chamadas da equipe do incidente e, na revogação, relê o estado gravado para conferir o histórico de pareceres. Os pareceres da revogação já estão escritos no código, em sequência: o primeiro pede para reter e o segundo assina. Nenhum dos dois programas espera texto digitado.

Os agentes não têm um comando próprio. Estão em `src\setor_ti.py` e entram quando um dos programas acima os chama. São seis, um por área: central de serviços, infraestrutura e redes, segurança da informação, sustentação de sistemas, dados e banco de dados, e gestão de acessos. Nenhum deles delega. O coordenador da triagem está em `src\main.py` e é o único que delega. Na segunda execução de `src\main.py`, a equipe é a dos seis analistas e o coordenador distribui o trabalho. Na primeira, o framework cria o gerente. Em `src\fluxo.py`, a equipe do incidente usa só o analista de segurança e o da central de serviços, nessa ordem.

As funções de `src\setor_ti.py` preparam os dados. `carregar_manifestacoes` lê o arquivo de manifestações. `registrar_areas_esperadas` copia o gabarito de área antes de qualquer execução.

As funções de `src\main.py` medem a triagem. `montar_tarefas` cria uma tarefa por manifestação, sem agente e sem a área esperada. `executar` zera o registro de delegações, roda a equipe e devolve quantas chamadas o modelo fez. `marcar_tarefa` e `anotar_delegacao` escutam os eventos e anotam a quem cada manifestação foi entregue. `tabela` junta o gabarito com essas consultas. `imprimir_tabela` mostra o resultado. `mais_de_um_especialista` lista as manifestações em que o gerente consultou mais de um papel. `chamadas_do_modelo` lê o contador do modelo compartilhado. `identificar` casa o nome visto no evento com o identificador da manifestação.

As funções de `src\fluxo.py` conduzem o tratamento da conta. `redigir` pede uma minuta curta ao modelo. `equipe_de_incidente` monta a equipe sequencial do ramo mais trabalhoso. `anotar_parecer` guarda um parecer no estado, sem repetir o último. `historico_completo` confere se o estado relido tem cada parecer da execução e se o último assina. Dentro do fluxo, `abrir` cria o registro, `conferir_relato` valida o texto em código, `decidir` escolhe o rótulo, `acompanhar` responde o chamado já aberto, `anotar_incidente` chama a equipe e grava `token_usage`, `propor_revogacao` redige a minuta que pede assinatura, `efetivar` marca a revogação como assinada e `encerrar` reúne os três ramos.

A execução usou Python 3.12. A versão atual do CrewAI exige uma versão do Python anterior à 3.14.

