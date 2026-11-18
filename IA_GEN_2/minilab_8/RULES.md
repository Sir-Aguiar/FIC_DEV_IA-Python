# Estrutura de arquivos

A solução do Mini LAB fica separada da pasta `exemplos/` e da pasta `aulas/`. Os PDFs permanecem em `aulas/`. Os fluxos e o cliente da aula permanecem em `exemplos/` como referência das Seções 4 a 7. O que a turma entrega vive em `fluxos/`, `prompts/`, `dados/`, `src/`, `executar/` e `resultados/`.

O LangFlow desenha o grafo na tela. O repositório guarda esse grafo em JSON, o prompt como documento legível e a evidência que o README cita. Quem abre o repositório encontra a parte do laboratório pelo nome do arquivo.

```text
minilab_8/
├── README.md
├── RULES.md
├── requirements.txt              # langflow, httpx, python-dotenv
├── .env                          # OPENAI_API_KEY, LANGFLOW_API_KEY, LANGFLOW_URL
├── .gitignore                    # .env, langflow-env/, .venv/, __pycache__, langflow.db
│
├── aulas/                        # PDFs da aula; não fazem parte da entrega
│
├── exemplos/                     # material da aula; não alterar para fazer caber a entrega
│   ├── fluxo01-atendimento-professor.json
│   ├── fluxo02-resumo-oficio.json
│   ├── fluxo03-classificador-mensagens.json
│   ├── fluxo04-agente-pesquisa.json
│   └── cliente_api.py
│
├── fluxos/                       # JSON exportados do setor; o que o LangFlow importa e executa
│   ├── atendimento.json          # Parte 2: Chat Input, Prompt, Language Model, Chat Output
│   ├── resumo.json               # Parte 3: a mesma topologia, prompt de extração
│   ├── classificador.json        # Parte 3: a mesma topologia, categorias do setor
│   ├── agente-pesquisa.json      # Parte 4: Simple Agent, busca e leitura de página
│   └── agente-url.json           # desafio opcional: única ferramenta é o componente URL
│
├── prompts/                      # o texto que a tela executa, legível fora do JSON
│   ├── atendimento.md
│   ├── resumo.md
│   ├── classificador.md
│   └── agente-pesquisa.md
│
├── dados/
│   ├── setor.md                  # nome do setor, escopo, categorias e quem revisa
│   ├── perguntas_atendimento.json
│   ├── documento_resumo.txt
│   ├── gabarito_resumo.json
│   ├── mensagens.json
│   └── perguntas_agente.json
│
├── src/
│   ├── __init__.py
│   ├── configuracao.py           # URL, cabeçalhos, tempos e caminhos
│   └── cliente.py                # listar, importar, localizar, rodar, apagar
│
├── executar/
│   ├── importar.py               # envia os JSON de fluxos/ ao servidor
│   └── classificar.py            # Parte 5: cinco mensagens pela API
│
└── resultados/
    ├── reproducao_aula.md        # Parte 2: pergunta da Seção 4.3 no fluxo importado
    ├── bateria_atendimento.md    # seis perguntas, tokens e tempo
    ├── conferencia_resumo.md     # prazo e responsável contra o original
    ├── bateria_classificador.md  # Playground: categoria, tokens e tempo
    ├── comparacao_api.md         # as mesmas cinco mensagens pela API
    ├── custo_agente.md           # duas perguntas, chamadas de ferramenta, tokens e tempo
    └── ficha_governanca.md       # Parte 6: uma linha justificada por item
```

`agente-url.json` só entra na árvore quando o desafio opcional for feito. O README só fala dele nesse caso.

## O que cada arquivo guarda

`dados/setor.md` declara o setor antes de qualquer prompt. Traz o nome do órgão, os assuntos que o atendimento aceita, o que fica fora do escopo, os campos que o resumo precisa extrair e as categorias do classificador, cada uma com o critério em uma frase. Os prompts e as baterias de teste saem dessa declaração. O exemplo da aula é a SEDUC-MT; a entrega usa o setor escrito aqui.

