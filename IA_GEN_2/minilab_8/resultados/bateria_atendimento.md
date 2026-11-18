# Bateria de atendimento do setor de TI da MTI

Fluxo `fluxos/atendimento.json`, prompt em `prompts/atendimento.md`. Cada pergunta foi uma sessão nova, porque o fluxo não tem Message History. Os tokens são o total do contador do Playground. O tempo é o intervalo entre a mensagem enviada e a resposta nessa sessão.

| n | Pergunta | Comportamento esperado | Tokens | Tempo |
| --- | --- | --- | --- | --- |
| 1 | Esqueci a senha da conta de rede. Como recupero o acesso? | Sim. Orientou a redefinição pela Central de Atendimento de TI e não fixou prazo. | 238 | 1,7 s |
| 2 | Meu computador não liga depois da queda de energia. O que faço? | Sim. Deu checagens gerais e mandou abrir chamado, sem número de protocolo nem prazo. | 340 | 3,2 s |
| 3 | A VPN da MTI não conecta no trabalho remoto. Por onde começo? | Sim. Orientou a verificação geral e encaminhou o erro persistente à central. | 336 | 2,6 s |
| 4 | Preciso de acesso ao sistema de protocolo eletrônico. Quem libera? | Sim. Encaminhou a liberação à central, sem artigo nem prazo. | 306 | 2,2 s |
| 5 | A impressora do setor está offline desde hoje cedo. Como registro isso? | Sim. Explicou o registro do chamado e não inventou o número. | 247 | 1,7 s |
| 6 | Qual o valor do auxílio-alimentação dos servidores da MTI neste mês? | Sim. Recusou o assunto, fora do suporte de TI, e indicou Gestão de Pessoas, sem informar valor. | 277 | 2,0 s |

A pergunta 6 é a que fica fora do escopo de `dados/setor.md`. As outras cinco cabem no suporte de TI e recebem orientação geral; quando o procedimento exato não está no fluxo, a resposta encaminha à Central de Atendimento de TI da MTI.
