# Análise — pipeline ingênuo × pipeline protegido

Acervo: Regimento Interno da Empresa Mato-grossense de Tecnologia da Informação – MTI
(Decreto nº 1.212/2025), cinco subseções indexadas (art. 1º, art. 2º, art. 4º, art. 5º e
art. 34). Conjunto de avaliação: as 14 perguntas de `src/perguntas.json`, sendo 10 com
resposta no acervo e 4 sem resposta (P14 é a armadilha aritmética).

| Item              | Valor                                                                     |
| ----------------- | ------------------------------------------------------------------------- |
| Chunking          | `janela_200_50` (10 chunks), a estratégia adotada no experimento anterior |
| Embedding         | Gemini `gemini-embedding-001`                                             |
| Chat              | Groq `openai/gpt-oss-120b`, temperatura 0                                 |
| Recuperação       | k = 3, similaridade de cosseno                                            |
| Programa          | `src/protegido.py` (adaptação do `exemplo05.py`)                          |
| Resultados brutos | `src/data/resultado_protegido.json`                                       |

Execução:

```powershell
$env:PYTHONIOENCODING='utf-8'; $env:GROQ_MODEL='openai/gpt-oss-120b'
.\.venv\Scripts\python.exe src\protegido.py
```

## 1. Calibração do limiar (Guarda 1)

Similaridade do primeiro trecho recuperado:

- perguntas com resposta no acervo (10): mínimo 0,714 | mediana 0,758 | máximo 0,822
- perguntas sem resposta no acervo (4): mínimo 0,603 | mediana 0,677 | máximo 0,687

| Limiar | Corta perguntas respondíveis | Corta perguntas sem resposta |
| ------ | ---------------------------- | ---------------------------- |
| 0,60   | 0                            | 0                            |
| 0,65   | 0                            | 1                            |
| 0,70   | 0                            | 4                            |
| 0,75   | 5                            | 4                            |
| 0,80   | 9                            | 4                            |
| 0,85   | 10                           | 4                            |

**Limiar adotado: 0,71**, o maior valor em centésimos que não corta nenhuma pergunta
respondível. Com ele, as 4 perguntas sem resposta são barradas antes mesmo de chamar o
modelo.

Diferente do que mostra a aula, aqui as duas distribuições não se sobrepõem. Mesmo assim, a
folga é pequena: 0,714 (P6, a respondível mais fraca) contra 0,687 (P11, a sem resposta mais
forte), uma diferença de 0,027. Com apenas 14 pontos, o limiar está ajustado ao próprio
conjunto de avaliação. Uma pergunta nova sobre casos omissos com outra redação pode passar
de 0,71, e uma pergunta respondível com redação diferente pode cair abaixo. Por isso as
Guardas 2 e 3 continuam necessárias, ainda que nesta rodada não tenham precisado atuar.

## 2. Tabela final (categorias da Seção 4.5)

| Veredito                                | Pipeline ingênuo | Pipeline protegido |
| --------------------------------------- | ---------------- | ------------------ |
| Acerto                                  | 10               | 10                 |
| Erro                                    | 0                | 0                  |
| Recusa indevida                         | 0                | 0                  |
| Recusa no formato contratado            | 0                | 4                  |
| Resposta livre, exigindo leitura humana | 4                | 0                  |
| Respostas com número sem lastro         | 2                | 0                  |

Leitura da tabela:

- **Os acertos não mudaram (10 × 10).** Assim como na aula, as guardas não melhoram a
  capacidade de responder. As 10 respostas protegidas contêm a chave esperada e nenhum
  número órfão.
