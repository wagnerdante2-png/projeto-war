# ULTIMECIA War Room — Research Autopilot v1

## Objetivo

Reduzir o gargalo humano na triagem dos estudos sem transformar a War Room em autoridade de produção.

O motor trabalha sobre o corpus estruturado e produz quatro coisas:

1. avaliação automática de cada ideia;
2. rota recomendada;
3. plano de pesquisa/experimento/certificação quando aplicável;
4. fila curta de exceções que realmente merecem decisão humana.

## Regra central

> Alta autonomia de pesquisa; autoridade de produção zero.

O Autopilot não faz commit, branch, PR, merge, cutover ou alteração no `ultimecia-code`. Ele organiza e planeja.

## Dimensões avaliadas

- aderência ao AS-IS declarado no estudo;
- evidência disponível no corpus;
- viabilidade;
- valor potencial;
- risco arquitetural/operacional;
- convergência com ideias independentes de outros estudos.

## Classificações

- `JÁ EXISTE`
- `EXPANDE`
- `SUBSTITUTO CANDIDATO`
- `DUPLICA AUTHORITY`
- `CERTIFICATION GAP`
- `PESQUISA`
- `DEFERIR`
- `REJEITAR`

## Rotas automáticas

### reference

Capacidade já existe. Preservar como referência e procurar apenas delta mensurável.

### research

Aprofundar evidência e alternativas antes de qualquer POC.

### experiment

Preparar experimento falsificável, preferencialmente sandbox/shadow, com baseline, critérios de aceitação e rollback.

### certification

Não criar feature nova; fechar a evidência/certificação que falta.

### defer

Preservar a ideia, mas não consumir capacidade de implementação agora.

### human

Reservado a potenciais duplicações de authority, substituições arquiteturais, riscos elevados ou decisões estratégicas.

## Attention Budget

O usuário não deve revisar todas as ideias. A War Room mantém uma fila curta de exceções relevantes. O restante pode continuar sendo pesquisado, organizado e planejado automaticamente.

## Planos gerados

Um plano pode ser `RESEARCH`, `EXPERIMENT` ou `CERTIFICATION`.

Todos possuem:

- origem rastreável;
- objetivo;
- target repository apenas como referência;
- prioridade P1/P2/P3;
- risco;
- passos;
- critérios de aceitação;
- constraints arquiteturais;
- `authority: none`.

## Invariantes

1. não criar authority nova por inferência;
2. preservar owners/state authorities existentes;
3. executar primeiro em sandbox/shadow quando possível;
4. exigir evidência antes de promoção;
5. `DEFERIR` não significa descartar;
6. `JÁ EXISTE` não significa que o estudo é inútil: ele pode conter melhorias;
7. nenhum score é autorização de produção;
8. revisão humana permanece obrigatória para mudanças estratégicas.

## Próxima evolução prevista

- usar snapshot real do AS-IS do `ultimecia-code` em vez de depender apenas do cruzamento declarado nos estudos;
- detectar automaticamente ideias deferidas cuja dependência foi satisfeita;
- criar Research Missions por pergunta, não apenas por ideia;
- permitir um agente consumir planos de `RESEARCH` e devolver evidência à War Room;
- manter escrita no repositório de produção atrás de autorização explícita separada.
