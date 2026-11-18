# -*- coding: utf-8 -*-
"""
Roda o pipeline INTEIRO do TCC na ordem certa, a partir da foto congelada da coorte
(coorte_comum.SNAPSHOT_DIR) ate os PDFs dos capitulos. Para no primeiro erro.

Uso (de dentro de modelo-machine-learning/, com o ambiente de requirements.txt ativo):
  python scripts/rodar_pipeline.py                 # tudo
  python scripts/rodar_pipeline.py --listar        # mostra as etapas numeradas
  python scripts/rodar_pipeline.py --desde 9       # a partir da etapa 9
  python scripts/rodar_pipeline.py --desde 9 --ate 12
  python scripts/rodar_pipeline.py --sem-exportar  # nao grava o JSON na API da V2

Log completo em logs/pipeline_AAAAMMDD_HHMM.log. Sem limite de tempo por etapa (o
Fine-Gray leva de 3 a ~30 min conforme a memoria livre). Tempo total tipico: ~1h30.

Nao reextrai a coorte do banco (isso e uma decisao deliberada: ver manifesto.json da foto
congelada). Para atualizar o estudo, criar uma nova foto congelada e trocar SNAPSHOT_DIR.
Ambiente: requirements-tcc.txt (versoes fixadas).
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import argparse
import subprocess
import sys
import time
from datetime import datetime

BASE_DIR = ML_DIR
# V2: o mesmo Python que roda este script (o ambiente de requirements.txt).
PY = sys.executable

# (script, argumentos, descricao)
ETAPAS = [
    ("calcular_fase2.py", [], "Fase 2 - descritiva (KM, log-rank, rankings)"),
    ("fase3_cox.py", [], "Fase 3 - Cox (coorte inteira)"),
    ("fase3_finegray.py", [], "Fase 3 - Fine-Gray (lento)"),
    ("fase4_split_temporal.py", [], "Fase 4 - split temporal treino/teste"),
    ("fase4_cox_mesmo_split.py", [], "Fase 4 - Cox no split"),
    ("fase4_xgboost_aft.py", [], "Fase 4 - XGBoost-AFT (ano + base_score)"),
    ("fase4_rsf_tuning.py", [], "Fase 4 - tuning da RSF (CV no treino)"),
    ("fase4_rsf.py", ["300", "2"], "Fase 4 - RSF final + importancia"),
    ("fase4_brier_calibracao.py", [], "Fase 4 - Brier integrado"),
    ("fase5_validacao.py", [], "Fase 5 - bootstrap pareado + calibracao 90d"),
    ("fase5_backtest.py", [], "Fase 5 - backtest (origens jul/2024, jan/2025)"),
    ("diagnostico_generalizacao.py", [], "Fase 5 - diagnostico de generalizacao (decorar x aprender)"),
    ("historico_versoes.py", [], "Historico - versoes anteriores recalculadas"),
    ("qualidade_dados.py", [], "Qualidade dos dados - foto x dados atuais (*_atual)"),
    ("fase6_selecao_temporal.py", [], "Fase 6 - selecao de modelos sem o teste"),
    ("fase6_prototipo_dados.py", [], "Fase 6 - grade de previsoes do XGBoost-AFT"),
    ("fase6_procedencia.py", [], "Fase 6 - procedencia 1G"),
    ("fase6_procedencia_2g.py", [], "Fase 6 - procedencia 2G"),
    ("fase6_acordos.py", [], "Fase 6 - acordos pre e pos-sentenca"),
    ("fase6_exportar_bundle_api.py", [], "Fase 6 - JSON da pagina (grava no api_dashboards)"),
    ("gerar_capitulo_fase2.py", [], "PDF - capitulo Fase 2"),
    ("gerar_capitulo_fase3.py", [], "PDF - capitulo Fase 3"),
    ("gerar_capitulo_fase4.py", [], "PDF - capitulo Fase 4"),
    ("gerar_capitulo_fase5.py", [], "PDF - capitulo Fase 5"),
    ("gerar_capitulo_fase6.py", [], "PDF - capitulo Fase 6"),
    ("gerar_capitulo_qualidade_dados.py", [], "PDF - Apendice A (qualidade dos dados)"),
    ("gerar_capitulo_conclusao.py", [], "PDF - Capitulo 7 (discussao e conclusao)"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", type=int, default=1)
    ap.add_argument("--ate", type=int, default=len(ETAPAS))
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--sem-exportar", action="store_true")
    a = ap.parse_args()

    if a.listar:
        for i, (s, _, d) in enumerate(ETAPAS, 1):
            print(f"{i:>2}. {d:<52} ({s})")
        return

    log_path = f"{BASE_DIR}/logs/pipeline_{datetime.now():%Y%m%d_%H%M}.log"
    inicio_total = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        for i, (script, args, desc) in enumerate(ETAPAS, 1):
            if not a.desde <= i <= a.ate:
                continue
            if a.sem_exportar and script == "fase6_exportar_bundle_api.py":
                print(f"{i:>2}. {desc} - PULADA (--sem-exportar)")
                continue
            print(f"{i:>2}. {desc} ...", end=" ", flush=True)
            log.write(f"\n===== {i}. {script} {' '.join(args)} ({datetime.now():%H:%M:%S}) =====\n")
            log.flush()
            t0 = time.time()
            r = subprocess.run([PY, "-u", f"{BASE_DIR}/scripts/{script}", *args], cwd=BASE_DIR,
                               stdout=log, stderr=subprocess.STDOUT)
            dt = time.time() - t0
            if r.returncode != 0:
                print(f"FALHOU ({dt:.0f}s, codigo {r.returncode}) - ver {log_path}")
                sys.exit(r.returncode)
            print(f"ok ({dt:.0f}s)")
    print(f"\nConcluido em {(time.time() - inicio_total) / 60:.1f} min. Log: {log_path}")


if __name__ == "__main__":
    main()
