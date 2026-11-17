# Eliminação dos dados do titular

A rotina percorre as tabelas em que o identificador apareceu na Parte 3. A etapa 1 apaga sessão e execuções. A etapa 2 apaga as memórias extraídas.

## Contagem

| Momento | Identificador | Nome | Login | Dado desnecessário |
| --- | --- | --- | --- | --- |
| antes | agno_memories (4), agno_runs (14), agno_sessions (1) | agno_memories (1), agno_runs (14) | agno_memories (1), agno_runs (13) | agno_memories (1), agno_runs (11) |
| depois da etapa 1 | agno_memories (4) | agno_memories (1) | agno_memories (1) | agno_memories (1) |
| depois da etapa 2 | nenhuma tabela | nenhuma tabela | nenhuma tabela | nenhuma tabela |
| depois da limpeza da pergunta | nenhuma tabela | nenhuma tabela | nenhuma tabela | nenhuma tabela |

Memórias apagadas na etapa 2: 4.

## Resposta depois da etapa 1

Encerrar aqui deixaria o agente sabendo o que estava em `agno_memories`.

> Seu nome completo é **Ana Beatriz Costa**, seu login institucional é **ana.costa** e o nome da sua mãe é **Lúcia Costa**.

## Resposta depois da exclusão completa

Pergunta: Sem que eu repita nada: qual é o meu nome completo, o meu login institucional e o nome da minha mãe?

> Ainda não tenho essas informações nesta conversa. Por favor, informe seu nome completo, login institucional e nome da sua mãe.

Conferência no banco depois das duas etapas e da limpeza da pergunta: nada do titular restou.
