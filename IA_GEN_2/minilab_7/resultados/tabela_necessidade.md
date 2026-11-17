# Necessidade do que ficou retido

Atendimento do service desk da MTI com extração de memória ligada. A finalidade é desbloquear o acesso ao correio e ao SEI. Conta bancária e nome da mãe, ditos no turno 4, não servem a esse pedido.

| Texto retido | Necessária ao atendimento | Tabela |
| --- | --- | --- |
| A usuária se chama Ana Beatriz Costa e prefere ser chamada de Ana. | sim | agno_memories |
| O login institucional da Ana é ana.costa; ela teve problemas de acesso ao correio eletrônico e ao SEI. | sim | agno_memories |
| A mãe de Ana se chama Lúcia Costa e mora com ela. | não — excede a finalidade | agno_memories |
| Ana trabalha na Secretaria de Fazenda, na Coordenadoria de Arrecadação. | sim | agno_memories |

## Dado pessoal desnecessário

- `45123-8`: O texto extraído não repetiu esse trecho; ele ficou no registro bruto. Tabelas: `agno_memories` (1), `agno_runs` (1).
- `Lúcia Costa`: O texto extraído em `agno_memories` contém esse trecho. Tabelas: `agno_memories` (1), `agno_runs` (11).

## Tabelas em que o identificador aparece

- `agno_memories`: 4 registro(s)
- `agno_runs`: 14 registro(s)
- `agno_sessions`: 1 registro(s)

## Tabelas do banco

`agno_memories`, `agno_runs`, `agno_schema_versions`, `agno_sessions`
