# Comparar V2 × v1 (dashboards LexPre)

Roda o cálculo da v1 (`api_dashboards`, os `_build_*_response` originais) e o módulo da V2 sobre as **mesmas linhas**
do LexPre e compara o JSON campo a campo. `opcoes_filtro` (novo da V2) fica fora da comparação.

Casos: Protocolo, Pendências, Organização de Documentos, Peticionamento, Comercial e Comissão Comercial (LexPre) ×
NG/LA/RJ × mês fechado anterior e mês corrente até hoje, sem filtros (visão de quem gere a unidade).

Precisa das duas pastas lado a lado (`C:\workspace\api_dashboards` e `C:\workspace\lexhub-platform`) e do `.env` da V2
com o LexPre (o LexPre abre de qualquer rede). Em PowerShell:

```powershell
$out = "$env:TEMP\comparar_v1"
cd C:\workspace\lexhub-platform\apps\api
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe scripts\comparar_v1\fetch_rows.py $out     # 1. busca as linhas uma vez (rows.pkl)

cd C:\workspace\api_dashboards
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe C:\workspace\lexhub-platform\apps\api\scripts\comparar_v1\compare_v1.py $out   # 2. v1

cd C:\workspace\lexhub-platform\apps\api
$env:PYTHONPATH = "$PWD\src"
.venv\Scripts\python.exe scripts\comparar_v1\compare_v2.py $out    # 3. V2 e comparação
```

O passo 3 imprime `IGUAL` ou o número de diferenças por caso e grava `relatorio.json` com exemplos (caminho, v1, V2).

Resultado em 11/11/2026: 36 de 36 iguais. Única variação observada: a ordem de atendentes **empatados** em
`tabela_por_atendente` (Comercial) muda de uma execução para outra, na v1 e na V2, porque a v1 não desempata.
