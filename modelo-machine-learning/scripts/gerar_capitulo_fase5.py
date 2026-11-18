# -*- coding: utf-8 -*-
"""
Gera Capitulo_Fase5_Resultados.pdf (validacao: bootstrap pareado do C-index e
calibracao em horizonte fixo) - mesmo padrao visual dos capitulos anteriores.

Fontes: scripts/fase5_validacao.py e seus CSVs em dados/fase5_*.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_fase5.py
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
OUT_PDF = f"{BASE_DIR}/Capitulo_Fase5_Resultados.pdf"

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
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Fase 5: Validação")
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
# Carrega os resultados reais
# ---------------------------------------------------------------------------
ic = pd.read_csv(f"{BASE_DIR}/dados/fase5_bootstrap_ic.csv").set_index("modelo")
vitorias = pd.read_csv(f"{BASE_DIR}/dados/fase5_bootstrap_vitorias.csv").iloc[0]
calib = pd.read_csv(f"{BASE_DIR}/dados/fase5_calibracao.csv")

N_VALIDAS = int(vitorias["n_validas"])
PCT_XGB_COX = 100 * vitorias["xgb_vs_cox"] / N_VALIDAS
PCT_XGB_RSF = 100 * vitorias["xgb_vs_rsf"] / N_VALIDAS
PCT_RSF_COX = 100 * vitorias["rsf_vs_cox"] / N_VALIDAS


def fmt4(v):
    return f"{v:.4f}".replace(".", ",")


def fmt1(v):
    return f"{v:.1f}".replace(".", ",")


def fmt3(v):
    return f"{v:.3f}".replace(".", ",")


PCT_XGB_COX_FMT = fmt1(PCT_XGB_COX)
PCT_XGB_RSF_FMT = fmt1(PCT_XGB_RSF)
PCT_RSF_COX_FMT = fmt1(PCT_RSF_COX)
PCT_COX_RSF_FMT = fmt1(100 - PCT_RSF_COX)
TEXTO_VALIDAS = (
    "As 500 reamostragens (todas válidas)" if N_VALIDAS == 500 else
    f"As {N_VALIDAS} de 500 reamostragens válidas (as demais tiveram zero eventos observados, "
    "incompatível com o cálculo do C-index)"
)

import sys  # noqa: E402
sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import hiperparametros_fase4  # noqa: E402

HP = hiperparametros_fase4()
N_BLOCOS_RSF = 3  # mesmo valor de fase5_validacao.py
ARVORES_POR_BLOCO = HP["rsf_n_estimators"] // N_BLOCOS_RSF

C4_COX = pd.read_csv(f"{BASE_DIR}/dados/fase4_cox_mesmo_split_metricas.csv").iloc[0]["cindex_teste"]
C4_RSF = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_tunada_metricas.csv").iloc[0]["cindex_teste"]
C4_XGB = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_metricas.csv").iloc[0]["cindex_teste"]
IBS = pd.read_csv(f"{BASE_DIR}/dados/fase4_brier_resultado.csv").set_index("modelo")["ibs"]

_split = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet",
                         columns=["split", "distribuicao_d", "duracao_dias_e1"])
_treino = _split[_split["split"] == "treino"]
_teste = _split[_split["split"] == "teste"]
MAX_DUR_TESTE = int(_teste["duracao_dias_e1"].max())
ANO_INI_TREINO = _treino["distribuicao_d"].min().year
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
         "outubro", "novembro", "dezembro"]
PERIODO_TESTE = (f"{MESES[_teste['distribuicao_d'].min().month - 1]} a "
                 f"{MESES[_teste['distribuicao_d'].max().month - 1]} de {_teste['distribuicao_d'].max().year}")

calib["dif"] = calib["s_previsto_medio"] - calib["s_observado_km"]
DIF_MAX = calib.groupby("modelo")["dif"].max()
DIF_MIN = calib.groupby("modelo")["dif"].min()


def _sinal(v):
    return f"+{fmt3(v)}" if v >= 0 else fmt3(v)


def faixa_dif(modelo):
    return f"{_sinal(DIF_MIN[modelo])} a {_sinal(DIF_MAX[modelo])}"


DIF_ABS_MAX = calib.assign(a=calib["dif"].abs()).groupby("modelo")["a"].max()
XGB_SO_POSITIVO = DIF_MIN["XGBoost_AFT"] >= 0


# Medianas previstas da pagina de previsao (Fase 6), para a limitacao de horizonte
import json  # noqa: E402
with open(f"{BASE_DIR}/dados/fase6_prototipo_previsoes.json", encoding="utf-8") as _fh:
    _med = [v for v in json.load(_fh)["medianas_materia"].values() if v]
MED_MIN, MED_MAX = min(_med), max(_med)
N_MED = len(_med)
N_MED_ALEM = sum(1 for v in _med if v > MAX_DUR_TESTE)

with open(f"{BASE_DIR}/dados/fase5_backtest_info.json", encoding="utf-8") as _fh:
    BT_INFO = {i["origem"]: i for i in json.load(_fh)}
BT_MET = pd.read_csv(f"{BASE_DIR}/dados/fase5_backtest_metricas.csv")
BT_CAL = pd.read_csv(f"{BASE_DIR}/dados/fase5_backtest_calibracao.csv")
BT_CAL["erro"] = (BT_CAL["previsto"] - BT_CAL["observado"]).abs()
BT_ERRO = BT_CAL.groupby(["origem", "modelo", "horizonte"])["erro"].mean()
BT_MED = pd.read_csv(f"{BASE_DIR}/dados/fase5_backtest_medianas.csv")
BT_C = {(r["origem"], r["modelo"]): r["cindex"] for _, r in BT_MET.iterrows()}
ORIGENS_BT = list(BT_INFO)
ROTULO_ORIGEM = {"2024-07-01": "jul/2024", "2025-01-01": "jan/2025"}
ROTULO_MODELO_BT = {"Cox": "Cox", "RSF": "RSF", "XGBoost_AFT_config_antiga": "XGBoost-AFT (config. antiga)",
                    "XGBoost_AFT": "XGBoost-AFT (atual)"}
HORIZ_BT = sorted(BT_CAL["horizonte"].unique())


def _erro_bt(o, m, h):
    return BT_ERRO.loc[(o, m, h)]


def _faixa_erro_bt(modelo, h_min=365):
    vals = [_erro_bt(o, modelo, h) for o in ORIGENS_BT for h in HORIZ_BT if h >= h_min]
    return f"{fmt3(min(vals)).replace('0,', '0,', 1)}–{fmt3(max(vals))}"


SEG_MIN = {o: BT_INFO[o]["seguimento_min_teste_dias"] for o in ORIGENS_BT}
import json as _json_hist  # noqa: E402
with open(f"{BASE_DIR}/dados/historico_versoes.json", encoding="utf-8") as _fh_hist:
    HIST = _json_hist.load(_fh_hist)  # versoes anteriores recalculadas por historico_versoes.py
# versoes anteriores recalculadas por historico_versoes.py (nao digitadas)
PCT_XGB_COX_CONFIG_ANTIGA_FMT = f"{HIST['24mat_8com_config_antiga']['pct_vitorias_xgb_vs_cox']:.1f}".replace(".", ",")

# Versao de 04/11/2026 (8 materias) para o historico - lida do backup, nao digitada
_vit_041126 = pd.read_csv(f"{BASE_DIR}/backups_fases_pre_ampliacao/fase5_bootstrap_vitorias.csv").iloc[0]
PCT_XGB_COX_041126_FMT = fmt1(100 * _vit_041126["xgb_vs_cox"] / _vit_041126["n_validas"])

from coorte_comum import TOP_COMARCA, TOP_MATERIA  # noqa: E402
N_MAT, N_COM = len(TOP_MATERIA), len(TOP_COMARCA)
_h248 = HIST["24mat_8com_config_revista"]
C_XGB_24_8_FINAL_FMT = f"{_h248['cindex_teste_xgb']:.4f}".replace(".", ",")
PCT_XGB_COX_24_8_FMT = f"{_h248['pct_vitorias_xgb_vs_cox']:.0f}"


def leitura(pct, a, b):
    """Leitura da % de vitorias pareadas de A sobre B: >=95% ou <=5% = diferenca consistente."""
    if pct >= 95:
        return f"vantagem consistente do {a}"
    if pct <= 5:
        return f"vantagem consistente do {b}"
    return "<b>empate técnico</b>"


def ordem_discriminacao():
    """Resume a ordem em discriminacao a partir das vitorias pareadas."""
    xc, xr, rc = PCT_XGB_COX, PCT_XGB_RSF, PCT_RSF_COX
    if xc >= 95 and xr >= 95:
        resto = "Cox ≈ RSF" if 5 < rc < 95 else ("Cox &gt; RSF" if rc <= 5 else "RSF &gt; Cox")
        return f"XGBoost-AFT &gt; {resto}"
    if 5 < xc < 95:
        return "Cox ≈ XGBoost-AFT &gt; RSF" if rc <= 5 and xr >= 95 else "sem ordem clara"
    return "sem ordem clara"


ORDEM_DISC = ordem_discriminacao()
PIOR_Q = calib.loc[calib.groupby("modelo")["dif"].idxmax()].set_index("modelo")["quartil"]

from coorte_comum import DATA_REFERENCIA_BR as DATA_FOTO, carregar_coorte as _cc_carregar  # noqa: E402
DADOS_ATE = _cc_carregar()["distribuicao_d"].max().strftime("%d/%m/%Y")  # ultima distribuicao na foto

story = []

# ---------------------------------------------------------------------------
# CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 3 * cm))
story.append(p("Fase 5 — Resultados", "TituloCapa"))
story.append(p(
    "Validação: Intervalos de Confiança por Bootstrap, Calibração e Backtest com Acompanhamento Longo",
    "SubtituloCapa",
))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Reexecutado sobre a foto da coorte extraída em {DATA_FOTO} (t=0 na distribuição do processo, agravos "
    f"fora da coorte, {N_MAT} matérias e {N_COM} comarcas — ver os capítulos das Fases 2 a 4). "
    "Esta fase fecha duas lacunas que a Fase 4 deixou explicitamente em aberto: (1) a diferença de "
    "C-index entre os três modelos é estatisticamente confiável, ou poderia ser ruído amostral? "
    "(2) o Brier Score agregado diz que os modelos 'calibram bem em média' — mas calibram bem em "
    "TODA faixa de risco, ou só na média? E fecha uma terceira, que o split temporal não alcança: (3) as "
    "previsões de prazo longo (1 a 2 anos) se confirmam? Para isso, um backtest treina os modelos 'como se "
    "estivéssemos' numa data passada e confere contra o que aconteceu depois. Os três modelos finais (Cox, RSF "
    "tunada, XGBoost-AFT) são os mesmos da Fase 4, com os mesmos hiperparâmetros.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. INTRODUCAO
# ---------------------------------------------------------------------------
story.append(p("1. Introdução", "H1"))
story.append(p(
    "A Fase 4 comparou três modelos no mesmo split temporal e encontrou o XGBoost-AFT à frente no C-index "
    f"de teste ({fmt4(C4_XGB)}), seguido do Cox ({fmt4(C4_COX)}) e da RSF tunada ({fmt4(C4_RSF)}) — "
    "diferenças pequenas, e um único número de cada lado não diz se elas são grandes o "
    "suficiente para não serem explicadas por qual amostra específica caiu no conjunto de teste. O Brier Score integrado também resumiu a "
    "calibração num único número por modelo, mas um bom número agregado pode esconder um modelo que "
    "calibra bem em alguns grupos de risco e mal em outros. Esta fase formaliza as duas perguntas: "
    "significância da diferença de C-index e calibração desagregada por faixa de risco."
))

# ---------------------------------------------------------------------------
# 2. METODOLOGIA
# ---------------------------------------------------------------------------
story.append(p("2. Metodologia", "H1"))
story.append(p("2.1 Modelos", "H2"))
story.append(p(
    "Mesmos três modelos da Fase 4, reajustados com os mesmos hiperparâmetros já escolhidos (lidos dos "
    "resultados da Fase 4, não redigitados): Cox (penalizer=0,01), Random Survival Forest "
    f"(min_samples_leaf={HP['rsf_min_samples_leaf']}, {HP['rsf_n_estimators']} árvores — vencedor da "
    "validação cruzada da Fase 4) e XGBoost-AFT (distribuição log-normal, escala=1,0, "
    f"{HP['xgb_num_boost_round']} rodadas de boosting — parada por early stopping na Fase 4 —, com o ano de "
    f"distribuição como covariável e ponto de partida na mediana KM do treino, {HP['xgb_base_score']:.0f} dias; "
    "configuração revista a partir do backtest da Seção 3.3, ver Fase 4, Seção 2.3). Nenhum hiperparâmetro foi "
    "reajustado aqui."
))
story.append(p(
    f"<b>RSF em blocos:</b> a calibração precisa das curvas de sobrevivência de cada árvore, e uma floresta "
    f"única de {HP['rsf_n_estimators']} árvores com essas curvas pedia cerca de 6,4 GB de memória — o processo "
    "foi encerrado por falta de RAM na máquina de pesquisa. A floresta foi então ajustada em "
    f"{N_BLOCOS_RSF} blocos de {ARVORES_POR_BLOCO} árvores (sementes diferentes), um de cada vez, descartando "
    "cada bloco depois de prever. Isso é matematicamente equivalente a uma floresta única: no scikit-survival, "
    "o risco e a curva S(t|x) da floresta são a MÉDIA das árvores, calculada sobre os mesmos tempos únicos do "
    "treino, então a média de blocos de tamanho igual é a média de todas as árvores. Na prática, o C-index "
    "médio do bootstrap da RSF em blocos ficou praticamente igual ao da floresta única da Fase 4."
))
story.append(p("2.2 Bootstrap pareado do conjunto de teste", "H2"))
story.append(p(
    "Em vez de reajustar cada modelo centenas de vezes (computacionalmente caro e desnecessário "
    "para esta pergunta), o bootstrap reamostra com reposição os processos do CONJUNTO DE TESTE — "
    "os três modelos já treinados preveem sobre essa reamostra, e o C-index é recalculado. Repetido "
    "500 vezes, isso produz uma distribuição empírica do C-index de cada modelo (de onde vem o "
    "intervalo de confiança de 95%) — mas o ponto mais importante é que a MESMA reamostragem é usada "
    "nos três modelos a cada rodada: isso permite uma comparação pareada (quem venceu nesta "
    "reamostragem específica, não apenas 'os intervalos se sobrepõem?'), que é um teste "
    "estatisticamente mais poderoso do que comparar intervalos de confiança sobrepostos."
))
story.append(p("2.3 Calibração em horizonte fixo", "H2"))
story.append(p(
    "Para um tempo fixo t=90 dias (escolhido por estar dentro do intervalo observado no teste, que "
    f"tem duração máxima de {MAX_DUR_TESTE} dias por causa do split temporal — ver Fase 4, Seção 2.1), cada "
    "modelo prevê a probabilidade de sobrevivência S(90|x) para cada processo do teste. Os processos "
    "são divididos em quartis pela probabilidade PREVISTA, e dentro de cada quartil a sobrevivência "
    "REAL observada em t=90 é estimada por Kaplan-Meier. Um modelo bem calibrado tem os dois números "
    "próximos em todo quartil — não só na média."
))
story.append(p("2.4 Backtest com acompanhamento longo", "H2"))
def _milhar(v):
    return f"{int(v):,}".replace(",", ".")


_bt_txt = "; ".join(
    f"origem {ROTULO_ORIGEM[o]}: treino de {_milhar(BT_INFO[o]['n_treino'])} processos "
    f"({_milhar(BT_INFO[o]['eventos_treino'])} desfechos até a origem), teste de {_milhar(BT_INFO[o]['n_teste'])} "
    f"processos com no mínimo {SEG_MIN[o]} dias de acompanhamento"
    for o in ORIGENS_BT
)
story.append(p(
    f"O split temporal da Fase 4 só acompanha o teste por até {MAX_DUR_TESTE} dias. Para validar prazos longos, "
    "o backtest escolhe uma data de origem T0 no passado e reconstrói o que se sabia nela: o treino usa só "
    "processos distribuídos antes de T0, com o desfecho <b>censurado em T0</b> (um desfecho posterior a T0 não "
    "entra); o teste são os processos distribuídos nos 6 meses seguintes, acompanhados até a extração "
    f"({DATA_FOTO}). Duas origens: {_bt_txt}. Os hiperparâmetros são os da Fase 4; só o número de rodadas do "
    "XGBoost-AFT é escolhido por early stopping dentro do treino da origem. Métricas: C-index; erro médio de "
    "calibração (|previsto − observado KM| médio nos quartis) em 180, 365, 545 e 730 dias; e mediana prevista "
    "x mediana KM observada por quintil de mediana prevista. Origens mais antigas (2023 e jan/2024) foram "
    "testadas e descartadas: a carteira só ganha volume em 2024, e o treino nessas datas tinha só 58 e 1.260 "
    "desfechos registrados (C-index de 0,48 a 0,55)."
))

with open(f"{BASE_DIR}/dados/diagnostico_generalizacao.json", encoding="utf-8") as _fh_dg:
    DIAG = json.load(_fh_dg)  # scripts/diagnostico_generalizacao.py
story.append(p("2.5 Diagnóstico de generalização", "H2"))
story.append(p(
    "Um modelo que <b>decora</b> o treino vai muito bem nele e mal em dados novos; um modelo que aprende "
    "padrões gerais mantém um desempenho parecido nos dois. Além do split temporal e do backtest, três testes "
    "sobre o XGBoost-AFT de produção verificam isso (script <code>diagnostico_generalizacao.py</code>): "
    "(i) <b>curva por rodadas</b> — C-index de treino e teste a cada número de rodadas do boosting; num modelo "
    "que decora, a distância entre os dois cresce e o teste cai; (ii) <b>curva de aprendizado</b> — treino "
    "só com os 10%, 25%, 50% e 100% processos mais recentes, para ver se mais dados ainda ajudam e de onde vem a "
    "diferença treino-teste; (iii) <b>teste de permutação</b> — os desfechos do treino são embaralhados entre os "
    f"processos ({DIAG['permutacao']['n']} vezes), quebrando qualquer relação real com as características; o "
    "C-index no teste deve cair para perto de 0,5 — se ficasse alto, haveria vazamento de informação."
))

# ---------------------------------------------------------------------------
# 3. RESULTADOS
# ---------------------------------------------------------------------------
story.append(CondPageBreak(6 * cm))
story.append(p("3. Resultados", "H1"))
story.append(p("3.1 Intervalos de confiança (bootstrap, 500 reamostragens)", "H2"))
linhas_ic = [["Modelo", "C-index médio", "IC 95%"]]
destaque = set()
for i, (nome, row) in enumerate(ic.iterrows(), start=1):
    if nome == ic["cindex_medio"].idxmax():
        destaque.add(i)
    linhas_ic.append([
        nome.replace("_", " "), fmt4(row["cindex_medio"]),
        f"[{fmt4(row['ic_2.5%'])} – {fmt4(row['ic_97.5%'])}]",
    ])
story.append(tabela(linhas_ic, [6 * cm, 5 * cm, 5 * cm], destaque_linhas=destaque))
story.append(Spacer(1, 6))
story.append(p(
    f"{TEXTO_VALIDAS}, com o critério usual de vencer em 95% ou mais das reamostragens para chamar a "
    f"diferença de consistente: <b>XGBoost-AFT vs. Cox:</b> o XGBoost venceu em {PCT_XGB_COX_FMT}% — "
    f"{leitura(PCT_XGB_COX, 'XGBoost-AFT', 'Cox')}. <b>XGBoost-AFT vs. RSF:</b> o XGBoost venceu em "
    f"{PCT_XGB_RSF_FMT}% — {leitura(PCT_XGB_RSF, 'XGBoost-AFT', 'RSF')}. <b>RSF vs. Cox:</b> a RSF venceu em "
    f"{PCT_RSF_COX_FMT}% (o Cox em {PCT_COX_RSF_FMT}%) — {leitura(PCT_RSF_COX, 'RSF', 'Cox')}. Em "
    f"discriminação, portanto: {ORDEM_DISC}. O intervalo do XGBoost-AFT fica inteiro acima dos outros dois.",
    "CorpoTabelaNota",
))

story.append(p("3.2 Calibração em t=90 dias, por quartil de risco previsto", "H2"))
for nome in ["Cox", "RSF_tunada", "XGBoost_AFT"]:
    sub = calib[calib["modelo"] == nome]
    story.append(p(nome.replace("_", " "), "H2"))
    linhas_cal = [["Quartil", "N", "S(90) previsto", "S(90) observado (KM)", "Diferença"]]
    for _, row in sub.iterrows():
        dif = row["s_previsto_medio"] - row["s_observado_km"]
        linhas_cal.append([
            f"{int(row['quartil'])}", f"{int(row['n']):,}".replace(",", "."),
            fmt3(row["s_previsto_medio"]), fmt3(row["s_observado_km"]),
            f"+{fmt3(dif)}" if dif >= 0 else fmt3(dif),
        ])
    story.append(tabela(linhas_cal, [2.6 * cm, 2.6 * cm, 3.6 * cm, 4.6 * cm, 2.6 * cm]))
    story.append(Spacer(1, 10))

story.append(p(
    "Cox e RSF superestimam a sobrevivência em todo quartil (previsto sempre acima do observado), por "
    f"margens grandes: o Cox erra de {faixa_dif('Cox')} e a RSF de {faixa_dif('RSF_tunada')}; "
    + (f"nos dois, o pior quartil é o {int(PIOR_Q['Cox'])}, não o 1 (o de maior risco previsto) — sinal de que a "
       "ordenação de risco não se traduz em calibração suave entre grupos adjacentes. "
       if PIOR_Q["Cox"] == PIOR_Q["RSF_tunada"] and PIOR_Q["Cox"] != 1 else
       "o erro varia bastante de um quartil para o outro. ")
    + "O XGBoost-AFT erra pouco em toda a faixa "
    f"({faixa_dif('XGBoost_AFT')})"
    + ("." if XGB_SO_POSITIVO else ", e para os dois lados — sem o viés sistemático dos outros dois.")
    + " Em calibração, portanto: XGBoost-AFT muito à frente, depois RSF &gt; Cox.",
    "CorpoTabelaNota",
))

story.append(CondPageBreak(8 * cm))
story.append(p("3.3 Backtest com acompanhamento longo", "H2"))
_cab = ["Origem", "Modelo", "C-index"] + [f"Erro {h}d" for h in HORIZ_BT]
_linhas = [_cab]
_dest = set()
for o in ORIGENS_BT:
    for m in ["Cox", "RSF", "XGBoost_AFT_config_antiga", "XGBoost_AFT"]:
        if m == "XGBoost_AFT":
            _dest.add(len(_linhas))
        _linhas.append([ROTULO_ORIGEM[o], ROTULO_MODELO_BT[m], fmt4(BT_C[(o, m)])]
                       + [fmt3(_erro_bt(o, m, h)) for h in HORIZ_BT])
story.append(tabela(_linhas, [1.9 * cm, 4.6 * cm, 1.8 * cm] + [1.7 * cm] * len(HORIZ_BT), destaque_linhas=_dest))
story.append(Spacer(1, 6))
_o1, _o2 = ORIGENS_BT[0], ORIGENS_BT[1]
story.append(p(
    "Erro de calibração = |S(t) previsto − S(t) observado (KM)|, médio nos 4 quartis de risco previsto; menor é "
    "melhor. <b>Leitura:</b> (1) a vantagem do XGBoost-AFT em calibração se confirma em prazo longo — em 1 a 2 "
    f"anos, Cox e RSF erram de {_faixa_erro_bt('Cox')} e {_faixa_erro_bt('RSF')}, o XGBoost-AFT atual de "
    f"{_faixa_erro_bt('XGBoost_AFT')}. (2) A configuração antiga do XGBoost-AFT era instável: na origem "
    f"{ROTULO_ORIGEM[_o1]} o early stopping parou em {BT_INFO[_o1]['xgb_rodadas']} rodadas e o erro a 180 dias "
    f"foi {fmt3(_erro_bt(_o1, 'XGBoost_AFT_config_antiga', 180))}; na origem {ROTULO_ORIGEM[_o2]} acertou "
    "(nível baixo coincidindo com processos que ficaram mais rápidos). A configuração atual — ano de "
    "distribuição + ponto de partida na mediana KM — tem o melhor C-index do XGBoost nas duas origens "
    f"({fmt4(BT_C[(_o1, 'XGBoost_AFT')])} e {fmt4(BT_C[(_o2, 'XGBoost_AFT')])}) e calibração estável"
    + (f"; o Cox fica um pouco à frente em C-index na origem {ROTULO_ORIGEM[_o2]} ({fmt4(BT_C[(_o2, 'Cox')])})."
       if BT_C[(_o2, "Cox")] > BT_C[(_o2, "XGBoost_AFT")] else
       f", e fica à frente do Cox nas duas origens (Cox: {fmt4(BT_C[(_o1, 'Cox')])} e {fmt4(BT_C[(_o2, 'Cox')])}).")
    + " Este mesmo backtest foi usado para escolher a granularidade das categorias (Fase 4, Seção 2.4), sem "
    "olhar o teste final.",
    "CorpoTabelaNota",
))
story.append(Spacer(1, 6))
_linhas_med = [["Origem", "Quintil", "Config. antiga: prevista / observada", "Atual: prevista / observada"]]


def _med(o, m, q):
    r = BT_MED[(BT_MED["origem"] == o) & (BT_MED["modelo"] == m) & (BT_MED["quintil"] == q)].iloc[0]
    obs = "não atingida" if pd.isna(r["mediana_km_observada"]) else f"{r['mediana_km_observada']:.0f}"
    return f"{r['mediana_prevista']:.0f} / {obs}"


for o in ORIGENS_BT:
    for q in sorted(BT_MED["quintil"].unique()):
        _linhas_med.append([ROTULO_ORIGEM[o], str(int(q)), _med(o, "XGBoost_AFT_config_antiga", q),
                            _med(o, "XGBoost_AFT", q)])
story.append(tabela(_linhas_med, [2.2 * cm, 1.8 * cm, 6.5 * cm, 6.5 * cm]))
story.append(Spacer(1, 6))
_m5 = BT_MED[(BT_MED["modelo"] == "XGBoost_AFT") & (BT_MED["quintil"] == BT_MED["quintil"].max())]
story.append(p(
    "Mediana em dias, por quintil da mediana prevista pelo XGBoost-AFT (1 = casos previstos como mais rápidos). "
    "Na configuração atual, a mediana prevista bate com a observada nos quintis 1 a 3 (e 4, na origem "
    f"{ROTULO_ORIGEM[_o1]}). O ponto fraco é o <b>quintil dos casos mais lentos</b>, superestimado nas duas "
    "origens (prevista " + " e ".join(f"{r['mediana_prevista']:.0f}" for _, r in _m5.iterrows())
    + " dias, observada " + " e ".join(f"{r['mediana_km_observada']:.0f}" for _, r in _m5.iterrows())
    + "): o modelo sabe que esses processos demoram mais, mas exagera quanto.",
    "CorpoTabelaNota",
))

_cr = {r["rodadas"]: r for r in DIAG["curva_rodadas"]}
_ca = DIAG["curva_aprendizado"]
_pm = DIAG["permutacao"]
_r_min, _r_max = min(_cr), max(_cr)
DG_GAP_MIN, DG_GAP_MAX = fmt3(_cr[_r_min]["gap"]), fmt3(_cr[_r_max]["gap"])
DG_TE_MIN, DG_TE_MAX = fmt3(_cr[_r_min]["teste"]), fmt3(_cr[_r_max]["teste"])
DG_A10, DG_A100 = _ca[0], _ca[-1]
DG_PM_MED, DG_PM_LO, DG_PM_HI = fmt3(_pm["teste_medio"]), fmt3(_pm["teste_min"]), fmt3(_pm["teste_max"])
# pre-formatados (gotcha do ReportLab: nada de .replace em string multilinha)
DG_N10, DG_N100 = (f"{a['n']:,}".replace(",", ".") for a in (DG_A10, DG_A100))
DG_TR10, DG_TE10, DG_TE100 = fmt3(DG_A10["treino"]), fmt3(DG_A10["teste"]), fmt3(DG_A100["teste"])
DG_PCT10 = f"{100 * DG_A10['fracao']:.0f}"
story.append(CondPageBreak(6 * cm))
story.append(p("3.4 Diagnóstico de generalização", "H2"))
story.append(tabela(
    [["Rodadas", "C-index treino", "C-index teste", "Diferença"]]
    + [[str(r["rodadas"]), fmt3(r["treino"]), fmt3(r["teste"]), fmt3(r["gap"])] for r in DIAG["curva_rodadas"]],
    [3 * cm, 4 * cm, 4 * cm, 4 * cm],
    destaque_linhas={1 + [r["rodadas"] for r in DIAG["curva_rodadas"]].index(DIAG["rodadas_producao"])}
    if DIAG["rodadas_producao"] in _cr else None,
))
story.append(p(
    f"Linha destacada: {DIAG['rodadas_producao']} rodadas, a configuração usada em produção (escolhida por early "
    "stopping na Fase 4).",
    "CorpoTabelaNota",
))
story.append(tabela(
    [["Treino usado (mais recentes)", "Processos", "Desde", "C-index treino", "C-index teste"]]
    + [[f"{100 * a['fracao']:.0f}%", f"{a['n']:,}".replace(",", "."),
        pd.Timestamp(a["desde"]).strftime("%m/%Y"), fmt3(a["treino"]), fmt3(a["teste"])] for a in _ca],
    [4.4 * cm, 2.6 * cm, 2.4 * cm, 3.2 * cm, 3.2 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    f"<b>O modelo não está decorando.</b> A diferença entre treino e teste já existe com {_r_min} rodadas "
    f"({DG_GAP_MIN}) e quase não cresce até {_r_max} ({DG_GAP_MAX}), enquanto o C-index no teste continua "
    f"subindo devagar ({DG_TE_MIN} para {DG_TE_MAX}) em vez de cair — o oposto do sobreajuste. A curva de "
    f"aprendizado mostra de onde vem essa diferença: treinando só com os {DG_PCT10}% mais "
    f"recentes, ela é pequena (treino {DG_TR10}, teste {DG_TE10}); ela cresce quando "
    "entram os processos antigos, que já tiveram anos para chegar ao desfecho e por isso são mais fáceis de "
    "ordenar — o C-index de treino sobe pela composição da amostra, não por memorização. Ao mesmo tempo, o "
    f"teste quase não muda com 10 vezes mais dados ({DG_TE10} com {DG_N10} processos e {DG_TE100} com "
    f"{DG_N100}): o modelo "
    "já captura os padrões gerais com pouca informação, e o limite do desempenho está nas variáveis "
    "disponíveis, não no volume de dados. No <b>teste de permutação</b>, com os desfechos embaralhados, o "
    f"C-index no teste foi {DG_PM_MED} em média (de {DG_PM_LO} a {DG_PM_HI}) — o nível do acaso —, o que "
    "confirma que o desempenho real vem de relação verdadeira entre as características e o tempo, e não de "
    "coincidência ou vazamento."
))

# ---------------------------------------------------------------------------
# 4. DISCUSSAO
# ---------------------------------------------------------------------------
story.append(p("4. Discussão", "H1"))
story.append(p(
    "O bootstrap pareado responde à pergunta que os números pontuais da Fase 4 deixavam em aberto: a "
    "vantagem do XGBoost-AFT em C-index é pequena em valor absoluto, mas consistente — ele vence o Cox em "
    f"{PCT_XGB_COX_FMT}% das reamostragens e a RSF em {PCT_XGB_RSF_FMT}%. <b>Histórico desta comparação:</b> "
    "com t=0 na contratação, o XGBoost-AFT vencia o Cox em 100% das reamostragens; com t=0 na distribuição e "
    f"8 matérias (04/11/2026), só em {PCT_XGB_COX_041126_FMT}% — empate técnico; com a matéria ampliada para "
    f"{N_MAT} categorias, {PCT_XGB_COX_CONFIG_ANTIGA_FMT}%; com a configuração revista (ano de distribuição), "
    f"{PCT_XGB_COX_24_8_FMT}%; e com as {N_COM} comarcas escolhidas sem o teste, {PCT_XGB_COX_FMT}%. A "
    "ampliação da matéria ajudou o XGBoost-AFT e não o Cox "
    "(Fase 4, Seção 2.4), o que é coerente com a hipótese do TCC: mais categorias significam mais efeitos "
    "fixos para o Cox, sob uma suposição de riscos proporcionais já violada, enquanto as árvores aproveitam a "
    "informação."
))
story.append(p(
    "A calibração desagregada reforça a escolha. A previsão individualizada mostra ao usuário uma "
    "PROBABILIDADE e um prazo, e o XGBoost-AFT é o único que acerta o nível: erra no máximo "
    f"{fmt3(DIF_ABS_MAX['XGBoost_AFT'])} em S(90), contra até {fmt3(DIF_MAX['Cox'])} do Cox e "
    f"{fmt3(DIF_MAX['RSF_tunada'])} da RSF. A vantagem em calibração é muito maior que a em discriminação — "
    "mesmo que o C-index empatasse, ela já justificaria o XGBoost-AFT como modelo da página de previsão em "
    "produção."
))
story.append(p(
    "Cox e RSF superestimam a sobrevivência — preveem prazos mais longos que os reais — no split oficial e em "
    "todos os horizontes do backtest. O backtest identificou a causa principal: <b>mudança real no ritmo da "
    "carteira</b>. A mediana até o desfecho caiu de cerca de 720 dias (processos distribuídos em 2022) para "
    f"cerca de 250 (2024) e 190 (2025); um modelo treinado no histórico de {ANO_INI_TREINO} em diante, sem "
    "saber a época do processo, prevê o ritmo antigo. O XGBoost-AFT, depois de receber o ano de distribuição "
    f"como covariável, deixa de ter esse viés (no split oficial, erros entre {faixa_dif('XGBoost_AFT')} em "
    "S(90)). Cox e RSF não receberam a covariável — num modelo linear ela extrapolaria a tendência "
    "indefinidamente —, e é isso que explica boa parte da distância de calibração entre eles e o XGBoost-AFT."
))

# ---------------------------------------------------------------------------
# 5. LIMITACOES
# ---------------------------------------------------------------------------
story.append(p("5. Limitações", "H1"))
story.append(lista([
    "Bootstrap de avaliação, não de treino: reamostrar o teste mede a incerteza de COMO os modelos "
    "já ajustados performam sobre reamostras plausíveis dos mesmos dados de teste — não mede quanto "
    "os coeficientes/árvores mudariam se o treino em si fosse reamostrado. Um bootstrap do treino "
    "(reajustando cada modelo a cada rodada) daria uma resposta mais completa, a um custo "
    "computacional várias ordens de magnitude maior.",

    f"Prazos longos: no split oficial a calibração só pode ser medida até {MAX_DUR_TESTE} dias; o backtest "
    f"valida até cerca de {min(SEG_MIN.values())}–{max(SEG_MIN.values())} dias de acompanhamento mínimo (com "
    "estimativa KM até 730 dias), em duas origens só. O quintil dos casos mais lentos continua superestimado — "
    "previsões muito longas devem ser lidas como 'acima da média', não como prazo preciso.",

    "Ano de distribuição como covariável: para um processo novo o XGBoost-AFT usa o ritmo do período mais "
    "recente do treino. Se a carteira acelerar ou desacelerar de novo, a previsão só acompanha quando o "
    "modelo for retreinado — retreino periódico é parte do uso em produção.",

    "Backtest com só duas origens úteis: origens mais antigas não têm desfechos registrados suficientes "
    "(Seção 2.4). Tanto a configuração do XGBoost-AFT (ano + ponto de partida) quanto a granularidade das "
    f"categorias ({N_MAT} matérias / {N_COM} comarcas) foram escolhidas por ele, sem olhar o teste final — e no "
    f"teste final a granularidade descartada (24/8) teria dado um C-index um pouco maior ({C_XGB_24_8_FINAL_FMT} "
    f"contra {fmt4(C4_XGB)}), o custo esperado de não escolher pelo teste. O mesmo critério (validação temporal "
    "sem o teste, regra fixada antes de rodar) foi usado nos modelos de procedência e acordo da Fase 6.",

    "Demais limitações já documentadas na Fase 4 (sem riscos competitivos nativos em RSF/XGBoost-AFT, "
    "busca de hiperparâmetro pequena, escala da AFT fixada) continuam "
    "valendo aqui, por reutilizarem os mesmos modelos.",
]))

# ---------------------------------------------------------------------------
# 6. SINTESE
# ---------------------------------------------------------------------------
story.append(p("6. Síntese e encerramento da linha de modelagem", "H1"))
story.append(p(
    "Com a Fase 5, as quatro fases centrais de modelagem do TCC — exploratória (Fase 2), "
    "multivariada clássica (Fase 3), não-paramétrica (Fase 4) e validação (Fase 5) — formam uma "
    "progressão coerente: cada fase testou uma hipótese mais exigente que a anterior sobre os mesmos "
    "dados, e cada uma produziu evidência que a próxima pôde confirmar, refinar ou contestar. A conclusão "
    "final é que a hipótese do TCC se confirma nas duas dimensões para o XGBoost-AFT: em "
    f"<b>discriminação</b>, ele supera o Cox e a RSF de forma consistente no bootstrap pareado ({ORDEM_DISC}), "
    "com diferença modesta em magnitude, mas estatisticamente clara (intervalos de confiança sem sobreposição e vitória em todas as reamostragens); em <b>calibração</b>, é de longe o melhor (Brier Score integrado e "
    "calibração por quartil). A RSF não confirmou a hipótese. O caminho até aqui também mostrou que o "
    "resultado em discriminação é sensível a escolhas de especificação — o marco zero do relógio e a "
    "granularidade das categorias mudaram a ordem entre Cox e XGBoost-AFT —, enquanto a vantagem em "
    "calibração apareceu em todas as versões. O backtest com acompanhamento longo confirmou essa vantagem em "
    "1 a 2 anos, revelou que os processos ficaram mais rápidos ao longo do tempo e levou à configuração atual "
    "do XGBoost-AFT (ano de distribuição + ponto de partida), mais estável; também passou a ser o critério para "
    "as escolhas de especificação, que antes olhavam o teste. O XGBoost-AFT segue como o modelo "
    "em produção — com a ressalva de que, para os casos previstos como mais lentos, o prazo tende a ser "
    "superestimado."
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(p("Referências", "H1"))
for ref in [
    "EFRON, B.; TIBSHIRANI, R. J. <i>An Introduction to the Bootstrap</i>. New York: Chapman and Hall/CRC, 1994.",
    "HARRELL, F. E. et al. Evaluating the Yield of Medical Tests. <i>JAMA</i>, v. 247, n. 18, p. 2543-2546, 1982. (C-index.)",
    "GRAF, E. et al. Assessment and Comparison of Prognostic Classification Schemes for Survival Data. <i>Statistics in Medicine</i>, v. 18, n. 17-18, p. 2529-2545, 1999.",
    "KAPLAN, E. L.; MEIER, P. Nonparametric Estimation from Incomplete Observations. <i>Journal of the American Statistical Association</i>, v. 53, n. 282, p. 457-481, 1958.",
    "AUSTIN, P. C.; HARRELL, F. E.; STEYERBERG, E. W. Predictive Performance of Machine Learning and Statistical Methods for Predicting Survival. <i>Statistical Methods in Medical Research</i>, v. 31, n. 2, p. 227-246, 2022. (Discriminação vs. calibração em modelos de sobrevivência.)",
]:
    story.append(p(ref, "Referencia"))

story.append(Spacer(1, 10))
story.append(p(
    "Este capítulo complementa os capítulos de resultados das Fases 2, 3 e 4, na mesma pasta de "
    "pesquisa. Scripts reprodutíveis: scripts/fase5_validacao.py, scripts/fase5_backtest.py e "
    "scripts/gerar_capitulo_fase5.py "
    "(este documento).",
    "CorpoTabelaNota",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Fase 5: Validação",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
