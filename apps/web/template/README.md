# Template HTML do front (MVP / piloto NG)

Páginas estáticas com dados fictícios, a partir do protótipo "LexHub v2 — app navegável".
Servem de referência visual e de contrato de dados para o `apps/web` (React), que começa na terça 10/11.

## Abrir

Precisa de um servidor HTTP (aberto como arquivo, o navegador não carrega CSS/JS na pré-visualização):

```powershell
python -m http.server 5500 --bind 127.0.0.1 -d apps/web/template
```

Depois: http://localhost:5500 (índice com todas as páginas e estados).

## Arquivos

| Arquivo | O que é | No React |
|---|---|---|
| `tokens.css` | Cores, tipografia, componentes (botão, pill, cartão, KPI, tabela, selos, gráficos simples) | Entra **inteiro** |
| `app.js` | Monta barra lateral + cabeçalho, KPIs, gráficos e estados | Vira `<AppLayout>` e componentes |
| `mock-data.js` | Dados fictícios no formato da API (campos da v1 + bloco `meta`) | Vira chamadas à API |
| `login.html`, `hub.html`, `protocolo.html`, `pendencias.html` | Markup de cada tela | Vira as rotas |

## Decisões

- **Escopo do MVP**: administração só leitura ("em breve"); sem plano/cobrança, console da plataforma,
  troca de organização, Google e MFA (estão no protótipo, ficam para depois).
- **Números reais da v1**: os KPIs usam os campos de `ProtocoloLexpreNGResponse` e `PendenciaLexpreNGResponse`
  (ex.: Protocolo não tem "taxa"), para a conferência v2 × v1 ser campo a campo.
- **`meta` na resposta** (novo na V2): `{unit, from, to, source, synced_at}` alimenta "Atualizado há X" e o aviso
  de fonte atrasada (padrão: mais de 60 min sem sincronizar).
- **Separação "No período" × "Situação atual"**: represados, abertas e devolvidos não dependem do período na v1;
  a tela deixa isso explícito.
- **Comissão**: só aparece para quem pode ver (decisão pendente com o gestor).
- **403** não mostra nada do dashboard (nem filtros nem horário dos dados) e informa que a tentativa foi auditada.
- **Gráficos** aqui são CSS puro; no React entra uma biblioteca de gráficos.

## Estados (`?estado=`)

`carregando`, `atrasado`, `vazio`, `sem-acesso` nos dashboards; `?convite=…` e `?estado=sessao-expirada` no login;
`hub.html?unit=LA_AM` mostra unidade sem dashboards.
