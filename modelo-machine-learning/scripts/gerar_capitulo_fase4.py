# -*- coding: utf-8 -*-
"""
Gera Capitulo_Fase4_Resultados.pdf (RSF, XGBoost-AFT, validacao temporal e
Brier Score) - mesmo padrao visual dos capitulos da Fase 2 e Fase 3.

Fontes: scripts/fase4_split_temporal.py, fase4_rsf.py, fase4_rsf_tuning.py,
fase4_cox_mesmo_split.py, fase4_xgboost_aft.py, fase4_brier_calibracao.py e
seus CSVs de saida em dados/fase4_*.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_fase4.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    CondPageBreak,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = ML_DIR
OUT_PDF = f"{BASE_DIR}/Capitulo_Fase4_Resultados.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=20, leading=25, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle(name="SubtituloCapa", fontSize=13, leading=17, fontName="Helvetica", spaceAfter=14, textColor=colors.HexColor("#333333")))
styles.add(ParagraphStyle(name="AutorData", fontSize=10.5, leading=14, fontName="Helvetica"))
styles.add(ParagraphStyle(name="NotaRodapeCapa", fontSize=9, leading=13, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceBefore=18))
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=18, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8, keepWithNext=1))
styles.add(ParagraphStyle(name="H2", fontSize=11.5, leading=15, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6, keepWithNext=1))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=14.5, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="CabecalhoTabela", fontSize=10, leading=14.5, fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle(name="CorpoTabelaNota", fontSize=8.5, leading=12, fontName="Helvetica-Oblique", textColor=colors.HexColor("#444444"), alignment=TA_JUSTIFY, spaceAfter=10))
styles.add(ParagraphStyle(name="Destaque", fontSize=10.5, leading=15, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8, backColor=colors.HexColor("#eef0ff"), borderPadding=8))
styles.add(ParagraphStyle(name="Referencia", fontSize=9.5, leading=14, fontName="Helvetica", leftIndent=14, firstLineIndent=-14, spaceAfter=6))

COR_CABECALHO = colors.HexColor("#2d3142")
COR_ALT = colors.HexColor("#f2f2f5")
COR_DESTAQUE_LINHA = colors.HexColor("#e8f5e9")


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Fase 4: Random Survival Forest e XGBoost-AFT")
    canvas.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


def p(texto, estilo="Corpo"):
    return Paragraph(texto, styles[estilo])


def lista(itens):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["Corpo"]), bulletColor=colors.HexColor("#2d3142")) for item in itens],
        bulletType="bullet", leftIndent=14,
    )


def tabela(linhas, col_widths, header=True, destaque_linhas=None):
    destaque_linhas = destaque_linhas or set()
    estilo_celula = [styles["CabecalhoTabela"] if (header and i == 0) else styles["Corpo"] for i in range(len(linhas))]
    data = [[Paragraph(str(c), estilo_celula[i]) if isinstance(c, str) else c for c in linha]
            for i, linha in enumerate(linhas)]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ]
    if header:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    for i in range(1 if header else 0, len(data)):
        if i in destaque_linhas:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_DESTAQUE_LINHA))
        elif (i - (1 if header else 0)) % 2 == 1:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_ALT))
    t.setStyle(TableStyle(estilo))
    return t


# ---------------------------------------------------------------------------
# Carrega os resultados reais (nunca digitar numero a mao sem checar aqui)
# ---------------------------------------------------------------------------
cv_rsf = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_tuning_cv.csv")
rsf_tunada = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_tunada_metricas.csv").iloc[0]
rsf_palpite = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_metricas.csv").iloc[0]
cox_split = pd.read_csv(f"{BASE_DIR}/dados/fase4_cox_mesmo_split_metricas.csv").iloc[0]
xgb_metricas = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_metricas.csv").iloc[0]
imp_rsf = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_importancia.csv", index_col=0)["importancia"]
imp_xgb = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_importancia.csv", index_col=0)["gain"]
brier = pd.read_csv(f"{BASE_DIR}/dados/fase4_brier_resultado.csv")

N_TREINO = int(rsf_palpite["n_treino"])
N_TESTE = int(rsf_palpite["n_teste"])
EVENTOS_TREINO = int(rsf_palpite["eventos_treino"])
EVENTOS_TESTE = int(rsf_palpite["eventos_teste"])
MELHOR_LEAF = int(rsf_tunada["melhor_min_samples_leaf"])

# Numeros pre-formatados (nunca encadear .replace(".",",") apos concatenacao
# implicita de strings adjacentes - ele aplica no bloco inteiro, nao so no
# ultimo literal. Ver bug corrigido em 02/11/2026: "Seção 3.2" virou "3,2").
N_TREINO_FMT = f"{N_TREINO:,}".replace(",", ".")
N_TESTE_FMT = f"{N_TESTE:,}".replace(",", ".")
PCT_CENSURA_TESTE_FMT = f"{100*(1-EVENTOS_TESTE/N_TESTE):.1f}".replace(".", ",")
PCT_CENSURA_TREINO_FMT = f"{100*(1-EVENTOS_TREINO/N_TREINO):.1f}".replace(".", ",")

_split = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet",
                         columns=["split", "distribuicao_d", "duracao_dias_e1"])
_teste = _split[_split["split"] == "teste"]
CORTE_FMT = _teste["distribuicao_d"].min().strftime("%d/%m/%Y")
FIM_TESTE_FMT = _teste["distribuicao_d"].max().strftime("%d/%m/%Y")
MAX_DUR_TESTE = int(_teste["duracao_dias_e1"].max())
BEST_ITER = int(xgb_metricas["best_iteration"])
N_RODADAS = BEST_ITER + 1
BASE_SCORE_FMT = f"{float(xgb_metricas['base_score']):.0f}"
import json as _json_hist  # noqa: E402
with open(f"{BASE_DIR}/dados/historico_versoes.json", encoding="utf-8") as _fh_hist:
    HIST = _json_hist.load(_fh_hist)  # versoes anteriores recalculadas por historico_versoes.py
# Versoes anteriores na mesma coorte/split, recalculadas por historico_versoes.py (nao digitadas):
# config ANTIGA do XGBoost (sem ano/base_score) e config revista ainda com 24 materias / 8 comarcas.
C_XGB_CONFIG_ANTIGA = HIST["24mat_8com_config_antiga"]["cindex_teste_xgb"]
C_XGB_24_8_FINAL = HIST["24mat_8com_config_revista"]["cindex_teste_xgb"]
C_COX_24_8_FINAL = HIST["24mat_8com_config_revista"]["cindex_teste_cox"]
_CAL_041126 = HIST["calibracao_categorias_041126"]["erro_abs_medio_ponderado"]
# pre-formatado com virgula (gotcha do ReportLab: nada de .replace em string multilinha)
CAL_COM_8, CAL_COM_24 = (f"{_CAL_041126['comarca'][k]:.2f}".replace(".", ",") for k in ("8/8", "24/14"))
CAL_MAT_8, CAL_MAT_24 = (f"{_CAL_041126['materia'][k]:.3f}".replace(".", ",") for k in ("8/8", "24/14"))
import json  # noqa: E402
with open(f"{BASE_DIR}/dados/fase6_selecao_temporal.json", encoding="utf-8") as _fh:
    SELECAO = json.load(_fh)["granularidade"]
SEL = {r["config"]: r for r in SELECAO["resumo"]}
from coorte_comum import TOP_COMARCA as _TOPC, TOP_MATERIA as _TOPM  # noqa: E402
ADOTADA = f"{len(_TOPM)} materias / {len(_TOPC)} comarcas"   # a que o pipeline usa (coorte_comum.TOP_*)
ESCOLHIDA = SELECAO["escolhida"]                     # a que a regra apontou nesta foto
_ROT = lambda k: k.replace(" materias", " matérias")  # noqa: E731
DELTA_C = f"{abs(SEL[ESCOLHIDA]['cindex'] - SEL[ADOTADA]['cindex']):.4f}".replace(".", ",")
CAL_ADOT = f"{SEL[ADOTADA]['erro_calib_medio']:.3f}".replace(".", ",")
CAL_ESC = f"{SEL[ESCOLHIDA]['erro_calib_medio']:.3f}".replace(".", ",")
C_88 = f"{SEL['8 materias / 8 comarcas']['cindex']:.4f}".replace(".", ",")
_bt = pd.read_csv(f"{BASE_DIR}/dados/fase5_backtest_metricas.csv")
BT_C = {(r["origem"], r["modelo"]): r["cindex"] for _, r in _bt.iterrows()}
PALPITE_LEAF = int(rsf_palpite["min_samples_leaf"])
TUNING_IGUAL_PALPITE = MELHOR_LEAF == PALPITE_LEAF
N_PERM_FMT = f"{min(2000, N_TESTE):,}".replace(",", ".")

C_COX, C_RSF, C_XGB = cox_split["cindex_teste"], rsf_tunada["cindex_teste"], xgb_metricas["cindex_teste"]
IBS = {r["modelo"]: r["ibs"] for _, r in brier.iterrows()}
DIFF_COX_XGB_FMT = f"{C_COX - C_XGB:.4f}".replace(".", ",")
DIFF_COX_RSF_FMT = f"{C_COX - C_RSF:.4f}".replace(".", ",")
GAP = {
    "Cox": cox_split["cindex_treino"] - C_COX,
    "RSF": rsf_tunada["cindex_treino"] - C_RSF,
    "XGB": xgb_metricas["cindex_treino"] - C_XGB,
}
GAP_FMT = {k: f"{v:.3f}".replace(".", ",") for k, v in GAP.items()}
REDUCAO_IBS_FMT = f"{100 * (1 - IBS['XGBoost_AFT'] / IBS['Cox']):.0f}"


def fmt4(v):
    return f"{v:.4f}".replace(".", ",")


# --- experimento de granularidade (coorte de 04/11/2026, backups das rodadas) ---
def _metr(pasta):
    cox = pd.read_csv(f"{BASE_DIR}/{pasta}/fase4_cox_mesmo_split_metricas.csv").iloc[0]["cindex_teste"]
    xgb_ = pd.read_csv(f"{BASE_DIR}/{pasta}/fase4_xgboost_metricas.csv").iloc[0]["cindex_teste"]
    rsf_ = pd.read_csv(f"{BASE_DIR}/{pasta}/fase4_rsf_tunada_metricas.csv").iloc[0]["cindex_teste"]
    return cox, xgb_, rsf_
GRAN = {
    "8/8": _metr("backups_fases_pre_ampliacao"),
    "24/14": _metr("backups_fases_ampliado_24mat_14com"),
    "24/8": _metr("backups_fases_hibrido_parcial_041126"),
}
C_COX_041126, C_XGB_041126 = GRAN["8/8"][0], GRAN["8/8"][1]

import sys  # noqa: E402
sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import TOP_COMARCA, TOP_MATERIA  # noqa: E402
N_MAT, N_COM = len(TOP_MATERIA), len(TOP_COMARCA)

_tipo_rsf = imp_rsf[[k for k in imp_rsf.index if k.startswith("tipo_")]]
TIPO_RSF_ZERO = float(_tipo_rsf.abs().max()) < 0.001
TOP1_XGB = imp_xgb.sort_values(ascending=False).index[0]
_rank_xgb = list(imp_xgb.sort_values(ascending=False).index)
RANK_RI_XGB = _rank_xgb.index("tipo_RECURSO_INOMINADO") + 1 if "tipo_RECURSO_INOMINADO" in _rank_xgb else None
N_VARS_XGB = len(_rank_xgb)
_top8 = set(imp_rsf.sort_values(ascending=False).head(8).index) | set(imp_xgb.sort_values(ascending=False).head(8).index)
_rank_rsf = list(imp_rsf.sort_values(ascending=False).index)
RANK_JEC = (_rank_rsf.index("comp_Juizado_Especial_Cível") + 1, _rank_xgb.index("comp_Juizado_Especial_Cível") + 1)
RANK_ANO = _rank_xgb.index("ano_dist") + 1 if "ano_dist" in _rank_xgb else None
COMARCAS_NOVAS_TOP = [c.replace("com_", "").replace("_", " ").title() for c in _rank_xgb[:8]
                      if c.replace("com_", "").replace("_", " ") in
                      {"TABATINGA", "NHAMUNDÁ", "SANTO ANTÔNIO DO IÇÁ", "PRESIDENTE FIGUEIREDO", "HUMAITÁ", "BARREIRINHA"}]
MATERIAS_TOP = [c.replace("mat_", "") for c in ["mat_MORA", "mat_CESTA", "mat_SLN", "mat_RMC", "mat_SVA"] if c in _top8]


from coorte_comum import DATA_REFERENCIA_BR as DATA_FOTO, carregar_coorte as _cc_carregar  # noqa: E402
DADOS_ATE = _cc_carregar()["distribuicao_d"].max().strftime("%d/%m/%Y")  # ultima distribuicao na foto

story = []

# ---------------------------------------------------------------------------
# CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 3 * cm))
story.append(p("Fase 4 — Resultados", "TituloCapa"))
story.append(p(
    "Modelos Não-Paramétricos de Sobrevivência: Random Survival Forest e XGBoost-AFT, com Validação "
    "Temporal",
    "SubtituloCapa",
))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Modelos reajustados sobre a foto de {DATA_FOTO}, com a mesma coorte e covariáveis da Fase 3 (NG+LA, tipo de "
    f"ação, matéria com {N_MAT} categorias, valor de causa, escritório, comarca, competência; t=0 na "
    "distribuição do processo; agravos fora da coorte), mas agora com <b>validação "
    "temporal</b>: o conjunto de teste é separado por data de distribuição, não por sorteio — avalia "
    "se o modelo generaliza para processos futuros, não apenas para uma reamostragem dos mesmos "
    "dados. O Cox da Fase 3 também foi reajustado neste mesmo split, para a comparação ser justa.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. INTRODUCAO
# ---------------------------------------------------------------------------
story.append(p("1. Introdução", "H1"))
story.append(p(
    "A Fase 3 ajustou um modelo multivariado clássico (Cox) e encontrou uma limitação conhecida: a "
    "suposição de riscos proporcionais foi rejeitada para a maioria das covariáveis — sinal de que o "
    "efeito real de cada variável provavelmente não é constante ao longo do tempo nem estritamente "
    "linear nos coeficientes. Esta fase avalia se dois modelos não-paramétricos — Random Survival "
    "Forest (RSF) e XGBoost com função de perda AFT (Accelerated Failure Time) — capturam esse tipo "
    "de padrão melhor que o Cox, usando exatamente as mesmas covariáveis."
))
story.append(p(
    "Diferente das Fases 2 e 3 (ajustadas e avaliadas sobre a coorte inteira), esta fase introduz uma "
    "mudança metodológica relevante: <b>validação temporal</b>. O motivo é concreto — um modelo que "
    "decora padrões específicos do passado pode performar bem numa reamostragem aleatória dos mesmos "
    "dados sem necessariamente prever bem processos que ainda vão ser distribuídos. Separar por data "
    "de distribuição simula esse cenário real e antecipa, para esta fase, o cuidado que o plano "
    "original já previa para a Fase 5."
))

# ---------------------------------------------------------------------------
# 2. METODOLOGIA
# ---------------------------------------------------------------------------
story.append(p("2. Metodologia", "H1"))
story.append(p("2.1 Escopo e split temporal", "H2"))
story.append(p(
    "Mesma coorte NG+LA da Fase 3. A coorte foi ordenada por data de distribuição e dividida no "
    f"quantil 80%: os {N_TREINO_FMT} processos distribuídos antes de {CORTE_FMT} "
    f"formam o treino; os {N_TESTE_FMT} processos distribuídos a partir dessa data (até "
    f"{FIM_TESTE_FMT}) formam o teste, nunca usado para ajustar nenhum modelo. Como esperado, o teste tem "
    f"mais censura que o treino ({PCT_CENSURA_TESTE_FMT}% vs. {PCT_CENSURA_TREINO_FMT}%) — processos "
    "mais recentes têm menos tempo de tramitar até a data de extração, então menos deles já têm "
    "desfecho conhecido. Isso não é erro: é exatamente a dificuldade adicional que a validação "
    "temporal deve capturar. Uma consequência importante: o processo mais antigo do teste tem só "
    f"{MAX_DUR_TESTE} dias de acompanhamento, então toda avaliação no teste (C-index, Brier) mede o "
    "desempenho dos modelos nos primeiros meses de tramitação."
))
story.append(p(
    "O evento usado é o mesmo da Fase 3, all-cause (qualquer desfecho vs. censurado) — nem RSF nem "
    "XGBoost-AFT têm, nas bibliotecas usadas, um equivalente nativo ao Fine-Gray de riscos "
    "competitivos; isso fica registrado como limitação (Seção 5)."
))
story.append(p("2.2 Random Survival Forest", "H2"))
story.append(p(
    "RSF (ISHWARAN et al., 2008) estende Random Forest para dados censurados: cada árvore divide os "
    "dados maximizando a separação entre curvas de sobrevivência dos grupos resultantes, e a previsão "
    "final agrega as árvores da floresta. Implementação: <code>scikit-survival</code>. O "
    "hiperparâmetro mais sensível — <code>min_samples_leaf</code> (tamanho mínimo de folha, controla "
    "o quão profundo cada árvore cresce) — foi escolhido por validação cruzada de 3 folds, só dentro "
    "do treino (nunca toca o teste), testando os valores 5, 15, 30 e 50:"
))
story.append(tabela(
    [["min_samples_leaf", "C-index médio (CV)", "Desvio padrão"]] + [
        [str(int(r["param_min_samples_leaf"])), fmt4(r["mean_test_score"]), fmt4(r["std_test_score"])]
        for _, r in cv_rsf.iterrows()
    ],
    [5 * cm, 5.5 * cm, 5.5 * cm],
    destaque_linhas={cv_rsf.reset_index(drop=True)["mean_test_score"].idxmax() + 1},
))
story.append(Spacer(1, 6))
TEXTO_TUNING = (
    f"O melhor valor ({MELHOR_LEAF}) coincide com o palpite inicial usado antes do tuning (leaf={PALPITE_LEAF}) "
    "— a busca confirmou o palpite, não melhorou nada. As diferenças entre 15, 30 e 50 são menores que o desvio "
    "padrão entre folds; só leaf=5 (árvores mais profundas) piora de forma clara."
    if TUNING_IGUAL_PALPITE else
    f"O melhor valor ({MELHOR_LEAF}) difere do palpite inicial (leaf={PALPITE_LEAF})."
)
story.append(p(
    f"{TEXTO_TUNING} A RSF final foi reajustada no treino inteiro com 300 árvores, "
    "<code>max_features='sqrt'</code>. Para caber na memória da máquina de pesquisa, o ajuste usa "
    "<code>low_memory=True</code> (guarda só o risco, suficiente para o C-index); onde as curvas de "
    "sobrevivência são necessárias (Brier, calibração da Fase 5), a floresta é ajustada em blocos menores.",
    "CorpoTabelaNota",
))
story.append(p("2.3 XGBoost-AFT", "H2"))
story.append(p(
    "XGBoost com <code>objective='survival:aft'</code> ajusta um modelo de tempo de falha acelerado: "
    "em vez de prever risco (hazard), prevê diretamente o tempo de sobrevivência, assumindo que "
    "log(T) segue uma distribuição escolhida (aqui, Normal — equivalente a uma AFT log-normal) em "
    "torno de uma localização que a árvore de boosting estima a partir das covariáveis. Cada linha "
    "entra no treino como um intervalo: evento observado vira [duração, duração] (tempo exato "
    "conhecido); censurado vira [duração, +∞) (sabe-se apenas que sobreviveu até ali). O número de "
    "rodadas de boosting foi escolhido por early stopping numa partição de validação interna (85/15 "
    f"do treino, respeitando a mesma ordem temporal) — a melhor iteração foi a {BEST_ITER} ({N_RODADAS} "
    "rodadas), de um máximo de 2.000."
))
story.append(p(
    "<b>Configuração revista após o backtest (09/11/2026).</b> O backtest da Fase 5 (Seção \"Backtest com "
    "acompanhamento longo\") mostrou dois problemas na configuração original. Primeiro, com taxa de "
    "aprendizado 0,05 o modelo parte de um nível inicial baixo e precisa de muitas rodadas para chegar ao "
    "nível real dos prazos — o <i>nível</i> das previsões dependia de quantas rodadas o early stopping "
    "escolhia (numa das origens parou em 36 e as medianas saíram 2 a 3 vezes curtas demais). Segundo, os "
    "processos ficaram mais rápidos ao longo do tempo (mediana de cerca de 720 dias para os distribuídos em "
    "2022, 250 em 2024 e 190 em 2025), e um modelo que não sabe a 'época' do processo prevê o ritmo antigo. "
    "Duas mudanças foram adotadas: (i) o <b>ano de distribuição</b> entra como covariável numérica "
    "(<code>ano_dist</code>; para um processo novo usa-se a data de referência, e as árvores aplicam o "
    "ritmo mais recente que viram); (ii) o ponto de partida do boosting (<code>base_score</code>) passa a ser "
    f"a mediana de Kaplan-Meier do treino ({BASE_SCORE_FMT} dias), de modo que as árvores só aprendem as "
    "diferenças entre casos. A configuração foi escolhida pelo backtest (origens passadas), não olhando o "
    "conjunto de teste desta fase. Cox e RSF não mudaram."
))
story.append(p("2.4 Escolha da granularidade das categorias", "H2"))
story.append(p(
    "Até 04/11/2026 matéria e comarca entravam com as 8 categorias de maior volume cada, e o 'Outros' de "
    "matéria juntava 49% do treino, com medianas de cerca de 180 dias (SVA) a mais de 600 (JUROS_ABUSIVOS) — "
    "o modelo não tinha como distinguir essas matérias. Testou-se um critério objetivo: toda categoria com pelo "
    "menos 300 processos na coorte de modelagem vira categoria própria. Aplicado às duas dimensões, isso dá "
    "24 matérias e 14 comarcas. <b>Primeira escolha (descartada):</b> as três configurações foram comparadas no "
    "conjunto de teste da coorte de 04/11/2026 (configuração antiga do XGBoost-AFT):"
))
story.append(tabela(
    [["Matérias / comarcas", "Cox (teste)", "XGBoost-AFT (teste)", "RSF (teste)"]] + [
        [rotulo, fmt4(GRAN[k][0]), fmt4(GRAN[k][1]), fmt4(GRAN[k][2])]
        for k, rotulo in (("8/8", "8 / 8 (original)"), ("24/14", "24 / 14 (critério nas duas)"),
                          ("24/8", "24 / 8"))
    ],
    [5.6 * cm, 3.4 * cm, 4 * cm, 3.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "Por essa tabela, ampliar as duas dimensões piorava todos os modelos. A calibração por categoria apontava "
    "na mesma direção: no teste de 04/11, o erro médio de calibração a 90 dias nas comarcas novas subia de "
    f"{CAL_COM_8} (8/8) para {CAL_COM_24} (24/14), enquanto nas "
    f"matérias novas quase não mudava ({CAL_MAT_8} para {CAL_MAT_24}) "
    "— a escolha foi 24 matérias / 8 comarcas. O problema é que a decisão foi tomada <b>olhando o conjunto de teste</b> — o teste deixa de ser "
    "uma avaliação independente quando é usado para escolher a especificação.",
    "CorpoTabelaNota",
))
story.append(p(
    "<b>Escolha final (sem o teste).</b> A decisão foi refeita no backtest da Fase 5 (origens jul/2024 e "
    "jan/2025), cujas janelas de avaliação são processos distribuídos em 2024 e 2025 — nenhum deles está no "
    "teste desta fase — com o XGBoost-AFT na configuração revista (Seção 2.3) e uma regra fixada antes de "
    "rodar: vence a configuração de maior C-index médio nas duas origens (script "
    "<code>fase6_selecao_temporal.py</code>):"
))
story.append(tabela(
    [["Matérias / comarcas", "C-index médio (backtest)", "Erro médio de calibração (180–730 d)"]] + [
        [k.replace(" materias", " matérias"), fmt4(SEL[k]["cindex"]), f"{SEL[k]['erro_calib_medio']:.3f}".replace(".", ",")]
        for k in ("8 materias / 8 comarcas", "24 materias / 8 comarcas", "24 materias / 14 comarcas")
    ],
    [5.6 * cm, 4.6 * cm, 5.8 * cm],
    destaque_linhas={1 + ("8 materias / 8 comarcas", "24 materias / 8 comarcas",
                          "24 materias / 14 comarcas").index(ADOTADA)},
))
story.append(Spacer(1, 6))
if ESCOLHIDA == ADOTADA:
    _txt_escolha = (
        f"Sem olhar o teste, a melhor configuração é a ampliada nas duas dimensões: {N_MAT} matérias e {N_COM} "
        "comarcas — o contrário da primeira escolha. ")
else:
    _txt_escolha = (
        f"Na foto de 09/11/2026 a regra apontou {_ROT(ADOTADA)} — o contrário da primeira escolha — e essa passou "
        f"a ser a configuração do estudo. Na foto final a mesma regra apontou {_ROT(ESCOLHIDA)}, por uma diferença "
        f"de {DELTA_C} no C-index médio (um empate na prática), enquanto {_ROT(ADOTADA)} teve o menor erro de "
        f"calibração ({CAL_ADOT} contra {CAL_ESC}). <b>O estudo manteve {_ROT(ADOTADA)}</b>; usar a calibração "
        "como desempate foi decidido depois de ver o resultado, e fica registrado como limitação. Na prática, a "
        "granularidade da comarca não muda as conclusões — o que pesa é ampliar as matérias (8 matérias / 8 "
        f"comarcas: {C_88}). ")
story.append(p(
    _txt_escolha +
    "Competência (4 categorias, cerca de 96% da coorte) e tipo de "
    "ação não mudaram. <b>O custo honesto dessa disciplina:</b> no teste final, a configuração descartada (24/8) "
    f"daria ao XGBoost-AFT um C-index de {fmt4(C_XGB_24_8_FINAL)}, contra {fmt4(C_XGB)} da adotada — o teste "
    "'preferiria' a outra, por uma diferença pequena. É exatamente o que se aceita ao não usar o teste para "
    "escolher: o número reportado na Seção 3 é uma estimativa honesta do desempenho em processos futuros, e "
    "não o melhor de várias tentativas no mesmo conjunto.",
    "CorpoTabelaNota",
))
story.append(p("2.5 Métricas de avaliação", "H2"))
story.append(p(
    "Além do C-index (Fase 3, Seção 3.1 — mede se o modelo ordena corretamente quem resolve mais "
    "rápido), esta fase acrescenta o <b>Brier Score integrado</b> (IBS): mede a distância quadrática "
    "entre a probabilidade de sobrevivência prevista e o desfecho real observado, integrada ao longo "
    "de uma grade de tempo, ponderada para corrigir o viés que a censura introduziria numa comparação "
    "ingênua. IBS = 0 é previsão perfeita; IBS ≈ 0,25 é o nível de um 'chute constante' de 50% de "
    "chance de sobrevivência para todo mundo, em todo tempo — serve de piso de comparação. A grade vai de "
    "15 a 210 dias (de 15 em 15), dentro do acompanhamento máximo do teste."
))

# ---------------------------------------------------------------------------
# 3. RESULTADOS
# ---------------------------------------------------------------------------
story.append(CondPageBreak(6 * cm))
story.append(p("3. Resultados", "H1"))
story.append(p("3.1 C-index — comparação direta (mesmo split temporal)", "H2"))
linhas_cindex = [
    ["Modelo", "C-index (treino)", "C-index (teste)"],
    ["Cox (Fase 3, reajustado no split)", fmt4(cox_split["cindex_treino"]), fmt4(cox_split["cindex_teste"])],
    ["RSF — palpite único (leaf=15)", fmt4(rsf_palpite["cindex_treino"]), fmt4(rsf_palpite["cindex_teste"])],
    [f"RSF — tunada (leaf={MELHOR_LEAF})", fmt4(rsf_tunada["cindex_treino"]), fmt4(rsf_tunada["cindex_teste"])],
    ["XGBoost-AFT", fmt4(xgb_metricas["cindex_treino"]), fmt4(xgb_metricas["cindex_teste"])],
]
_melhor_linha = 1 + max(range(4), key=lambda k: [C_COX, rsf_palpite["cindex_teste"], C_RSF, C_XGB][k])
story.append(tabela(linhas_cindex, [7 * cm, 4.7 * cm, 4.3 * cm], destaque_linhas={_melhor_linha}))
story.append(Spacer(1, 6))
DIFF_XGB_COX_FMT = f"{C_XGB - C_COX:.4f}".replace(".", ",")
story.append(p(
    f"No C-index de teste, o <b>XGBoost-AFT fica à frente</b> ({fmt4(C_XGB)}), seguido pelo Cox "
    f"({fmt4(C_COX)}, diferença de {DIFF_XGB_COX_FMT}) e pela RSF ({fmt4(C_RSF)}). Como o tuning da RSF "
    "escolheu o mesmo leaf do palpite, as duas linhas de RSF são idênticas. Os dois modelos de árvore têm "
    "C-index de treino mais alto que o Cox e perdem mais do treino para o teste (queda de "
    f"{GAP_FMT['RSF']} na RSF e {GAP_FMT['XGB']} no XGBoost, contra {GAP_FMT['Cox']} no Cox) — parte do que "
    "aprendem no histórico não se repete nos processos mais recentes —, mas o XGBoost-AFT ainda termina acima. "
    "<b>Histórico desta comparação:</b> com t=0 na contratação, o XGBoost-AFT superava o Cox (0,6476 vs. "
    "0,6314); com t=0 na distribuição e 8 matérias (04/11/2026), o Cox ficou à frente "
    f"({fmt4(C_COX_041126)} vs. {fmt4(C_XGB_041126)}); com 24 matérias, o XGBoost-AFT volta à frente "
    f"({fmt4(C_XGB_CONFIG_ANTIGA)}); com a configuração revista (ano de distribuição e ponto de partida, Seção "
    f"2.3) sobe para {fmt4(C_XGB_24_8_FINAL)}; e com as {N_COM} comarcas escolhidas sem o teste (Seção 2.4) fica "
    f"em {fmt4(C_XGB)} — ainda à frente do Cox. O preço é uma distância maior entre "
    f"treino e teste ({GAP_FMT['XGB']}): o modelo agora também aprende o efeito da época. Se a diferença é "
    "significativa é a pergunta da Fase 5 (bootstrap pareado)."
))
story.append(p("3.2 Brier Score integrado (IBS)", "H2"))
story.append(tabela(
    [["Modelo", "IBS (teste)"]] + [[row["modelo"].replace("_", " "), fmt4(row["ibs"])] for _, row in brier.iterrows()],
    [8 * cm, 8 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "O XGBoost-AFT tem o IBS bem mais baixo "
    f"({fmt4(IBS['XGBoost_AFT'])}, {REDUCAO_IBS_FMT}% menor que o do Cox), a RSF fica no meio e o Cox é o "
    "pior — a mesma ordem do C-index, mas com distância muito maior. As duas métricas medem coisas diferentes: "
    "o C-index só olha a ORDEM (quem resolve antes de quem); o Brier olha se a PROBABILIDADE prevista bate com "
    "o que aconteceu. A diferença de ordenação entre Cox e XGBoost-AFT é pequena; a de probabilidade é grande "
    "— a Fase 5 mostra onde (calibração por quartil). Os três ficam abaixo do piso de 'chute constante' "
    "(≈0,25).",
    "CorpoTabelaNota",
))
story.append(p("3.3 Importância de variável", "H2"))
story.append(p(
    "RSF (permutation importance, amostra de 2.000 processos do teste) e XGBoost-AFT (importância "
    "por ganho, nativa do boosting) contam histórias parcialmente diferentes:",
))
top_rsf = imp_rsf.sort_values(ascending=False).head(8)
top_xgb = imp_xgb.sort_values(ascending=False).head(8)
linhas_imp = [["RSF (permutation)", "XGBoost-AFT (gain)"]]
for (nome_r, val_r), (nome_x, val_x) in zip(top_rsf.items(), top_xgb.items()):
    linhas_imp.append([f"{nome_r} ({val_r:.4f})", f"{nome_x} ({val_x:.1f})"])
story.append(tabela(linhas_imp, [8 * cm, 8 * cm]))
story.append(Spacer(1, 6))
story.append(p(
    "Nos dois modelos, comarca, competência e matéria concentram boa parte da importância — consistente com o "
    f"Cox (Fase 3); competência (Juizado Especial Cível) é a {RANK_JEC[0]}ª variável na RSF e a {RANK_JEC[1]}ª no "
    "XGBoost-AFT"
    + (f", matérias específicas ({', '.join(MATERIAS_TOP)}) aparecem entre as 8 primeiras" if MATERIAS_TOP else "")
    + (f", e comarcas que só viraram categoria própria com a ampliação ({', '.join(COMARCAS_NOVAS_TOP)}) estão "
       "entre as 8 primeiras do XGBoost-AFT" if COMARCAS_NOVAS_TOP else "")
    + ". A diferença notável está "
    "em <b>tipo de ação</b>: na RSF, as categorias de tipo de ação aparecem com "
    + ("importância ≈0" if TIPO_RSF_ZERO else "importância baixa")
    + "; no XGBoost-AFT, o grupo 'Outros' de tipo de ação está entre as primeiras e RECURSO INOMINADO "
    + (f"fica na {RANK_RI_XGB}ª posição de {N_VARS_XGB}" if RANK_RI_XGB else "não aparece")
    + ". A leitura mais provável não é que tipo de ação "
    "'não importa' — é que permutation importance subestima variáveis correlacionadas (a floresta "
    "compensa embaralhar uma coluna usando outra, correlacionada, como comarca ou matéria), enquanto "
    "a importância por ganho do boosting é menos sensível a esse efeito. Tratar isso como 'tipo de "
    "ação não importa' seria uma leitura equivocada do método, não um achado substantivo. No "
    f"XGBoost-AFT, o <b>ano de distribuição</b> é a {RANK_ANO}ª variável — confirma que a época do "
    "processo carrega informação sobre o prazo (os processos ficaram mais rápidos ao longo do tempo)."
))

# ---------------------------------------------------------------------------
# 4. DISCUSSAO
# ---------------------------------------------------------------------------
story.append(CondPageBreak(6 * cm))
story.append(p("4. Discussão", "H1"))
story.append(p(
    "A hipótese que motivou esta fase — um modelo não-paramétrico capturaria interação ou "
    "não-linearidade que o Cox perde — <b>se confirma para o XGBoost-AFT, na discriminação e na "
    "calibração</b>: ele tem o maior C-index de teste e o menor Brier Score. A RSF não acompanha: fica abaixo "
    "do Cox em C-index e no meio em Brier. A vantagem do XGBoost-AFT em discriminação é pequena em valor "
    "absoluto (se ela é consistente é a pergunta da Fase 5); a de calibração é grande, e é ela que importa "
    "para estimar a PROBABILIDADE de um processo já ter resolvido em t dias — o que uma previsão "
    "individualizada mostra ao usuário."
))
story.append(p(
    "A Seção 2.4 mostra que esse resultado depende da granularidade das categorias. Com 8 matérias e 8 "
    "comarcas, a estrutura era a mais favorável ao Cox — poucas dummies, em que um modelo linear já captura a "
    f"maior parte do sinal de ordenação — e ele ficou à frente. Com {N_MAT} matérias e {N_COM} comarcas, o Cox "
    f"estima {N_MAT - 8 + N_COM - 8} efeitos fixos a mais, cada um suposto constante no tempo (suposição já "
    "rejeitada para a maioria das covariáveis na Fase 3), e praticamente não ganha fora da amostra; os modelos de "
    "árvore conseguem usar a informação nova sem tratá-la como efeito fixo, e o XGBoost-AFT melhora. A vantagem dele em calibração tem outra origem provável: por ser um "
    "modelo AFT paramétrico (log-normal), ele prevê diretamente o tempo, e não depende de um hazard basal "
    "estimado no histórico inteiro, como o Cox."
))
story.append(p(
    "O backtest da Fase 5 trouxe um achado que vale para qualquer modelo deste problema: o ritmo da carteira "
    "mudou com o tempo. Um modelo treinado no histórico, sem saber a época do processo, prevê prazos do "
    "passado. Incluir o ano de distribuição corrigiu isso no XGBoost-AFT e melhorou o C-index no split oficial "
    f"(de {fmt4(C_XGB_CONFIG_ANTIGA)} para {fmt4(C_XGB)}) e nas duas origens do backtest. O Cox não recebeu "
    "a mesma covariável: num modelo linear ela extrapolaria a tendência indefinidamente para o futuro, o que as "
    "árvores não fazem (usam o ritmo do período mais recente)."
))

# ---------------------------------------------------------------------------
# 5. LIMITACOES
# ---------------------------------------------------------------------------
story.append(p("5. Limitações", "H1"))
story.append(lista([
    "Sem riscos competitivos: nem RSF (scikit-survival) nem XGBoost-AFT têm um equivalente nativo ao "
    "Fine-Gray da Fase 3 — os resultados desta fase comparam com o Cox geral (Seção 3.2 da Fase 3), "
    "não com o Fine-Gray.",

    "Busca de hiperparâmetro pequena, por restrição de ambiente computacional (poucos núcleos/RAM "
    "disponíveis nesta máquina de pesquisa): a RSF testou só 4 valores de min_samples_leaf, com "
    "n_estimators reduzido durante a busca; uma busca mais ampla (mais valores, mais árvores por "
    "candidato) poderia encontrar um ajuste ainda melhor.",

    "Escala da distribuição AFT fixada em 1,0 (não otimizada): o XGBoost-AFT assumiu "
    "aft_loss_distribution_scale=1,0 por simplicidade; tratar a escala como mais um hiperparâmetro a "
    "buscar poderia mudar tanto o C-index quanto a calibração deste modelo.",

    f"Horizonte curto no teste: o acompanhamento máximo neste split é de {MAX_DUR_TESTE} dias, então C-index e "
    "Brier desta fase medem os primeiros meses de tramitação. Prazos longos são avaliados à parte, no backtest da "
    "Fase 5 (origens jul/2024 e jan/2025, acompanhamento mínimo de 682 e 497 dias).",

    "Poucos cortes temporais: além deste split, o backtest da Fase 5 usa duas origens. Origens mais antigas "
    "(2023, jan/2024) não serviram — a carteira só ganha volume em 2024, e o treino nessas datas tinha poucos "
    "desfechos registrados.",

    "Ano de distribuição como covariável: para um processo novo, o modelo usa o ritmo do período mais recente do "
    "treino. Se a carteira acelerar ou desacelerar de novo, o modelo só acompanha quando for retreinado.",

    "A granularidade das categorias (Seção 2.4) foi escolhida pelo backtest, sem o teste final, mas com só duas "
    "origens e uma diferença pequena entre as configurações (C-index médio de "
    f"{fmt4(SEL['24 materias / 14 comarcas']['cindex'])} contra {fmt4(SEL['24 materias / 8 comarcas']['cindex'])}); "
    "no teste final a alternativa descartada teria se saído um pouco melhor. As listas de categorias foram "
    "derivadas da frequência na coorte inteira (não do desfecho) — vazamento mínimo, aceito.",

    f"Permutation importance com amostra reduzida do teste ({N_PERM_FMT} de {N_TESTE_FMT} processos) e poucas "
    "repetições (3), por custo computacional — os valores de importância da RSF devem ser lidos como "
    "indicativos de ordem de grandeza, não como estimativa de precisão fina.",
]))

# ---------------------------------------------------------------------------
# 6. SINTESE
# ---------------------------------------------------------------------------
story.append(p("6. Síntese", "H1"))
story.append(p(
    f"Com validação temporal (treino nos {N_TREINO_FMT} processos mais antigos, teste nos {N_TESTE_FMT} "
    f"mais recentes), o XGBoost-AFT é o melhor modelo em discriminação (C-index de teste {fmt4(C_XGB)}, contra "
    f"{fmt4(C_COX)} do Cox e {fmt4(C_RSF)} da RSF) e, de longe, em calibração (Brier Score integrado "
    f"{fmt4(IBS['XGBoost_AFT'])} contra {fmt4(IBS['RSF_tunada'])} da RSF e {fmt4(IBS['Cox'])} do Cox). O tuning "
    "da RSF apenas confirmou o palpite inicial. O resultado em discriminação depende da granularidade das "
    f"categorias ({N_MAT} matérias e {N_COM} comarcas, escolhidas pelo backtest e não pelo teste) e da época: o "
    "ano de distribuição como covariável e o ponto de partida no nível certo tornaram o XGBoost-AFT estável "
    f"entre cortes temporais (C-index de teste {fmt4(C_XGB_CONFIG_ANTIGA)} na configuração anterior). "
    "A Fase 5 testa se a vantagem é consistente e valida os prazos longos com um backtest."
))

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(PageBreak())
story.append(p("Referências", "H1"))
for ref in [
    "ISHWARAN, H. et al. Random Survival Forests. <i>The Annals of Applied Statistics</i>, v. 2, n. 3, p. 841-860, 2008.",
    "CHEN, T.; GUESTRIN, C. XGBoost: A Scalable Tree Boosting System. In: <i>Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining</i>, 2016, p. 785-794.",
    "BARNWAL, A.; CHO, H.; HOCKING, T. Survival Regression with Accelerated Failure Time Model in XGBoost. <i>Journal of Computational and Graphical Statistics</i>, v. 31, n. 4, p. 1292-1302, 2022.",
    "GRAF, E. et al. Assessment and Comparison of Prognostic Classification Schemes for Survival Data. <i>Statistics in Medicine</i>, v. 18, n. 17-18, p. 2529-2545, 1999. (Brier Score integrado para dados censurados.)",
    "COX, D. R. Regression Models and Life-Tables. <i>Journal of the Royal Statistical Society: Series B</i>, v. 34, n. 2, p. 187-220, 1972.",
]:
    story.append(p(ref, "Referencia"))

story.append(Spacer(1, 10))
story.append(p(
    "Este capítulo complementa o Capitulo_Fase2_Resultados.pdf e o Capitulo_Fase3_Resultados.pdf, na "
    "mesma pasta de pesquisa. Scripts reprodutíveis: scripts/fase4_split_temporal.py, "
    "scripts/fase4_rsf.py, scripts/fase4_rsf_tuning.py, scripts/fase4_cox_mesmo_split.py, "
    "scripts/fase4_xgboost_aft.py, scripts/fase4_brier_calibracao.py, scripts/fase5_backtest.py e "
    "scripts/gerar_capitulo_fase4.py (este documento).",
    "CorpoTabelaNota",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Fase 4: Random Survival Forest e XGBoost-AFT",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
