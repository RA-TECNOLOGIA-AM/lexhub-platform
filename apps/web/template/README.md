# Template HTML do front (protótipo)

Protótipo navegável estático do LexHub V2, com dados fictícios. É uma referência visual e histórica para
[`apps/web`](../README.md), não faz parte do build React e não é a fonte de verdade para as funcionalidades atuais.

## Abrir

Precisa de um servidor HTTP (aberto como arquivo, o navegador não carrega CSS/JS na pré-visualização):

```powershell
python -m http.server 5500 --bind 127.0.0.1 -d apps/web/template
```

Depois, abra http://localhost:5500 (índice com as páginas e estados disponíveis no protótipo).

## Arquivos

| Arquivo | O que é | No React |
|---|---|---|
| `tokens.css` | Cores, tipografia e componentes visuais do protótipo | Inspirou `src/styles/tokens.css`; o React importa sua própria cópia |
| `app.js` | Barra lateral, cabeçalho, dados de demonstração e estados | Referência para layout e componentes React |
| `mock-data.js` | Dados fictícios no formato inicial da API (campos da V1 e bloco `meta`) | Referência de contrato; os mocks atuais ficam em `src/services/mock/` |
| `login.html`, `hub.html`, `protocolo.html`, `pendencias.html` | Markup das telas do protótipo | Referência visual; as rotas atuais estão em `apps/web/src/App.tsx` |

## Como interpretar

- O protótipo retrata um escopo inicial. A aplicação React atual também tem telas de administração, permissões,
  unidades/fontes, auditoria, pedidos de acesso e outros dashboards; confira o [README do front](../README.md).
- Os dados são fictícios. Os exemplos de Protocolo e Pendências seguem o contrato inicial da V1 e não representam
  conexão com uma fonte operacional.
- O bloco `meta` (`unit`, `from`, `to`, `source`, `synced_at`) informa unidade, período e atualização dos dados.
- A distinção entre “No período” e “Situação atual” reflete os indicadores definidos para esse protótipo.
- Os gráficos do template são desenhados com CSS; o template não determina a implementação visual dos dashboards
  atuais.

## Estados (`?estado=`)

`carregando`, `atrasado`, `vazio` e `sem-acesso` nos dashboards; `?convite=…` e
`?estado=sessao-expirada` no login; `hub.html?unit=LA_AM` mostra uma unidade sem dashboards.
