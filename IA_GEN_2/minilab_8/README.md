# Mini LAB 8 — Central de Atendimento de TI da MTI

A Central de Atendimento de TI da Empresa Mato-grossense de Tecnologia da Informação (MTI) recebe pedidos repetidos de conta de rede, senha, estações, impressoras, VPN e acesso a sistemas. O escopo, o que fica de fora e quem revisa a resposta estão em `dados/setor.md`.

## Problema

A equipe resolvia cada texto colando num assistente de conversa. Esse procedimento tem quatro falhas: o pedido muda de servidor para servidor, o resultado não fica registrado, ninguém sabe o custo e dados pessoais saem sem política de uso.

No lugar disso, o laboratório entrega quatro fluxos em arquivo, o prompt como documento e cada execução anotada com tokens e duração. Os arquivos medidos estão em `resultados/`.

## Como executar

As dependências estão em `requirements.txt`: `langflow`, `httpx` e `python-dotenv`. O LangFlow 1.13 desta entrega pede Python de 3.10 até 3.14. O ambiente usado aqui foi criado com `uv`.

O `.env` na raiz do projeto, e só nesta máquina, precisa destas variáveis:

```text
OPENAI_API_KEY=
LANGFLOW_URL=http://127.0.0.1:7860
LANGFLOW_AUTO_LOGIN=true
LANGFLOW_SUPERUSER=langflow
LANGFLOW_SUPERUSER_PASSWORD=
LANGFLOW_API_KEY=
```

`LANGFLOW_SUPERUSER_PASSWORD` não pode ser a senha antiga `langflow`: o servidor 1.13 recusa a subida sem uma senha nova. `LANGFLOW_API_KEY` só existe depois do passo 4. O arquivo está no `.gitignore` e não entra no repositório.

A ordem é esta, a partir da pasta do projeto:

1. Carregue o `.env` no terminal que vai iniciar o servidor: `set -a; source .env; set +a`.
2. Suba o servidor com a chave do provedor já no ambiente: `uv run --python .venv/bin/python langflow run --host 127.0.0.1 --port 7860`.
3. Abra `http://127.0.0.1:7860`, vá em Settings → Model Providers e confirme que a OpenAI aparece configurada, com a chave mascarada. A chave não é digitada na tela.
4. Em Settings → Langflow API Keys, crie uma chave, grave o valor em `LANGFLOW_API_KEY` no `.env` e habilite o modelo `gpt-6-luna` na lista da OpenAI, se ele ainda não estiver marcado. Os JSON apontam para esse modelo.
5. Com o servidor no ar, rode uma vez `.venv/bin/python executar/importar.py` e depois `.venv/bin/python executar/classificar.py`.

A chave da OpenAI inicia o servidor e autoriza o modelo. A chave `x-api-key` (`LANGFLOW_API_KEY`) autoriza o cliente em `src/cliente.py` a chamar o servidor. São chaves diferentes.

Um `.env` acima da pasta do projeto com `OPENAI_API_BASE` apontando para um servidor desligado faz o modelo falhar com "Connection error". Remova essa variável ou use o endereço oficial da OpenAI.

Rodar `executar/importar.py` de novo cria uma segunda cópia de cada fluxo. `localizar` fica com a mais recente, mas a tela enche de duplicatas.

Para classificar uma mensagem avulsa, o cliente da Seção 7.2 é o da pasta `exemplos/`:

```bash
.venv/bin/python exemplos/cliente_api.py listar
.venv/bin/python exemplos/cliente_api.py rodar "Classificador TI MTI" "A VPN caiu agora."
```

Os comandos `importar` e `apagar` do mesmo cliente existem para um arquivo ou um nome. Apagar remove o fluxo do servidor, não o JSON da pasta.

## Em outra máquina

O que viaja é o repositório: `fluxos/`, `prompts/`, `dados/`, `src/`, `executar/`, `exemplos/` e `resultados/`. O que não viaja, e precisa ser recriado no destino, é o `.env`, a pasta `.venv`, o banco `langflow.db` e as mensagens do Playground. O `.gitignore` já deixa esses três de fora.

No destino:

1. Instale o `uv` e um Python entre 3.10 e 3.14.
2. Na pasta do projeto, crie o ambiente e instale as dependências: `uv venv --python 3.12 .venv` e `uv pip install -r requirements.txt --python .venv/bin/python`.
3. Crie um `.env` novo, com a `OPENAI_API_KEY` dessa instalação e uma `LANGFLOW_SUPERUSER_PASSWORD` que não seja `langflow`. Deixe `LANGFLOW_API_KEY` vazio até a tela gerar a chave.
4. Carregue o `.env`, suba o servidor e confirme a OpenAI em Settings → Model Providers sem colar a chave na interface.
5. Crie a chave do LangFlow nessa instalação e habilite `gpt-6-luna`. A chave de outra máquina não serve: ela autoriza o banco daquele servidor.
6. Rode `executar/importar.py` uma vez. O servidor atribui ids novos. Os arquivos em `fluxos/` não trazem a chave do provedor.
7. Rode `executar/classificar.py` para repetir as cinco mensagens. Tokens e tempo mudam de execução para execução. As categorias medidas nesta entrega estão em `resultados/` e não são regravadas por esse script, que só reescreve `resultados/comparacao_api.md`.

Se o servidor estiver em outra máquina da rede, `LANGFLOW_URL` no `.env` do cliente aponta para esse endereço, por exemplo `http://192.168.0.20:7860`. O processo do LangFlow precisa ter sido iniciado com `OPENAI_API_KEY` no ambiente dele, e a `LANGFLOW_API_KEY` tem de ser uma chave criada nesse servidor.

O agente de pesquisa precisa de saída para a internet: a busca é DuckDuckGo e a leitura de página acessa o portal da MTI. Sem rede, atendimento, resumo e classificador continuam, porque só chamam o modelo. Um texto que não possa sair do órgão não usa esta instalação OpenAI; o caminho da ficha, nesse caso, é Ollama na própria máquina.

## O fluxo como grafo

No atendimento do setor, a pergunta entra como mensagem do usuário, o prompt entra como mensagem de sistema e a resposta do modelo segue para o Chat Output. É a separação que a API do provedor espera: uma mensagem de sistema e uma mensagem de usuário.

`fluxos/atendimento.json` tem quatro nós e três arestas. A porta de mensagem do Chat Input liga na porta Input do Language Model. O Prompt Template liga na porta System Message. Model Response liga na porta Inputs do Chat Output. A chave da OpenAI não viaja nesse arquivo.

## O prompt como programa

Atendimento, resumo e classificador usam esses quatro componentes e essas três ligações. O que muda é o texto em `prompts/`, copiado para o campo Template do JSON de mesmo nome. No agente, o texto vai para Agent Instructions.

O atendimento se apresenta como assistente da central de TI da MTI, responde em no máximo quatro frases e, se não conhecer norma, prazo ou número de chamado, diz isso e encaminha, sem inventar números, datas ou artigos. O resumo lista cada providência com responsável e prazo e escreve "não informado" quando o documento cala. O classificador só aceita INCIDENTE, REQUISICAO ou DUVIDA, desempata pela interrupção do trabalho e põe só a categoria, em maiúsculas, na primeira linha.

Esse texto é documento do setor. Quem responde por ele é a coordenação da Central de Atendimento de TI da MTI. A leitura humana fica em `prompts/` e a cópia que o LangFlow executa fica em `fluxos/`, os dois versionados no repositório.

## Atendimento medido

A reprodução da Seção 4.3, no fluxo de exemplo da SEDUC-MT, está em `resultados/reproducao_aula.md`. A pergunta da remoção no meio do ano letivo usou 307 tokens em 2,9 s. A resposta encaminhou à DRE ou ao RH da escola e não inventou prazo.

A bateria do setor, em `resultados/bateria_atendimento.md`:

| n | Pergunta | Comportamento esperado | Tokens | Tempo |
| --- | --- | --- | --- | --- |
| 1 | Esqueci a senha da conta de rede. Como recupero o acesso? | Sim. Orientou a redefinição pela central e não fixou prazo. | 238 | 1,7 s |
| 2 | Meu computador não liga depois da queda de energia. O que faço? | Sim. Deu checagens gerais e mandou abrir chamado, sem protocolo nem prazo. | 340 | 3,2 s |
| 3 | A VPN da MTI não conecta no trabalho remoto. Por onde começo? | Sim. Orientou a verificação geral e encaminhou o erro persistente. | 336 | 2,6 s |
| 4 | Preciso de acesso ao sistema de protocolo eletrônico. Quem libera? | Sim. Encaminhou a liberação à central, sem artigo nem prazo. | 306 | 2,2 s |
| 5 | A impressora do setor está offline desde hoje cedo. Como registro isso? | Sim. Explicou o registro do chamado e não inventou o número. | 247 | 1,7 s |
| 6 | Qual o valor do auxílio-alimentação dos servidores da MTI neste mês? | Sim. Recusou o assunto e indicou Gestão de Pessoas, sem informar valor. | 277 | 2,0 s |