`prompts/atendimento.md`, `prompts/resumo.md`, `prompts/classificador.md` e `prompts/agente-pesquisa.md` são o programa do fluxo, no sentido da Seção 5.3. Cada arquivo abre com o nome do fluxo JSON correspondente e guarda o texto integral colado no Prompt Template ou em Agent Instructions. O texto inclui papel, escopo, formato de saída e a instrução para o caso em que a informação não existe. O mesmo texto precisa estar no campo do nó exportado: o markdown é a leitura humana, o JSON é o que o LangFlow executa.

`fluxos/atendimento.json` é o fluxo montado em tela em branco, com quatro nós e três arestas. Chat Input liga a mensagem do usuário à porta Input do Language Model. Prompt Template liga o prompt à porta System Message. Language Model liga Model Response à porta Inputs do Chat Output. O arquivo não contém a chave do provedor.

`fluxos/resumo.json` e `fluxos/classificador.json` repetem esses quatro nós e essas três arestas. Mudam o texto do prompt e o nome do fluxo. A turma confere a igualdade da topologia olhando `nodes` e `edges`, sem redesenhar o grafo para cada tarefa.

`fluxos/agente-pesquisa.json` parte do modelo Simple Agent. A instrução está em português e pede busca, leitura da página encontrada, resposta curta, citação do endereço e recusa quando a busca não achar. Web Search e URL aparecem em modo de ferramenta, com a saída Toolset ligada à porta Tools. Calculadora e data atual permanecem as chaves do próprio Agent, como na Seção 6.1.

`dados/perguntas_atendimento.json` tem seis objetos, com `n`, `texto` e `espera`. Cinco perguntas cabem no escopo de `setor.md`. Uma fica fora, para mostrar o encaminhamento em vez de uma resposta inventada. `espera` descreve o comportamento, por exemplo encaminhar à instância competente ou recusar o assunto, e não uma frase única do modelo.

`dados/documento_resumo.txt` é um documento do setor com dados pessoais trocados por fictícios. O texto traz pelo menos dois prazos e dois responsáveis, e uma providência sem prazo ou sem responsável. `dados/gabarito_resumo.json` lista cada providência com o responsável e o prazo como estão no original, usando `nao_informado` quando o documento cala.

`dados/mensagens.json` tem cinco mensagens. Três cobrem as categorias do setor, uma por categoria. Duas são ambíguas. Cada objeto traz `texto` e `categoria_esperada`. A categoria esperada das ambíguas registra a leitura que o setor adotou e a dúvida, para o README poder explicar o desempate.

`dados/perguntas_agente.json` tem duas perguntas. `direta` pede um fato localizável numa página. `vaga` pede algo que o agente precisa interpretar, no espírito da matrícula sem data de início da Seção 6.2.

`src/configuracao.py` concentra o que o cliente compartilha: `LANGFLOW_URL` com padrão `http://127.0.0.1:7860`, a leitura de `LANGFLOW_API_KEY`, o tempo limite da chamada e os caminhos de `fluxos/`, `dados/` e `resultados/`. A chave da OpenAI não aparece neste módulo. Ela fica no ambiente que inicia o servidor.

`src/cliente.py` reúne as quatro operações da Seção 7.2: `listar`, `importar`, `rodar` e `apagar`. `localizar` acha o fluxo pelo nome. `rodar` envia `input_value`, `input_type` chat e `output_type` chat para `/api/v1/run/{id}` e devolve o texto da mensagem. O cabeçalho é `x-api-key`. Essa chave autoriza o programa a usar o servidor LangFlow; ela é distinta da chave do provedor de modelo.

`executar/importar.py` percorre os JSON de `fluxos/` e chama `importar`. `executar/classificar.py` lê `dados/mensagens.json`, executa o classificador pelo nome e grava `resultados/comparacao_api.md` com a categoria lida na primeira linha, a justificativa e se coincidiu com `categoria_esperada`. A lógica da chamada fica em `src/cliente.py`. O script só orquestra e imprime o veredito.

