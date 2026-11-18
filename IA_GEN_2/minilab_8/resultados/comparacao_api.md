# Comparação entre Playground e API

As cinco mensagens de `dados/mensagens.json` foram enviadas por `exemplos/cliente_api.py` ao fluxo Classificador TI MTI. A categoria da API é a primeira linha da resposta. A do Playground é a da Parte 3, em `resultados/bateria_classificador.md`.

| n | Mensagem | Playground | API | Coincidiram |
| --- | --- | --- | --- | --- |
| 1 | A VPN da MTI caiu agora e ninguém da unidade consegue entrar no sistema de protocolo. | INCIDENTE | INCIDENTE | sim |
| 2 | Solicito a instalação do LibreOffice na estação da sala 204 e a liberação do meu acesso ao portal de chamados. | REQUISICAO | REQUISICAO | sim |
| 3 | Qual a diferença entre a conta de rede e a conta do e-mail institucional? | DUVIDA | DUVIDA | sim |
| 4 | O computador da recepção está lento desde ontem. Dá para trocar por uma máquina nova? | REQUISICAO | REQUISICAO | sim |
| 5 | A impressora do setor não imprime desde as 8h de hoje. Vocês me explicam como resetar ou isso já é chamado? | INCIDENTE | INCIDENTE | sim |

### 1

A VPN da MTI caiu agora e ninguém da unidade consegue entrar no sistema de protocolo.

Playground: INCIDENTE. API: INCIDENTE.
Justificativa da API: A VPN está indisponível e impede a unidade de acessar o sistema de protocolo.
Categoria esperada em dados/mensagens.json: INCIDENTE.
### 2

Solicito a instalação do LibreOffice na estação da sala 204 e a liberação do meu acesso ao portal de chamados.

Playground: REQUISICAO. API: REQUISICAO.
Justificativa da API: A mensagem solicita a instalação de um programa e a liberação de acesso a um portal.
Categoria esperada em dados/mensagens.json: REQUISICAO.
### 3

Qual a diferença entre a conta de rede e a conta do e-mail institucional?

Playground: DUVIDA. API: DUVIDA.
Justificativa da API: A mensagem pede apenas uma explicação sobre a diferença entre as contas, sem solicitar ação ou recurso.
Categoria esperada em dados/mensagens.json: DUVIDA.
### 4

O computador da recepção está lento desde ontem. Dá para trocar por uma máquina nova?

Playground: REQUISICAO. API: REQUISICAO.
Justificativa da API: A mensagem solicita a troca do computador por uma máquina nova, sem informar que o trabalho está interrompido.
Categoria esperada em dados/mensagens.json: REQUISICAO.
### 5

A impressora do setor não imprime desde as 8h de hoje. Vocês me explicam como resetar ou isso já é chamado?

Playground: INCIDENTE. API: INCIDENTE.
Justificativa da API: A impressora está sem funcionar desde hoje cedo, interrompendo o serviço no momento.
Categoria esperada em dados/mensagens.json: INCIDENTE.
