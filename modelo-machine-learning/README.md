# Modelo de machine learning — Sobrevivência Processual (TCC)

Pipeline de pesquisa que mede **quanto tempo um processo leva da distribuição até o mérito/acordo e até o pagamento**,
e treina os modelos que alimentam as páginas **Sobrevivência Processual** e **Previsão Individualizada** do LexHub.
Veio da pasta `TCC - Luiz` da v1 (`lexhub_project/TCC - Luiz`), com o mesmo código; só os caminhos, que eram fixos
na máquina do pesquisador, passaram a ser configuráveis.

## Fases

| # | Script | O que faz |
|---|---|---|
| 2 | `calcular_fase2.py` | Descritiva: Kaplan-Meier, log-rank e rankings de mediana. |
| 3 | `fase3_cox.py`, `fase3_finegray.py` | Cox (hazard ratios) e Fine-Gray (riscos competitivos: acordo × mérito). O Fine-Gray é lento (3 a 30 min). |
| 4 | `fase4_split_temporal.py`, `fase4_cox_mesmo_split.py`, `fase4_xgboost_aft.py`, `fase4_rsf_tuning.py`, `fase4_rsf.py`, `fase4_brier_calibracao.py` | Split temporal treino/teste e os modelos de machine learning: **XGBoost-AFT**, **Random Survival Forest** (com tuning por validação cruzada) e Cox no mesmo split; C-index e Brier integrado. |
| 5 | `fase5_validacao.py`, `fase5_backtest.py`, `diagnostico_generalizacao.py` | Bootstrap pareado (IC95 do C-index), calibração a 90 dias, backtest em origens passadas e o diagnóstico "decorar × aprender". |
| 6 | `fase6_selecao_temporal.py`, `fase6_prototipo_dados.py`, `fase6_procedencia.py`, `fase6_procedencia_2g.py`, `fase6_acordos.py`, `fase6_exportar_bundle_api.py` | Escolha do modelo sem olhar o teste, a grade de previsões do XGBoost-AFT, procedência 1G/2G e acordos; o último grava o JSON da página **Previsão Individualizada** na API da V2 (`apps/api/src/app/analyses/GERAL/data/tcc_previsao_individual.json`). Só dado agregado, nenhum processo individual. |
| — | `historico_versoes.py`, `qualidade_dados.py` | Versões anteriores recalculadas e o apêndice de qualidade dos dados. |
| — | `gerar_capitulo_*.py`, `gerar_doc_*.py`, `gerar_status_*.py`, `gerar_inconsistencias_datas.py` | Geram os capítulos/relatórios em PDF do TCC (não são usados pelo app). |
| — | `atualizar_dashboard_tcc.py`, `fase6_datas_merito.py` | Reextraem dados do LexFlow (`.env` da API). O estudo **não** reextrai a coorte: usa a foto congelada (ver abaixo). |

`coorte_comum.py` tem o que todas as fases compartilham: a carga da coorte, a foto congelada em uso e os grupos de
matéria, comarca, competência e tipo de ação. `rodar_pipeline.py` roda tudo na ordem (cerca de 1h30).

A coorte é a mesma da página Sobrevivência Processual: `sql/coorte_sobrevivencia_2_estagios.sql` (a API usa a cópia
em `apps/api/src/app/source_queries.py`, query `tcc_sobrevivencia_processual`).

## Como rodar

```bash
cd modelo-machine-learning
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt   # versões fixadas em 10/11/2026

# Os dados não ficam no Git (a coorte tem um processo por linha). Copie a pasta dados/ e as backups_fases_*
# (usadas pela etapa 13, histórico de versões) da pasta antiga. Copie em vez de criar link: o pipeline
# regrava dados/ e sobrescreveria os resultados da v1.
cp -a "/home/luiz/lexhub_project/TCC - Luiz/dados" dados
cp -a "/home/luiz/lexhub_project/TCC - Luiz"/backups_* .
# (ou use outra pasta inteira do estudo: export LEXHUB_ML_DIR=/caminho/da/pasta)

.venv/bin/python scripts/rodar_pipeline.py --listar          # as etapas numeradas
.venv/bin/python scripts/rodar_pipeline.py                   # tudo
.venv/bin/python scripts/rodar_pipeline.py --desde 16 --ate 20   # só a Fase 6 e o JSON da página
.venv/bin/python scripts/rodar_pipeline.py --sem-exportar    # sem gravar o JSON na API
```

Variáveis:

- `LEXHUB_ML_DIR` — a pasta do estudo (com `dados/`, onde também saem `logs/` e os PDFs). Padrão: esta pasta.
- `LEXHUB_API_ENV` — o `.env` com o acesso ao LexFlow, para os scripts que reextraem dados. Padrão: `apps/api/.env`.

A foto congelada em uso está em `coorte_comum.SNAPSHOT_DIR` (`dados/congelado_20261119`, com `manifesto.json` e o
hash conferido a cada carga). A foto **final do texto do TCC** é a `congelado_20261110` (hoje a `SNAPSHOT_ANTERIOR`):
para reproduzir os números do TCC, volte `SNAPSHOT_DIR` para ela. Com essa foto, a v2 gera o JSON da página
idêntico ao da v1 (conferido em 19/11/2026).

Para atualizar o estudo com dados novos:

1. `scripts/atualizar_dashboard_tcc.py` e depois `scripts/fase6_datas_merito.py` (gravam `dados/*_atual.parquet`).
2. Copie os dois `*_atual.parquet` para `dados/congelado_AAAAMMDD/` (sem o `_atual`) e escreva o `manifesto.json`
   com o sha256 de cada um e a `data_referencia` (o "hoje" do estudo); use o de uma foto anterior como modelo.
3. Troque `SNAPSHOT_DIR` (e `SNAPSHOT_ANTERIOR`) em `coorte_comum.py` e rode o pipeline.