`resultados/reproducao_aula.md` registra a pergunta da Seção 4.3 no fluxo importado de `exemplos/`: resposta, tokens e tempo lidos no Playground. Esse arquivo mostra que a topologia da aula foi reproduzida antes da reescrita do prompt.

`resultados/bateria_atendimento.md` tem uma linha por pergunta do setor: texto, resposta obtida, se o comportamento bate com `espera`, tokens e tempo.

`resultados/conferencia_resumo.md` coloca lado a lado cada prazo e cada responsável do gabarito e o que o fluxo escreveu. A linha da providência sem dado no original marca se a saída trouxe `não informado` ou um valor que o documento não contém.

`resultados/bateria_classificador.md` é a tabela do enunciado preenchida no Playground: fluxo, mensagem, categoria obtida, se a resposta está correta, tokens e tempo. `resultados/comparacao_api.md` repete as cinco mensagens pela API e diz, mensagem a mensagem, se a categoria coincidiu com a do Playground.

`resultados/custo_agente.md` transcreve a tela Flow Activity e as linhas de ferramenta do Playground. Para cada pergunta: texto, lista de chamadas com nome da ação, tokens, duração e a resposta. A explicação da diferença fica nesse arquivo, contando as chamadas, e o README a retoma.

`resultados/ficha_governanca.md` tem quatro linhas, uma por decisão da Parte 6: destino dos textos, prazo de retenção no banco do LangFlow, quem revisa a resposta antes de ela sair em nome do setor, e onde o prompt fica guardado e versionado.

## Dependências entre módulos

```text
dados/setor.md
    ├── prompts/*.md
    │       └── fluxos/*.json
    └── dados/*.json e dados/*.txt
            └── resultados/*.md

configuracao.py
    └── cliente.py
            ├── executar/importar.py      → servidor LangFlow
            └── executar/classificar.py   → resultados/comparacao_api.md
```

`cliente.py` não importa os experimentos uns dos outros. Importar um fluxo não dispara a bateria do classificador. Os números do Playground e do Flow Activity são copiados para `resultados/` porque a interface é o instrumento de medida dessas partes. O script só mede o que a API devolve.

# Comentários

Toda decisão lógica em Python deve ser comentada de maneira explicativa.

O comentário diz por que a decisão existe e a qual parte do Mini LAB ela responde. Um comentário útil nomeia o efeito tratado na aula: a chave do provedor fica no ambiente e não no JSON; a chave `x-api-key` autoriza o servidor LangFlow e não substitui a chave do modelo; as três variações de prompt compartilham nós e arestas; o agente gasta tokens na medida das ferramentas que chama. O comentário fica junto da função, em português, em frases completas.

O JSON do LangFlow não recebe comentário. A explicação do grafo fica no README e a explicação do texto fica no markdown de `prompts/`, ao lado do fluxo que o executa.

# Estilo

Deve haver espaçamento satisfatório entre linhas de funções, entre classes, fluxos e funções.

Uma função por responsabilidade. Linha em branco entre funções e entre os passos de um fluxo: montar o cliente, localizar o fluxo, enviar a mensagem, ler a categoria, gravar o resultado. Constantes de URL, tempo limite e caminhos ficam no topo de `configuracao.py`. Nomes de funções e de arquivos em português, alinhados às partes do enunciado.

Os prompts seguem o mesmo cuidado da Seção 5.3: papel definido, escopo delimitado, formato de saída explícito e instrução para a informação ausente. No classificador, a primeira linha é só a categoria, para a API e o fluxo seguinte lerem sem ambiguidade.

# Como escrever o README.md

O README é o texto pelo qual a turma acompanha a solução sem abrir o canvas e sem percorrer o JSON inteiro. Ele explica o problema do setor, a forma do grafo, a decisão que está no prompt e a evidência medida. Cada decisão aponta o arquivo em que está escrita. Números, categorias e trechos de resposta vêm de `resultados/`. O README não antecipa um resultado que o Playground, o Flow Activity ou `classificar.py` ainda não produziram.

