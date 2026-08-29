# ULTIMECIA Research Runner v3

## Regra central

O Runner pode aumentar autonomia de **pesquisa**, mas continua sem autoridade de produção.

`Research autonomy != production authority.`

## Ferramentas controladas

### GitHub read-only

Para o `targetRepo`, o Runner pode consultar pela API pública do GitHub:

- metadata do repositório;
- branch padrão;
- HEAD real;
- commits recentes;
- árvore de arquivos.

Também pode consultar até cinco repositórios explicitamente presentes em `repositoryLinks` do Work Package.

O Runner não possui código para commit, branch, PR, merge, issue mutation ou Contents API de escrita.

`ULTIMECIA_GITHUB_TOKEN` é opcional e serve apenas para autenticação de leitura/rate limit. Nunca deve ser incluído em Work Packages ou no repositório.

### Web read-only

O Runner pode abrir via HTTPS até seis URLs já presentes em `sourceLinks` do Work Package. Nesta versão ele **não faz crawling aberto nem pesquisa arbitrária por palavras-chave**. Isso limita prompt injection, deriva de escopo e coleta acidental.

Pode ser desligado com:

`ULTIMECIA_RESEARCH_WEB=0`

GitHub pode ser desligado com:

`ULTIMECIA_RESEARCH_GITHUB=0`

O limite padrão é 12 evidências por job e pode ser ajustado por `ULTIMECIA_RESEARCH_MAX_EVIDENCE`.

## Evidence Ledger

Toda evidência externa coletada recebe:

- `evidenceId` estável dentro do job (`EV-001`, ...);
- tipo (`github`, `web`, `gap`);
- claim de coleta;
- referência;
- excerpt limitado;
- timestamp;
- hash de conteúdo;
- metadata quando disponível.

O provider recebe o ledger separado do Work Package e é instruído a citar `evidenceId` nos findings externos.

## Fail closed

O job é recusado quando:

- `productionWrite != false`; ou
- authority não é `research-only`/`none`.

O Runner não implementa nenhuma chamada de escrita ao GitHub.

Decisões `ADOPT`, `ADAPT` e `CERTIFY` terminam no gate humano. Sem provider configurado, o Runner pode coletar evidência, mas termina em `WAITING_EXECUTOR` e não inventa conclusão.

## Evolução posterior

Antes de permitir busca web aberta, adicionar:

1. allowlist/denylist de domínios;
2. orçamento por missão;
3. sanitização explícita de conteúdo não confiável;
4. provenance graph;
5. detecção de instruções hostis em páginas;
6. política por categoria de pesquisa;
7. cache e deduplicação cross-job;
8. avaliação de qualidade/autoridade das fontes.

Mesmo após essas evoluções, escrita de produção permanece em uma capability separada e não deve ser incorporada ao Research Runner.