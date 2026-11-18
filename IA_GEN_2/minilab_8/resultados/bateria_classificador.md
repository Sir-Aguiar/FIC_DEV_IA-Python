# Bateria do classificador

Fluxo `fluxos/classificador.json`. As categorias vêm de `dados/setor.md`. A primeira linha da resposta é só a categoria, em maiúsculas. Os tokens são o total do contador do Playground. O tempo é o intervalo entre a mensagem e a resposta na sessão.

| Fluxo | Mensagem de teste | Resposta correta? | Tokens | Tempo |
| --- | --- | --- | --- | --- |
| Classificador TI MTI | A VPN da MTI caiu agora e ninguém da unidade consegue entrar no sistema de protocolo. | Sim. INCIDENTE. | 242 | 1,4 s |
| Classificador TI MTI | Solicito a instalação do LibreOffice na estação da sala 204 e a liberação do meu acesso ao portal de chamados. | Sim. REQUISICAO. | 257 | 2,0 s |
| Classificador TI MTI | Qual a diferença entre a conta de rede e a conta do e-mail institucional? | Sim. DUVIDA. | 236 | 2,1 s |
| Classificador TI MTI | O computador da recepção está lento desde ontem. Dá para trocar por uma máquina nova? | Sim. REQUISICAO. | 271 | 2,5 s |
| Classificador TI MTI | A impressora do setor não imprime desde as 8h de hoje. Vocês me explicam como resetar ou isso já é chamado? | Sim. INCIDENTE. | 270 | 1,9 s |

A quarta mensagem é ambígua entre incidente e requisição: a máquina está lenta, mas o pedido é uma máquina nova e o texto não diz que o trabalho parou. O critério do prompt desempatou para REQUISICAO, e foi essa a categoria da primeira linha.

A quinta também é ambígua, entre incidente e dúvida, porque pede o modo de resetar e ao mesmo tempo descreve a impressora parada desde as 8h. O critério escolhe INCIDENTE quando o trabalho já está interrompido, e a primeira linha saiu INCIDENTE.