Escreva em português, em parágrafos curtos, na ordem das partes do Mini LAB. Cada seção abre com a decisão em uma frase e, em seguida, mostra como o fluxo a realiza e o que a execução mostrou.

## Seções obrigatórias

1. **Problema.** A coordenadoria recebe demandas repetidas e a equipe resolve cada texto colando num assistente de conversa. Nomeie as quatro falhas desse procedimento: o pedido muda de servidor para servidor, o resultado não fica registrado, ninguém sabe o custo e dados pessoais saem sem política de uso. Feche com o que o laboratório entrega no lugar: quatro fluxos em arquivo, o prompt como documento e cada execução anotada com tokens e duração. Diga o setor de `dados/setor.md` na primeira menção.

2. **Como executar.** Liste `requirements.txt` (`langflow`, `httpx`, `python-dotenv`) e as variáveis `OPENAI_API_KEY`, `LANGFLOW_API_KEY` e `LANGFLOW_URL`. Explique a ordem: carregar o `.env` no terminal, subir o servidor com `uv run langflow run`, confirmar o provedor em Settings e Model Providers sem digitar a chave, criar a chave do LangFlow e só então rodar `python executar/importar.py` e `python executar/classificar.py`. Diga que a chave do provedor inicia o servidor e a chave `x-api-key` autoriza o cliente. Aponte o aviso da aula: um `.env` acima da pasta do projeto com `OPENAI_API_BASE` apontando para um servidor desligado faz o modelo falhar com "Connection error".

3. **O fluxo como grafo.** Explique, com o atendimento do setor, as três ligações da Seção 4.1: a pergunta entra como mensagem do usuário, o prompt entra como mensagem de sistema, a resposta do modelo segue para o Chat Output. Relacione essa separação ao que a API do provedor espera. Mostre que `fluxos/atendimento.json` tem quatro nós e três arestas e que a chave não viaja no arquivo. Um trecho curto do README pode nomear as portas; o JSON completo fica no arquivo.

4. **O prompt como programa.** Mostre que atendimento, resumo e classificador usam os mesmos quatro componentes e as mesmas três ligações, e que o que muda é o texto em `prompts/`. Cite, de cada prompt, o papel, o limite de formato e a frase que impede inventar prazo, norma ou categoria. Aponte que esse texto é o campo Template ou Agent Instructions do JSON de mesmo nome. Trate o prompt como documento do setor: responsável, versão e arquivo versionado, que é o item da ficha de governança sobre onde o prompt fica guardado.

5. **Atendimento medido.** Reproduza a tabela de `resultados/bateria_atendimento.md`: pergunta, se o comportamento esperado ocorreu, tokens e tempo. Interprete dois fatos com os números próprios. A pergunta dentro do escopo recebe orientação geral e, quando a norma não está no fluxo, encaminha em vez de citar artigo ou prazo. A pergunta fora do escopo recusa o assunto. Se a reprodução da Seção 4.3 foi feita, um parágrafo curto aponta `resultados/reproducao_aula.md` e o total de tokens lido no fluxo de exemplo, antes de passar à bateria do setor. Diga o que o fluxo não faz: não há Message History, então a segunda pergunta não herda a primeira, e não há consulta a norma, tema da aula seguinte.

6. **Resumo conferido.** Descreva o documento de `dados/documento_resumo.txt` em poucas linhas, sem colar dados que o gabarito já isola. Mostre a tabela de `resultados/conferencia_resumo.md`: providência, responsável no original, prazo no original, responsável extraído, prazo extraído. Destaque a linha em que o documento não informa o campo. O leitor precisa ver se a saída escreveu "não informado" ou se preencheu um valor ausente do texto. Essa conferência é o que torna o resumo utilizável no setor.

