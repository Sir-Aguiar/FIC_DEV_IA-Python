# Ficha de governança

Textos enviados aos fluxos: cada mensagem do Playground e cada `input_value` da API seguem para o provedor OpenAI cadastrado em Settings → Model Providers, com o modelo gpt-6-luna, porque a chave veio do ambiente do servidor e não foi digitada na tela; um texto que não pudesse sair da MTI usaria Ollama na própria máquina.

Retenção no banco do LangFlow: as mensagens ficam no banco local desta instalação até serem apagadas em Settings → Messages, e o prazo deste laboratório é o da correção da entrega, porque o banco já guarda o que foi digitado nas sessões e o LangFlow não descarta a sessão sozinho.

Revisão humana: a coordenação da Central de Atendimento de TI da MTI revisa a resposta antes de ela sair em nome do setor, como está em `dados/setor.md`, porque o Playground só testa e a API só integra.

Prompt guardado e versionado: o texto de cada fluxo fica em `prompts/`, no markdown de mesmo nome, e a cópia executada fica no JSON correspondente em `fluxos/`, os dois no repositório do setor.
