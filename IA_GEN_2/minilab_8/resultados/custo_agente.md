# Custo do agente de pesquisa

Fluxo `fluxos/agente-pesquisa.json`, instrução em `prompts/agente-pesquisa.md`. Os números de tokens e de tempo são as colunas Token e Latency da tela Flow Activity. As chamadas são as linhas de ferramenta do Playground. Max Iterations permaneceu 15, no campo do componente Agent.

A pergunta direta custou 33.217 tokens em 34,27 s. A vaga custou 111.662 tokens em 40,52 s, cerca de 3,4 vezes os tokens da direta. A diferença vem das buscas a mais: a direta fez três buscas e leu duas páginas; a vaga fez sete buscas e leu uma página, e cada resultado ficou no contexto da chamada seguinte.

## Direta

Texto: Qual nota a MTI obteve na avaliação de gestão do Governo Federal, segundo a notícia publicada no portal oficial, e em que data ela saiu?

| Chamada | Ação | Duração da ferramenta |
| --- | --- | --- |
| 1 | perform_search — site:mti.mt.gov.br, nota da avaliação de gestão | 3,8 s |
| 2 | fetch_content — notícia da nota 95,22 no portal | 0,8 s |
| 3 | perform_search — "MTI eleva nota para 95,22" | 7,4 s |
| 4 | perform_search — site:mti.mt.gov.br e "95,22" | 6,9 s |
| 5 | fetch_content — https://www.mti.mt.gov.br/ | 0,5 s |

Flow Activity: 33.217 tokens, 34,27 s.

Resposta: a nota é 95,22 e a notícia saiu em 17 de novembro de 2026. A fonte citada é https://www.mti.mt.gov.br/.

## Vaga

Texto: Em que período uma unidade do Estado pode solicitar o catálogo de serviços da MTI, e desde quando esse catálogo está em vigor?

| Chamada | Ação | Duração da ferramenta |
| --- | --- | --- |
| 1 | perform_search — catálogo de serviços, período e vigência | 4,1 s |
| 2 | perform_search — "Catálogo de Serviços" MTI solicitar período | 3,7 s |
| 3 | perform_search — catálogo, vigência e unidade | 2,9 s |
| 4 | perform_search — desde quando o catálogo entrou em vigor | 2,7 s |
| 5 | perform_search — unidades do Estado e catálogo | 2,7 s |
| 6 | fetch_content — https://www.mti.mt.gov.br/servicos/catalogo-de-servicos | 0,9 s |
| 7 | perform_search — solicitar o catálogo, período | 2,3 s |
| 8 | perform_search — catálogo de solução de software e vigência | 4,4 s |

Flow Activity: 111.662 tokens, 40,52 s.

Resposta: a página lida não informa o período nem a data de início. A fonte citada é https://www.mti.mt.gov.br/servicos/catalogo-de-servicos. Quem for repassar a resposta em nome do setor abre esse endereço antes, porque o agente resume o que leu e a citação não prova sozinha que a página era a certa.