7. **Classificador.** Explique as categorias a partir de `dados/setor.md`, com o critério de cada uma em uma frase. Reproduza a tabela do enunciado que está em `resultados/bateria_classificador.md`: mensagem, categoria obtida, acerto, tokens e tempo. Comente as duas mensagens ambíguas: diga qual categoria saiu e por que o critério do prompt desempatou, ou registre que as duas execuções divergiram. Lembre que a primeira linha em maiúsculas existe para um programa ler a categoria sem ambiguidade.

8. **Agente e custo.** Conte as duas perguntas de `dados/perguntas_agente.json`. Para cada uma, liste as chamadas de ferramenta transcritas em `resultados/custo_agente.md`, os tokens e o tempo do Flow Activity. A decisão da seção é a da Seção 6.2: o agente custa o que as ferramentas o levam a consumir. Mostre a razão entre a pergunta vaga e a pergunta direta com os números da execução. Feche dizendo que a resposta cita a fonte e que o servidor abre essa fonte antes de repassar o texto, porque o agente resume o que leu. Se Max Iterations foi alterado do padrão, diga o valor e em qual campo do JSON ele está.

9. **Arquivo e API.** Diga que os quatro JSON estão em `fluxos/` e que `importar.py` os envia ao servidor. Mostre um trecho curto de `rodar` em `src/cliente.py`: o corpo com `input_value` e a leitura do texto em `outputs`. Reproduza a comparação de `resultados/comparacao_api.md`: as cinco mensagens, a categoria no Playground, a categoria na API e se coincidiram. Se uma mensagem divergiu, registre as duas saídas. A separação a defender é a da Seção 7.2: quem conhece o trabalho ajusta o fluxo na tela, e quem conhece os sistemas o chama pela rede.

10. **Ficha de governança.** Reproduza `resultados/ficha_governanca.md`. Cada linha justifica a escolha com um fato do laboratório. Os quatro itens são: para onde vão os textos enviados aos fluxos, por quanto tempo as mensagens ficam no banco do LangFlow, quem revisa as respostas antes de saírem em nome do setor, e onde o prompt de cada fluxo fica guardado e versionado. O destino dos textos nomeia o provedor cadastrado em Model Providers, ou Ollama quando o texto não pode sair da máquina. A revisão humana nomeia o papel no setor, porque o Playground testa e a API integra, e nenhum dos dois é o canal público. O versionamento aponta `prompts/` e o JSON em `fluxos/`. Se o desafio opcional foi feito, um parágrafo mostra que `fluxos/agente-url.json` só liga o componente URL à página oficial do órgão e que as respostas citaram essa fonte.

11. **O que a turma deve conseguir defender.** Feche com cinco frases que um colega conseguiria repetir. O atendimento é um grafo de quatro componentes e três ligações, com o prompt na mensagem de sistema. Resumo e classificador reutilizam esse grafo e mudam o prompt. O agente da pesquisa gastou mais na pergunta vaga porque fez mais chamadas de ferramenta, com os dois totais de tokens nomeados. O fluxo versionado é o JSON, executado pela API sem abrir a tela, e a chave do provedor permanece no ambiente. A resposta só sai em nome do setor depois da revisão humana definida na ficha.

## Tom e evidência

Escreva como quem apresenta o desenho à turma: decisão, medida, arquivo. Evite descrever o LangFlow em abstrato sem amarrar ao setor de `dados/setor.md`. Quando um comportamento da aula se repetir na execução, diga que o fluxo do setor reproduziu esse comportamento e mostre o número ou o trecho: o modelo encaminha em vez de inventar prazo, o resumo marca "não informado", a pergunta vaga do agente consome bem mais tokens que a direta, o JSON exportado não traz a chave. Quando não se repetir, registre o que saiu no Playground ou na API.

Trechos de código no README são curtos e servem para localizar a decisão: as três ligações, a frase do prompt que barra a informação inventada, a função `rodar` e a leitura da primeira linha do classificador. O restante da leitura fica no arquivo indicado. O JSON do fluxo não é colado inteiro. A turma lê a topologia pela contagem de nós e arestas e o programa pelo markdown em `prompts/`.