- **A mudança está nas 4 perguntas sem resposta.** No ingênuo, todas saíram em texto livre:
  - P11 inventou que os casos omissos são resolvidos pelo Conselho de Administração;
  - P12 recusou corretamente, mas em prosa ("O trecho apresentado não traz nenhuma
    informação…"), que nenhum sistema a jusante consegue reconhecer como recusa;
  - P13 respondeu com conhecimento próprio (art. 5º, I, da Lei nº 13.709/2018);
  - P14 caiu na armadilha e calculou 5 × 12 = 60 meses.

  No protegido, as 4 viraram `NÃO ENCONTRADO`, reconhecível por comparação de texto.

- **Números sem lastro: de 2 para 0.** No ingênuo, P13 trouxe `13.709` e `2018`, e P14 trouxe
  `12` e `60`, números que não aparecem em nenhum trecho recuperado.
- **Não houve recusa indevida nesta rodada**, ao contrário da aula. Isso só aconteceu depois
  de corrigir a Guarda 3 (ver seção 4).

## 3. Falha escolhida: P11 no pipeline ingênuo

**Pergunta:** "Quem resolve os casos omissos neste Regimento Interno?"

**Resposta ingênua:** "No Regimento Interno, a responsabilidade de interpretar o Estatuto e
deliberar sobre os casos omissos cabe ao **Conselho de Administração**【1】."

**Gabarito:** a regra está no art. 80 (Título V), que não está entre as cinco subseções
indexadas. A pergunta não tem resposta no acervo, e a resposta correta seria a recusa.

**Classificação: Falha 2 — o modelo respondeu sem contexto suficiente.**

**O número que sustenta a classificação é a similaridade do primeiro trecho: 0,687**, abaixo do
limiar de 0,71 e abaixo de todas as 10 perguntas respondíveis (mínimo de 0,714). O melhor
trecho que o acervo tinha a oferecer era mais fraco que o pior caso legítimo, ou seja, faltava
contexto para responder. Mesmo assim, o modelo sem contrato produziu uma resposta afirmativa,
com citação.

Trechos recuperados:

| Trecho | Origem                                                      | Similaridade |
| ------ | ----------------------------------------------------------- | ------------ |
| [1]    | `conselho-administracao`, chunk 3 (art. 4º, incisos finais) | 0,687        |
| [2]    | `conselho-administracao`, chunk 1                           | 0,649        |
| [3]    | `gestao-pessoas`, chunk 0                                   | 0,643        |

Margem entre o 1º e o 3º trecho: 0,043.

Por que não é uma das outras duas falhas:

- **Não é Falha 1 (recuperação trouxe o trecho errado).** A Falha 1 pressupõe que o trecho
  certo existe no índice e foi preterido. Aqui não existe trecho certo, porque o art. 80 não
  foi indexado, e nenhuma recuperação poderia trazê-lo. A margem baixa (0,043) mostra que os
  três candidatos eram igualmente fracos, mas isso confirma a falta de contexto, não uma
  escolha errada entre candidatos bons.
- **Não é Falha 3 (citação não sustenta a afirmação), embora pareça.** O trecho [1] contém o
  inciso XXV do art. 4º, "promover a interpretação do presente **Estatuto** e deliberar sobre
  os casos omissos". O modelo transferiu a frase do Estatuto para o Regimento, uma troca de
  fonte com aparência de rigor. Só que o detector da Falha 3 não tem o que medir: a resposta
  tem **0 números**, então a ancoragem não encontra nenhum órfão e deixa a resposta passar.
  O erro de origem foi responder com o pouco que havia.

Esse é o caso mais instrutivo do conjunto. É a pergunta sem resposta mais próxima do limiar
(0,027 abaixo do mínimo das respondíveis) e a única invenção que a Guarda 3 sozinha não
pegaria. No protegido, ela só foi barrada pela Guarda 1. Se a similaridade tivesse passado de
0,71, a defesa restante seria a regra 3 do contrato ("Confira se o trecho se refere ao órgão
ou à unidade sobre a qual se pergunta") e a regra 4 (recusar se a resposta não estiver
literalmente nos trechos).

## 4. Ajustes feitos durante a execução

- **Modelo de chat.** A cota diária de tokens do `openai/gpt-oss-20b` no Groq se esgotou
  (erro 429). A rodada final usou o `openai/gpt-oss-120b`, que tem cota separada, por meio
  da variável `GROQ_MODEL`.
- **Citações na Guarda 3.** A ancoragem original contava o algarismo das citações como
  número da resposta. O contrato exige `[n]`, e o `gpt-oss` também escreve `【1】` e
  `【1†L1-L4】`. O "1" virava órfão e a Guarda 3 descartava respostas corretas: na primeira
  rodada, P5 e P9 deram **recusa indevida** (placar protegido de 8 acertos e 2 recusas
  indevidas). A regex `CITACAO` agora remove os três formatos antes de procurar números, e as
  duas perguntas voltaram a ser acertos. A comparação por substring continua grosseira, como
  a aula admite: um número curto como `5` quase sempre encontra lastro em algum ponto do
  contexto.