As cinco perguntas de TI recebem orientação geral. Quando a norma não está no fluxo, a resposta encaminha à Central de Atendimento de TI da MTI. A pergunta 6 está fora do escopo de `dados/setor.md` e foi recusada.

O fluxo não guarda a conversa: não há Message History, então a segunda pergunta não herda a primeira. Também não consulta norma. Esse é o tema da aula seguinte.

## Resumo conferido

`dados/documento_resumo.txt` é o Ofício Circular nº 48/2026/GINF/MTI, de 10 de novembro de 2026, sobre estações e VPN. Os nomes de pessoas são fictícios. A execução usou 544 tokens em 2,9 s. A conferência está em `resultados/conferencia_resumo.md`.

| Providência | Responsável no original | Prazo no original | Responsável extraído | Prazo extraído |
| --- | --- | --- | --- | --- |
| Conferir as estações com o sistema operacional desatualizado e registrar o inventário | Ana Ribeiro | 28 de novembro de 2026 | Ana Ribeiro | 28 de novembro de 2026 |
| Substituir as senhas das contas de serviço da VPN e confirmar o teste | Carlos Mendes | 21 de novembro de 2026 | Carlos Mendes | 21 de novembro de 2026 |
| Esclarecer dúvidas sobre o novo formulário de abertura de chamado | não informado | não informado | não informado | não informado |

Na terceira linha o ofício não dá responsável nem prazo. A saída escreveu "não informado" nos dois campos. Essa conferência é o que torna o resumo utilizável no setor.

## Classificador

As categorias vêm de `dados/setor.md`. INCIDENTE é serviço de TI parado ou que impede o trabalho agora. REQUISICAO pede acesso, equipamento, instalação ou outro recurso que ainda não existe. DUVIDA pede orientação e não exige ação imediata.

A tabela do Playground, em `resultados/bateria_classificador.md`:

| Fluxo | Mensagem de teste | Resposta correta? | Tokens | Tempo |
| --- | --- | --- | --- | --- |
| Classificador TI MTI | A VPN da MTI caiu agora e ninguém da unidade consegue entrar no sistema de protocolo. | Sim. INCIDENTE. | 242 | 1,4 s |
| Classificador TI MTI | Solicito a instalação do LibreOffice na estação da sala 204 e a liberação do meu acesso ao portal de chamados. | Sim. REQUISICAO. | 257 | 2,0 s |
| Classificador TI MTI | Qual a diferença entre a conta de rede e a conta do e-mail institucional? | Sim. DUVIDA. | 236 | 2,1 s |
| Classificador TI MTI | O computador da recepção está lento desde ontem. Dá para trocar por uma máquina nova? | Sim. REQUISICAO. | 271 | 2,5 s |
| Classificador TI MTI | A impressora do setor não imprime desde as 8h de hoje. Vocês me explicam como resetar ou isso já é chamado? | Sim. INCIDENTE. | 270 | 1,9 s |

A quarta mensagem é ambígua entre incidente e requisição. A máquina está lenta, mas o pedido é uma máquina nova e o texto não diz que o trabalho parou. O critério do prompt desempatou para REQUISICAO. A quinta pede o modo de resetar e, ao mesmo tempo, descreve a impressora parada desde as 8h. O critério escolhe INCIDENTE quando o trabalho já está interrompido, e a primeira linha saiu INCIDENTE.

A primeira linha em maiúsculas existe para um programa ler a categoria sem ambiguidade. `executar/classificar.py` lê essa linha.

## Agente e custo

`dados/perguntas_agente.json` tem duas perguntas. A direta pede a nota da MTI na avaliação de gestão do Governo Federal e a data da notícia no portal. A vaga pede o período em que uma unidade pode solicitar o catálogo de serviços e desde quando ele está em vigor. O detalhe das chamadas está em `resultados/custo_agente.md`. Max Iterations permaneceu 15, no campo do componente Agent.

