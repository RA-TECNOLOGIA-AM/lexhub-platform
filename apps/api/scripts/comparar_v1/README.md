# Comparar V2 × v1 (dashboards LexPre e LexFlow)

Roda o cálculo da v1 (`api_dashboards`) e o módulo da V2 sobre as **mesmas linhas** do banco de origem e compara o
JSON campo a campo. `opcoes_filtro` (novo da V2) fica fora da comparação.

Casos, sempre × mês fechado anterior e mês corrente até hoje, sem filtros (visão de quem gere a unidade):

- **LexPre** (`compare_v1.py`, os `_build_*_response` da v1): Protocolo, Pendências, Organização de Documentos,
  Peticionamento, Comercial e Comissão Comercial (LexPre) × NG/LA/RJ.
- **LexFlow** (`compare_v1_lexflow.py`, as rotas da v1): Execução e Acordos × NG/LA/RJ; Recursal × NG/LA (a v1 não
  tem RJ). Do lado da v1 só a camada de cache (`fetch_data_with_cache`) é trocada para devolver as linhas de
  `rows.pkl`, com o mesmo recorte de situação do processo.

Precisa das duas pastas lado a lado (`C:\workspace\api_dashboards` e `C:\workspace\lexhub-platform`) e do `.env` da V2
com o banco (LexPre e LexFlow abrem de qualquer rede). Em PowerShell, trocando `lexpre` por `lexflow` e
`compare_v1.py` por `compare_v1_lexflow.py` para o LexFlow:

```powershell
$out = "$env:TEMP\comparar_v1_lexpre"
cd C:\workspace\lexhub-platform\apps\api
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe scripts\comparar_v1\fetch_rows.py $out lexpre     # 1. busca as linhas uma vez (rows.pkl)

cd C:\workspace\api_dashboards
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe C:\workspace\lexhub-platform\apps\api\scripts\comparar_v1\compare_v1.py $out   # 2. v1

cd C:\workspace\lexhub-platform\apps\api
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe scripts\comparar_v1\compare_v2.py $out lexpre    # 3. V2 e comparação
```

O passo 3 imprime `IGUAL` ou o número de diferenças por caso e grava `relatorio.json` com exemplos (caminho, v1, V2).

## Resultados

- **LexPre, 11/11/2026:** 36 de 36 iguais. Única variação: a ordem de atendentes **empatados** em
  `tabela_por_atendente` (Comercial) muda de uma execução para outra, na v1 e na V2, porque a v1 não desempata.
- **Banco NG, 12/11/2026** (`compare_v1_lexflow.py <saida> ng` e `compare_v2.py <saida> ng`, linhas de
  `fetch_rows.py <saida> ng`): Protocolo, Peticionamento, Org. de Documentos, Pendências e Comercial × NG/RJ e
  Marketing × NG: 22 de 22 iguais. A Comissão NG usa o mesmo módulo do Comercial. As fontes da LA no Comercial
  (banco LAADV/LexFlow) chegam vazias nos dois lados.
- **LexFlow, 12/11/2026:** Acordos e Recursal 10 de 10 iguais. Execução 6 de 6 com o **mesmo conteúdo**; só a ordem
  dos itens muda em `execucao_atividades_criadas_por_atividade_*` (e `execucao_taxa_conclusao_por_funcionario_LA`).
  A própria v1 muda essa ordem entre duas execuções (conferido rodando a v1 com `PYTHONHASHSEED` diferente): a
  ordem depende do hash do Python, não é um critério da v1.
