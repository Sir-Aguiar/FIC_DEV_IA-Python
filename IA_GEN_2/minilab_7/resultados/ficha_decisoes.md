# Ficha de decisões

Estratégia de memória: histórico completo com teto de 15 execuções, porque neste roteiro de 14 turnos ele acertou 6/6 por US$ 0,00395, enquanto o resumo acertou 5/6 por US$ 0,00724 e a entrada do histórico só superaria o patamar do resumo por volta do turno 28.

Origem do user_id: o CPF do servidor, em identificador_do_cidadao, porque o mesmo guichê_02 fez Carlos receber «Ana Beatriz Costa» e «ana.costa»; com um CPF por pessoa, a mesma sessão não entregou o atendimento da Ana.

Dados em tabela própria: protocolo, situação e prazo do desbloqueio ficam na tabela do órgão, porque mudam durante o chamado; nome e preferência de tratamento podem ficar na memória do framework, e conta bancária e nome da mãe não ficam em nenhuma das duas.

Prazo de retenção: 30 dias para sessão, execuções e memórias do framework, porque a finalidade se esgota com o chamado e o art. 18 da LGPD só se cumpriu quando delete_session e delete_user_memories rodaram em sequência — a primeira deixou as 4 memórias, inclusive o nome da mãe.

Modo de depuração: desligado, porque o prompt e o log passariam a guardar o CPF, o login e o dado desnecessário do turno 4, que a Parte 3 já encontrou em agno_memories e agno_runs.
