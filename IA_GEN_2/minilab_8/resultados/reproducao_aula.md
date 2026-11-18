# Reprodução da Seção 4.3

Fluxo importado de `exemplos/fluxo01-atendimento-professor.json`, com o nome Atendimento ao professor. O modelo é o gpt-6-luna e a temperatura é 0,1. A chave da OpenAI não está no JSON.

Pergunta, a mesma da figura da Seção 4.3:

> Preciso trocar de escola no meio do ano letivo. Como funciona o processo de remoção?

Resposta lida no Playground, sessão `secao-4-3-b`:

> A remoção entre escolas depende das normas e dos períodos definidos pela SEDUC-MT; durante o ano letivo, pode haver restrições e a mudança não é automática. Consulte a Diretoria Regional de Educação (DRE) responsável ou a unidade de recursos humanos da sua escola para verificar se há processo aberto, vagas e quais documentos e critérios se aplicam. Evite deixar a escola atual antes de receber a autorização formal.

O contador à direita da resposta mostrou **307** tokens. O intervalo entre a mensagem do usuário e a resposta, na mesma sessão, foi **2,9 s**. A figura da aula registrava 321 tokens e cerca de 3 s; esta execução ficou no mesmo patamar e repetiu o comportamento da seção: orientação geral, sem prazo ou artigo inventado, com encaminhamento à DRE ou ao RH da escola.
