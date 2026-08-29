# ULTIMECIA War Room

Central local de acompanhamento do projeto ULTIMECIA.

## Objetivo

Separar claramente três camadas do projeto:

- **Realidade**: o que existe de fato no repositório.
- **Plano**: o que está previsto no roadmap/checklist.
- **Visão**: estudos, hipóteses e melhorias futuras.

A War Room não executa o enxame e não modifica o repositório monitorado. Ela observa, organiza, registra decisões e cruza evidências do GitHub com o checklist local.

## Executar localmente

A aplicação é estática e não exige instalação de dependências.

### Opção 1 — Python

```bash
python -m http.server 8080
```

Acesse `http://localhost:8080`.

### Opção 2 — Node

```bash
npx serve .
```

## GitHub privado

O repositório `ultimecia-code` é privado. Na aba **Configuração**, informe um GitHub Personal Access Token com permissão **somente de leitura** do repositório. O token fica apenas no `localStorage` do navegador e não é enviado para nenhum servidor além da API do GitHub.

> Recomendação: use um fine-grained PAT limitado ao repositório `ultimecia-code` e apenas com `Contents: Read`, `Metadata: Read` e `Actions: Read`.

## Persistência

Checklists, estudos, decisões, dívida técnica, roadmap e configuração ficam no `localStorage`. A aba **Backup** permite exportar/importar um JSON integral da War Room.

## V1

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
