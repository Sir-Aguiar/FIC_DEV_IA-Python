# Minilab 4 — Equipe sobre o Relatório Anual de Gestão (RAG) 2025 da Empresa Mato-grossense de Tecnologia da Informação (MTI)

O roteiro para ler em voz alta, com as tabelas e a leitura dos números, está em [`resultados.md`](resultados.md). Este arquivo abre o trabalho e diz como reproduzir a medição.

## O que o trabalho responde

A diretoria da Empresa Mato-grossense de Tecnologia da Informação (MTI) precisa decidir o que o Relatório Anual de Gestão (RAG) de 2025 sustenta sobre o Programa 536, Tecnologia da Informação e Comunicação (TIC) para o governo. O relatório público mostra disponibilidade de 99,47% abaixo da meta de 99,80%, satisfação de 89,82% acima da meta de 75% e duas apurações orçamentárias que não fecham a mesma conta. Um parecer útil separa o eixo técnico, o financeiro e o jurídico. Um parecer que funde as duas séries, ou que repete um número recebido da etapa anterior, leva a diretoria a decidir sobre um dado que o dossiê não confirma.

O material de trabalho é o dossiê de uma página em `src/dados/dossie_projeto.md`, extraído do RAG publicado em [rag-2025-pdf](https://www.mti.mt.gov.br/documents/d/mti/rag-2025-pdf). O plano de negócios da empresa está classificado como sigiloso e não entra na análise.

Três agentes leem esse dossiê em sequência. O técnico avalia disponibilidade, satisfação e entregas. O financeiro avalia a execução de 2025 e registra as duas séries oficiais. O parecerista consolida as duas análises num parecer com recomendação. A medição compara essa equipe com uma chamada única ao mesmo modelo, com e sem a história de cada agente, e com a última tarefa devolvendo um objeto estruturado.

## Como reproduzir

O CrewAI, biblioteca que organiza a equipe de agentes, nesta versão exige Python 3.10 a 3.13. O interpretador usado aqui é o 3.12 em `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`. A chave `OPENAI_API_KEY`, credencial de acesso à interface de programação do modelo, fica no `.env` da raiz do minilab. Os comandos partem dessa raiz.

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m pip install crewai openai python-dotenv pydantic
& $py src\equipe.py
& $py src\experimento.py
& $py src\falhas.py
```

`src\equipe.py` gera um parecer estruturado no terminal. `src\experimento.py` roda as quatro configurações duas vezes e reescreve as tabelas de `resultados.md`. `src\falhas.py` planta a dotação errada, compara a delegação entre agentes (`allow_delegation`) e reescreve `falhas.md`. As duas últimas chamadas gastam a interface de programação e levam alguns minutos. O texto de apresentação que envolve as tabelas em `resultados.md` foi escrito para esta medição: uma nova execução do experimento substitui o arquivo pelas tabelas da rodada nova.

A rubrica de seis itens, em `src/dados/rubrica.json`, foi escrita antes da execução e só procura termo ou número no texto. A fidelidade fica com o juiz, o gpt-5.6-terra. A geração do parecer usa o gpt-5.6-luna. Nenhum agente delega. Os tetos são `max_iter` 5, `max_rpm` 10 e `max_execution_time` de 180 segundos. A análise financeira recebe a tarefa técnica em `context`. O parecerista recebe as duas e, na configuração estruturada, é o único com `output_pydantic`.

`falhas.md` registra o ensaio da Seção 7.3. A primeira tarefa recebeu a dotação inicial trocada para R$ 201.311.882,00 e a última repetiu o número. Com `allow_delegation` verdadeiro, a mesma tarefa passou de 6 para 12 chamadas. O guardrail em `src/falhas.py` recusou esse valor e só aceitou a dotação da Lei Orçamentária Anual (LOA), R$ 101.311.882,00.

## Quem fala na equipe

### Analista Técnico

- **Papel:** Analista Técnico.
- **Objetivo:** avaliar disponibilidade, satisfação e entregas do Programa 536.
- **História:** engenheiro da MTI que acompanha o painel dos 19 serviços críticos desde a implantação do monitoramento. Confronta o realizado com a meta de 99,80% e nomeia o mês que puxou a média para baixo antes de falar em arquitetura.

### Analista Financeiro

- **Papel:** Analista Financeiro.
- **Objetivo:** avaliar a execução orçamentária do Programa 536 no exercício de 2025.
- **História:** contador da execução do Plano Plurianual (PPA) que já devolveu relatório em que o quadro e o texto não fechavam a mesma conta. Registra as duas séries oficiais do RAG, a do quadro e a da análise, sem escolher uma no lugar da outra.

### Parecerista

- **Papel:** Parecerista.
- **Objetivo:** consolidar as análises em parecer com recomendação para a diretoria.
- **História:** procurador que há anos assina parecer sobre prestação de contas de empresa estatal. Só recomenda o que o RAG público sustenta e aponta contrato ainda em tramitação e dado sigiloso que o dossiê não abre.
