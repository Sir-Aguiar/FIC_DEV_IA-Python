# Parte 1 — Justificativa do limiar e critérios

Na bateria de 10 perguntas (7 com resposta no acervo, 3 sem), o assistente citou a página correta em **6** casos (p. 1, 2, 3, 4, 27 e 10) e recusou corretamente as **3** perguntas sem resposta (capital social, pregoeiro e IPVA). A sétima pergunta legítima — exame admissional, p. 5 — foi recusada nas duas medições; os trechos recuperados tinham similaridade **0,57** e vinham sobretudo da p. 4, então a falha não foi o corte do limiar. Subir o limiar de **0,25** para **0,45** produziu o mesmo quadro: **0** perguntas legítimas a mais recusadas, **6/6** citações de página mantidas e **3/3** recusas fora do acervo mantidas. No `exemplo02.py`, trechos off-topic das perguntas de licitação entraram com similaridade entre **0,408** e **0,535**; 0,45 corta parte dessa faixa sem ter reduzido, nesta bateria, nenhuma resposta válida. Adoto **0,45**: é o único valor acima de 0,25 que medi no acervo completo, não piorou os 9/10 comportamentos corretos e fica abaixo da menor similaridade das respostas que acertaram a página na interface (**0,605** a **0,699**).

## Critérios de avaliação

- [x] Acervo indexado com metadados de documento e página
- [x] Respostas citando documento e página verificáveis na fonte
- [x] Recusa correta nas perguntas sem resposta no acervo
- [x] Bateria de auditoria escrita e executada, com quadro preenchido
- [x] Interface Streamlit funcionando com painel de fontes
- [x] Justificativa do limiar baseada em medição
