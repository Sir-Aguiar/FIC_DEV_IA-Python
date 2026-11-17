# Vazamento por identificador

## Mesma sessão, CPFs distintos

O framework isolou.

> Não consigo visualizar nesta conversa o seu nome completo nem o login institucional informados anteriormente. Por favor, envie esses dados novamente para que eu possa confirmá-los.

## Mesmo identificador, derivado do guichê

O segundo cidadão recebeu dado da Ana.

> Seu nome completo informado é **Ana Beatriz Costa** e seu login institucional é **ana.costa**.

## Regra correta

O user_id do service desk da MTI sai do CPF do servidor, pela função identificador_do_cidadao. O CPF individualiza porque há um por pessoa. Guichê, canal e atendente são compartilhados por todos os chamados daquele balcão, então não separam um titular do outro.