A direta fez três buscas (`perform_search`) e duas leituras de página (`fetch_content`), inclusive a notícia da nota 95,22 e a página inicial do portal. Flow Activity: 33.217 tokens e 34,27 s. A resposta cita 95,22, 17 de novembro de 2026 e `https://www.mti.mt.gov.br/`.

A vaga fez sete buscas e uma leitura, a do catálogo em `https://www.mti.mt.gov.br/servicos/catalogo-de-servicos`. Flow Activity: 111.662 tokens e 40,52 s. A página lida não traz o período nem a data de início, e a resposta diz isso.

A vaga gastou cerca de 3,4 vezes os tokens da direta. O agente custa o que as ferramentas o levam a consumir: cada busca fica no contexto da chamada seguinte. O tempo quase não mudou, 40,52 s contra 34,27 s, porque as buscas extras cabem no mesmo limite de iterações. A resposta cita a fonte. Quem for repassá-la abre esse endereço antes, porque o agente resume o que leu.

## Arquivo e API

Os quatro JSON estão em `fluxos/`: atendimento, resumo, classificador e agente de pesquisa. `executar/importar.py` envia essa pasta ao servidor.

`rodar`, em `src/cliente.py`, manda a mensagem e lê o texto da resposta:

```python
corpo = {"input_value": mensagem, "input_type": "chat", "output_type": "chat"}
resposta = cliente.post(f"/run/{fluxo['id']}", params={"stream": "false"}, json=corpo)
mensagem_saida = resposta.json()["outputs"][0]["outputs"][0]["results"]["message"]
```

As cinco mensagens pela API, em `resultados/comparacao_api.md`, repetiram o Playground:

| n | Mensagem | Playground | API | Coincidiram |
| --- | --- | --- | --- | --- |
| 1 | A VPN da MTI caiu agora e ninguém da unidade consegue entrar no sistema de protocolo. | INCIDENTE | INCIDENTE | sim |
| 2 | Solicito a instalação do LibreOffice na estação da sala 204 e a liberação do meu acesso ao portal de chamados. | REQUISICAO | REQUISICAO | sim |
| 3 | Qual a diferença entre a conta de rede e a conta do e-mail institucional? | DUVIDA | DUVIDA | sim |
| 4 | O computador da recepção está lento desde ontem. Dá para trocar por uma máquina nova? | REQUISICAO | REQUISICAO | sim |
| 5 | A impressora do setor não imprime desde as 8h de hoje. Vocês me explicam como resetar ou isso já é chamado? | INCIDENTE | INCIDENTE | sim |

Quem conhece o trabalho ajusta o fluxo na tela. Quem conhece os sistemas o chama pela rede.

## Ficha de governança

O texto integral está em `resultados/ficha_governanca.md`.

Textos enviados aos fluxos: cada mensagem do Playground e cada `input_value` da API seguem para o provedor OpenAI cadastrado em Settings → Model Providers, com o modelo gpt-6-luna, porque a chave veio do ambiente do servidor e não foi digitada na tela. Um texto que não pudesse sair da MTI usaria Ollama na própria máquina.

Retenção no banco do LangFlow: as mensagens ficam no banco local desta instalação até serem apagadas em Settings → Messages, e o prazo deste laboratório é o da correção da entrega, porque o banco já guarda o que foi digitado nas sessões e o LangFlow não descarta a sessão sozinho.

Revisão humana: a coordenação da Central de Atendimento de TI da MTI revisa a resposta antes de ela sair em nome do setor, como está em `dados/setor.md`, porque o Playground só testa e a API só integra.

Prompt guardado e versionado: o texto de cada fluxo fica em `prompts/`, no markdown de mesmo nome, e a cópia executada fica no JSON correspondente em `fluxos/`, os dois no repositório do setor.

## O que a turma deve conseguir defender

O atendimento é um grafo de quatro componentes e três ligações, com o prompt na mensagem de sistema. Resumo e classificador reutilizam esse grafo e mudam o prompt. O agente da pesquisa gastou mais na pergunta vaga, 111.662 tokens contra 33.217 da direta, porque fez mais chamadas de ferramenta. O fluxo versionado é o JSON, executado pela API sem abrir a tela, e a chave do provedor permanece no ambiente. A resposta só sai em nome do setor depois da revisão humana definida na ficha.
