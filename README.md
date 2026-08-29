# ULTIMECIA War Room

Central local de acompanhamento, governança e pesquisa do projeto ULTIMECIA.

## Modelo de verdade

A War Room separa três camadas:

- **Realidade**: o que existe de fato no repositório monitorado.
- **Plano**: o que está previsto no roadmap/checklist.
- **Visão**: estudos, ideias, hipóteses, experimentos e candidatos ainda não incorporados ao código.

A War Room não executa o enxame e não modifica automaticamente o repositório monitorado. Ela observa, organiza, registra decisões e cruza evidências do GitHub com o conhecimento de pesquisa.

## Plataforma de pesquisa V2

A branch `research-platform-v2` amplia a V1 sem trocar sua arquitetura local-first. O corpus inicial contém 20 estudos do Ultimecia, cada um preservado como registro independente com resumo, tese, tags, seções, ideias, hipóteses codificadas, fontes e links de repositórios públicos citados.

O front oferece também **Banco de Ideias**, **Hipóteses**, **Experimentos** e **Fila de Produção**.

Fluxo conceitual:

`Estudo -> Ideia -> análise contra AS-IS -> Hipótese -> Experimento -> Decisão -> Candidato de Produção -> Plano`

A fila de produção é somente um envelope de planejamento. Ela não cria commits, branches ou PRs no `ultimecia-code` por conta própria.

### Classificação contra o AS-IS

Cada ideia pode ser classificada como `PESQUISA`, `JÁ EXISTE`, `EXPANDE`, `SUBSTITUTO CANDIDATO`, `DUPLICA AUTHORITY`, `CERTIFICATION GAP`, `DEFERIR` ou `REJEITAR`.

Isso evita promover como novidade uma capability já implementada e ajuda a identificar propostas que criariam state owners concorrentes.

### Persistência

O corpus de estudos é versionado no próprio repositório nos arquivos `research-study-XX.js`. O trabalho local do usuário - classificações, notas, experimentos e fila - continua no `localStorage` e entra no Backup JSON. PDFs não são embutidos em base64.

## Executar localmente

A aplicação é estática e não exige instalação de dependências.

### Windows

Execute `INICIAR_WAR_ROOM.bat`.

### Python

```bash
python -m http.server 8080
```

Acesse `http://localhost:8080`.

## GitHub privado

O repositório `ultimecia-code` é privado. Na aba **Configuração**, informe um GitHub Personal Access Token somente de leitura. Prefira um fine-grained PAT limitado ao repositório e apenas `Contents: Read`, `Metadata: Read` e `Actions: Read`.

## V1 preservada

- Dashboard executivo
- Sincronização com GitHub
- Branch/commit/Actions/arquivos
- Checklist com evidência automática
- Roadmap/Ondas
- Estudos futuros
- Registro de decisões
- Dívida técnica
- Backup JSON
- Sem backend e sem dependências externas

## V2 adiciona

- Corpus estruturado de 20 estudos
- Detalhamento individual de cada PDF
- Fontes e repositórios públicos por estudo
- Banco de ideias com classificação AS-IS
- Catálogo de hipóteses
- Criação de experimentos falsificáveis
- Fila de produção sem autoridade automática
- Notas de trabalho por estudo
- Indicadores de pesquisa no dashboard

O princípio continua sendo: **Realidade é observada; Plano é deliberado; Visão é estudada antes de virar produção.**
