# Parte 1 — Interface Streamlit (`app_assistente.py`)

Servidor: `http://localhost:8501`  
Acervo enviado pela barra lateral: `processo_seletivo_mti.pdf` e `regimento_interno_mti.pdf` (indexados com sucesso).

As dez perguntas da bateria do `exemplo03.py` foram feitas no chat. A URL permaneceu em `/` o tempo todo: o painel de fontes abre **na mesma tela**, sob cada resposta, sem abrir o PDF nem outra rota.

## O painel permite conferir sem sair da tela?

**Sim.** Cada resposta (e cada recusa) vem com um expander:

- fundamentada: `Fontes desta resposta — N trecho(s)`
- recusa: `Trechos consultados (nenhum responde à pergunta) — N trecho(s)`

Dentro do expander aparecem **documento, página, similaridade e o texto integral do trecho**. Dá para cruzar a citação com o trecho recuperado sem sair do chat.

## Bateria na interface

| Pergunta                                                                          | Painel na mesma tela? | Rótulo do painel             | Páginas no painel |
| --------------------------------------------------------------------------------- | --------------------- | ---------------------------- | ----------------- |
| Há cobrança de taxa de inscrição no processo seletivo da MTI?                     | Sim                   | Fontes desta resposta        | 1                 |
| Qual a remuneração do perfil Analista de TI - Gerente de Projeto?                 | Sim                   | Fontes desta resposta        | 2                 |
| Qual o percentual de vagas reservadas às pessoas com deficiência?                 | Sim                   | Fontes desta resposta        | 3                 |
| Qual o período de inscrições previsto no cronograma do edital?                    | Sim                   | Fontes desta resposta        | 4                 |
| O exame admissional é obrigatório na contratação?                                 | Sim                   | Trechos consultados (recusa) | 4, 1, 5, 3        |
| Qual a multa aplicada se o contratado não cumprir o aviso prévio de 30 dias?      | Sim                   | Fontes desta resposta        | 27                |
| A Gerência de Aquisições realiza procedimentos licitatórios de quais modalidades? | Sim                   | Fontes desta resposta        | 9, 10             |
| Qual o capital social mínimo exigido para participar do certame?                  | Sim                   | Trechos consultados (recusa) | 3, 1, 22          |
| Quem é o pregoeiro responsável pela sessão pública?                               | Sim                   | Trechos consultados (recusa) | 10, 20, 9         |
| Qual a alíquota do IPVA em Mato Grosso em 2026?                                   | Sim                   | Trechos consultados (recusa) | 1, 2, 7           |

Ao final havia **10 expanders** na conversa, um por pergunta.

## Observação

A recusa do exame admissional se repetiu na interface: o painel mostrou trechos da p. 4 e também da p. 5, mas o modelo recusou. Mesmo assim a conferência é possível sem sair da tela — o trecho consultado fica visível no expander.
