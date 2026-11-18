# -*- coding: utf-8 -*-
"""
Gera Capitulo_Fase6_Resultados.pdf (previsao individualizada: prazo, procedencia 1G/2G e
acordos pre/pos-sentenca) - mesmo padrao visual dos capitulos anteriores.

Fontes (nada digitado): dados/fase6_prototipo_previsoes.json, fase6_procedencia.json,
fase6_procedencia_2g.json, fase6_acordos.json, fase6_selecao_temporal.json/.csv,
historico_versoes.json, a foto congelada (coorte_comum) e o JSON exportado para a pagina
(api_dashboards/.../tcc_previsao_individual.json), lido so para os exemplos de saida.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_fase6.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import contextlib
import io
import json
import sys

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    CondPageBreak,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from scipy.stats import norm

BASE_DIR = ML_DIR
OUT_PDF = f"{BASE_DIR}/Capitulo_Fase6_Resultados.pdf"
BUNDLE_API = (REPO_DIR + "/apps/api/src/app/analyses/GERAL/data/tcc_previsao_individual.json")
sys.path.insert(0, f"{BASE_DIR}/scripts")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=20, leading=25, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle(name="SubtituloCapa", fontSize=13, leading=17, fontName="Helvetica", spaceAfter=14, textColor=colors.HexColor("#333333")))
styles.add(ParagraphStyle(name="AutorData", fontSize=10.5, leading=14, fontName="Helvetica"))
styles.add(ParagraphStyle(name="NotaRodapeCapa", fontSize=9, leading=13, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceBefore=18))
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=18, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8, keepWithNext=1))
styles.add(ParagraphStyle(name="H2", fontSize=11.5, leading=15, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6, keepWithNext=1))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=14.5, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="CorpoTabela", fontSize=8.8, leading=11.5, fontName="Helvetica"))
styles.add(ParagraphStyle(name="CabecalhoTabela", fontSize=8.8, leading=11.5, fontName="Helvetica-Bold", textColor=colors.white))
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
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Fase 6: Previsão Individualizada")
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
    data = [[Paragraph(str(c), styles["CabecalhoTabela"] if (header and i == 0) else styles["CorpoTabela"])
             for c in linha] for i, linha in enumerate(linhas)]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO)]
    for i in range(1 if header else 0, len(data)):
        if i in destaque_linhas:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_DESTAQUE_LINHA))
        elif (i - (1 if header else 0)) % 2 == 1:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_ALT))
    t.setStyle(TableStyle(estilo))
    return t


def fmt(v, casas=3):
    return f"{v:.{casas}f}".replace(".", ",")


def pct(v, casas=1):
    return f"{100 * v:.{casas}f}".replace(".", ",") + "%"


def milhar(v):
    return f"{int(v):,}".replace(",", ".")


def ler(nome):
    with open(f"{BASE_DIR}/dados/{nome}", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------
PROTO = ler("fase6_prototipo_previsoes.json")
PROC = ler("fase6_procedencia.json")
PROC2 = ler("fase6_procedencia_2g.json")
ACO = ler("fase6_acordos.json")
SEL = ler("fase6_selecao_temporal.json")
HIST = ler("historico_versoes.json")
SEL_CSV = pd.read_csv(f"{BASE_DIR}/dados/fase6_selecao_temporal.csv")
with open(BUNDLE_API, encoding="utf-8") as _fh:
    API = json.load(_fh)

from coorte_comum import TOP_COMARCA, TOP_MATERIA, carregar_coorte  # noqa: E402
from fase6_prototipo_dados import FAIXAS  # noqa: E402
import fase6_acordos  # noqa: E402

COORTE = carregar_coorte()
N_COORTE_FMT = milhar(len(COORTE))
N_TREINO_FMT = milhar(PROTO["n_treino"])
N_COMB_FMT = milhar(len(PROTO["previsoes"]))
N_MAT, N_COM = len(TOP_MATERIA), len(TOP_COMARCA)
N_MAT_REAIS, N_COM_REAIS = len(PROTO["categorias_reais"]["materia"]), len(PROTO["categorias_reais"]["comarca"])
N_COMP_REAIS = len(PROTO["categorias_reais"]["competencia"])
FAIXAS_TXT = ", ".join(FAIXAS[:-1]) + " e " + FAIXAS[-1]
MODELO_TXT = PROTO["modelo"]
DATA_GERACAO = pd.Timestamp(PROTO["gerado_em"]).strftime("%d/%m/%Y")

COB = HIST["cobertura_faixas_backtest"]
COB50 = [v["faixa_50"] for v in COB.values()]
COB80 = [v["faixa_80"] for v in COB.values()]
COB50_FMT = f"{pct(min(COB50), 0)} a {pct(max(COB50), 0)}"
COB80_FMT = f"{pct(min(COB80), 0)} a {pct(max(COB80), 0)}"

# Procedencia 1G (teste = split temporal da Fase 4)
M1 = PROC["metricas"]["1G"]
# Primeira tentativa do 2G (split por distribuicao) - registrada no mesmo arquivo
M2_V1 = PROC["metricas"]["2G"]
# 2G atual (teste pela data do acordao, com resultado do 1G)
M2 = PROC2["metricas"]["com_resultado_1g"]
M2_SEM = PROC2["metricas"]["sem_resultado_1g"]
MOD2 = PROC2["modelo_final"]
FRAC_EXT_FMT = pct(API["fracao_extinto_1g_desfavoravel"], 0)
MPRE, MPOS = ACO["metricas"]["pre"], ACO["metricas"]["pos"]
DEC = SEL["classificadores"]

# Contagem de acordos e conferencia das etiquetas (mesma regra do fase6_acordos.preparar)
with contextlib.redirect_stdout(io.StringIO()) as _buf:
    POP_PRE, POP_POS = fase6_acordos.preparar()
_log = _buf.getvalue()
N_POP_PRE, N_POP_POS = len(POP_PRE), len(POP_POS)
N_AC_PRE, N_AC_POS = int(POP_PRE["y"].sum()), int(POP_POS["y"].sum())
# pico trimestral da taxa de acordo pre-sentenca (trimestres com >= 500 resolucoes) - calculado
_tri = POP_PRE.assign(_t=pd.to_datetime(POP_PRE["data_resolucao"]).dt.to_period("Q")).groupby("_t")["y"].agg(["size", "mean"])
_tri = _tri[_tri["size"] >= 500]
PICO_PRE_FMT = f"{100 * _tri['mean'].max():.0f}%"
_q = _tri["mean"].idxmax()
PICO_PRE_QUANDO = f"{_q.quarter}º trimestre de {_q.year}"
_d = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
from coorte_comum import carregar_datas_merito  # noqa: E402
_d = _d.merge(carregar_datas_merito(), on="id", how="left")
for _c in ("sentenca_d", "acordao_d", "acordo_d"):
    _d[_c] = pd.to_datetime(_d[_c])
    _d.loc[_d[_c] > fase6_acordos.DATA_REFERENCIA, _c] = pd.NaT  # mesma regra do preparar()
_ac = _d["acordo_d"].notna()
_antes_acordao = _d["acordao_d"].isna() | (_d["acordo_d"] <= _d["acordao_d"])
_pos_data = _ac & _d["sentenca_d"].notna() & (_d["acordo_d"] > _d["sentenca_d"]) & _antes_acordao
_et = _d["etiqueta_acordo"]
_pos_nome = _ac & (_et == "POS")
N_ET_POS = int(_pos_nome.sum())
N_ET_POS_DISC = int((_pos_nome & ~_pos_data).sum())
N_AC_TOTAL = int((_ac | _et.notna()).sum())
N_SO_ETIQUETA = int((_et.notna() & ~_ac).sum())
PCT_AC_TOTAL_FMT = pct(N_AC_TOTAL / len(_d), 1)

# Selecao temporal: medias por populacao (logistica x XGBoost x taxa base)
_cls = SEL_CSV[SEL_CSV["parte"] == "classificador"].groupby("populacao").mean(numeric_only=True)
ROTULO_POP = {"procedencia_1g": "Procedência 1G", "procedencia_2g": "Procedência 2G",
              "acordo_pre": "Acordo pré-sentença", "acordo_pos": "Acordo pós-sentença"}
ROTULO_MOD = {"xgboost": "XGBoost", "logistica": "Logística"}
ROTULO_EXIB = {"previsao": "previsão", "relativo": "relativo", "historico": "histórico"}

# Fatores (gain do XGBoost-AFT, agregado por grupo)
FATORES = PROTO["fatores"]


# ---------------------------------------------------------------------------
# Exemplos de saida - MESMA logica da pagina (mistura ponderada pelos 6 filtros)
# ---------------------------------------------------------------------------
def perfil(filtro):
    g = API["grupo_modelo"]
    comps = []
    for chave, n in API["pesos_treino"].items():
        m, c, k, t, e, fx = chave.split("|")
        if not filtro(m, c, k, t, e, fx):
            continue
        v = API["previsoes"]["|".join([t, g["materia"].get(m, m), g["comarca"].get(c, c),
                                       g["competencia"].get(k, k), e, fx])]
        comps.append((v, n))
    total = sum(n for _, n in comps)
    w = np.array([n / total for _, n in comps])
    v = np.array([x for x, _ in comps], dtype=float)
    dias = v[:, 0]

    def S(t):
        return float(np.sum(w * (1 - norm.cdf(np.log(t / dias)))))

    def quantil(s_alvo):
        lo, hi = 0.0, np.log(100000)
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if S(np.exp(mid)) > s_alvo else (lo, mid)
        return round(np.exp((lo + hi) / 2))

    p1 = float(w @ v[:, 1]) / 1000
    f = API["fracao_extinto_1g_desfavoravel"]

    def comb(i0):
        fav, imp, ext = (float(w @ v[:, i0 + j]) / 1000 for j in range(3))
        return p1 * fav + (1 - p1) * (f * ext + (1 - f) * imp), fav, imp

    p2, p2_fav, p2_imp = comb(2)
    ac_pos, _, _ = comb(5)
    ac_pre = float(w @ v[:, 8]) / 10000
    return {"base": total, "mediana": quantil(0.5), "p25": quantil(0.75), "p75": quantil(0.25),
            "p1": p1, "p2": p2, "p2_fav": p2_fav, "p2_imp": p2_imp, "ac_pre": ac_pre, "ac_pos": ac_pos}


PERFIS = [
    ("Todos (sem filtro)", lambda *a: True),
    ("NG", lambda m, c, k, t, e, fx: e == "NG"),
    ("LA", lambda m, c, k, t, e, fx: e == "LA"),
    ("NG · ESPECIFICA · Manaus · Indenizatória",
     lambda m, c, k, t, e, fx: e == "NG" and m == "ESPECIFICA" and c == "MANAUS" and t == "INDENIZATÓRIA"),
    ("Tabatinga (comarca nova)", lambda m, c, k, t, e, fx: c == "TABATINGA"),
]
EXEMPLOS = [(rot, perfil(f)) for rot, f in PERFIS]
EX = dict(EXEMPLOS)
EX_ESP = EX["NG · ESPECIFICA · Manaus · Indenizatória"]

# pre-formatados (gotcha do ReportLab)
M1_AUC, M1_AUC_LOG = fmt(M1["auc_xgb"], 3), fmt(M1["auc_logistica"], 3)
M1_BR, M1_BR_BASE = fmt(M1["brier_xgb"], 3), fmt(M1["brier_taxa_base"], 3)
M1_TX_TR, M1_TX_TE = pct(M1["taxa_treino"], 0), pct(M1["taxa_teste"], 0)
M2V1_AUC, M2V1_N = fmt(M2_V1["auc_xgb"], 2), milhar(M2_V1["n_teste"])
M2_AUC_XGB, M2_AUC_LOG = fmt(M2["auc_xgb"], 3), fmt(M2["auc_logistica"], 3)
M2_BR_XGB, M2_BR_LOG, M2_BR_BASE = fmt(M2["brier_xgb"], 3), fmt(M2["brier_logistica"], 3), fmt(M2["brier_taxa_base"], 3)
M2SEM_AUC_LOG = fmt(M2_SEM["auc_logistica"], 2)
M2_NT, M2_N = milhar(PROC2["n_teste"]), milhar(PROC2["n_acordaos"])
M2_DE = pd.Timestamp(PROC2["teste_de"]).strftime("%d/%m/%Y")
M2_ATE = pd.Timestamp(PROC2["teste_ate"]).strftime("%d/%m/%Y")
AUC_DEC_2G = fmt(DEC["procedencia_2g"]["auc_medio"], 2)
PRE_AUC, PRE_BR, PRE_BR_BASE = fmt(MPRE["auc_xgb"], 3), fmt(MPRE["brier_xgb"], 4), fmt(MPRE["brier_taxa_base"], 4)
PRE_TX_TR, PRE_TX_TE = pct(MPRE["taxa_treino"], 1), pct(MPRE["taxa_teste"], 1)
PRE_EV_TE = MPRE["eventos_teste"]
POS_AUC, POS_BR, POS_BR_BASE = fmt(MPOS["auc_logistica"], 3), fmt(MPOS["brier_logistica"], 3), fmt(MPOS["brier_taxa_base"], 3)
POS_EV_TE = MPOS["eventos_teste"]
REF = ACO["referencia_pre"]
REF_NG, REF_LA = pct(REF["NG"]["taxa_observada_12m"], 1), pct(REF["LA"]["taxa_observada_12m"], 1)
FAT_TXT = "; ".join(f"{x['nome']} {fmt(x['pct'], 1)}%" for x in FATORES)
ESP_FMT = (f"{EX_ESP['mediana']} dias (metade entre {EX_ESP['p25']} e {EX_ESP['p75']}), procedência 1G de "
           f"{pct(EX_ESP['p1'], 0)}, 2G de {pct(EX_ESP['p2'], 0)} ({pct(EX_ESP['p2_fav'], 0)} se o 1G for procedente, "
           f"{pct(EX_ESP['p2_imp'], 0)} se improcedente)")
DISC_PCT = pct(N_ET_POS_DISC / N_ET_POS, 0) if N_ET_POS else "—"

story = []

# ---------------------------------------------------------------------------
# CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 3 * cm))
story.append(p("Fase 6 — Resultados", "TituloCapa"))
story.append(p("Previsão Individualizada: prazo, procedência e acordos", "SubtituloCapa"))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Sobre a mesma foto da coorte das Fases 2 a 5 ({N_COORTE_FMT} processos dos escritórios NG e LA/AM, t=0 "
    f"na distribuição, {N_MAT} matérias e {N_COM} comarcas como categorias próprias). Esta fase transforma os "
    "modelos validados em uma ferramenta de consulta — a página \"Previsão Individualizada\" do LexHub — e "
    "acrescenta três perguntas que a análise de sobrevivência sozinha não responde: a chance de procedência no "
    "1º e no 2º grau e a chance de acordo antes e depois da sentença. Todas as escolhas de modelo desta fase "
    "foram feitas sem olhar o conjunto de teste final.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. INTRODUCAO
# ---------------------------------------------------------------------------
story.append(p("1. Introdução", "H1"))
story.append(p(
    "As Fases 4 e 5 mostraram que o XGBoost-AFT discrimina e, sobretudo, calibra melhor que o Cox e a Random "
    "Survival Forest, inclusive em prazos de 1 a 2 anos (backtest). O passo natural é usar esse modelo para "
    "responder a uma pergunta prática do escritório: <i>para um processo novo, com estas características, "
    "quanto tempo até o desfecho?</i> Na prática, quem consulta também quer saber <i>como</i> o processo tende "
    "a terminar — a chance de a sentença e o acórdão serem favoráveis e a chance de um acordo antes ou depois "
    "da sentença. Esta fase descreve como essas quatro estimativas foram construídas, validadas e expostas na "
    "página, e onde elas devem ser lidas com cautela."
))
story.append(p(
    "A ferramenta generaliza padrões de processos passados com as mesmas características (matéria, comarca, "
    "competência, tipo de ação, escritório e faixa de valor de causa). Ela <b>não</b> analisa o mérito de um "
    "caso específico — provas, tese, partes — e não substitui a avaliação jurídica.",
    "Destaque",
))

# ---------------------------------------------------------------------------
# 2. METODOLOGIA
# ---------------------------------------------------------------------------
story.append(p("2. Metodologia", "H1"))
story.append(p("2.1 Prazo até o desfecho", "H2"))
story.append(p(
    f"O modelo de prazo é o XGBoost-AFT validado nas Fases 4 e 5 — {MODELO_TXT} —, reajustado no conjunto de "
    f"treino ({N_TREINO_FMT} processos). Como ele usa o ano de distribuição como covariável (os processos "
    "ficaram mais rápidos ao longo do tempo), um processo novo recebe a data de referência da extração: a "
    "previsão segue o ritmo mais recente que o modelo viu. Para não executar o modelo dentro do navegador, as "
    f"previsões foram pré-calculadas para todas as {N_COMB_FMT} combinações do formulário (scripts "
    "<code>fase6_prototipo_dados.py</code> e <code>fase6_grade.py</code>)."
))
story.append(lista([
    f"<b>Faixas de valor de causa:</b> {FAIXAS_TXT}. Cada faixa é representada por 5 pontos da distribuição real "
    "de valores do treino dentro dela (percentis 10, 30, 50, 70 e 90), e as probabilidades são a média nesses "
    "pontos. Um valor único (a mediana da faixa) caía num pico local de acordos e distorcia a faixa inteira.",
    f"<b>Categorias reais × categorias do modelo:</b> o formulário oferece todas as categorias existentes "
    f"({N_MAT_REAIS} matérias, {N_COM_REAIS} comarcas, {N_COMP_REAIS} competências), mas o modelo só distingue "
    "as mais frequentes; as demais usam a previsão do grupo \"Outros\". O peso de cada combinação e a base "
    "exibida usam a categoria real.",
    "<b>Várias opções marcadas:</b> a previsão é uma <b>mistura de log-normais</b> — uma componente por "
    "combinação selecionada, ponderada pelo número de processos de treino com os mesmos seis filtros. A mediana "
    "é o tempo em que a sobrevivência da mistura cai a 50%. Se nenhum processo do histórico tem a combinação, a "
    "página não mostra previsão (antes ela extrapolava).",
    "<b>Faixa de incerteza:</b> a página mostra também onde caem os 50% centrais dos casos (do 25º ao 75º "
    f"percentil da mistura). No backtest da Fase 5, essa faixa conteve {COB50_FMT} dos processos reais, e a de "
    f"80% conteve {COB80_FMT}: a faixa é honesta e um pouco mais larga do que precisaria.",
]))

story.append(p("2.2 Procedência no 1º e no 2º grau", "H2"))
story.append(p(
    "As duas probabilidades são <b>condicionais</b>: a chance de a decisão ser favorável <i>dado que</i> haja "
    "sentença (ou acórdão) de mérito. Favorável segue o critério de toda a coorte — procedente ou parcialmente "
    "procedente <i>com proveito econômico</i> (códigos 1 e 3 dos catálogos do LexFlow); no 2º grau, a "
    "\"sentença anulada\" fica fora da conta, porque não é decisão de mérito."
))
story.append(lista([
    f"<b>1G</b> (<code>fase6_procedencia.py</code>): classificador XGBoost com as mesmas covariáveis e o mesmo "
    f"split temporal da Fase 4 ({milhar(M1['n_treino'])} sentenças de mérito no treino, "
    f"{milhar(M1['n_teste'])} no teste).",
    "<b>2G</b> (<code>fase6_procedencia_2g.py</code>): o resultado do 1G entra como covariável e vira "
    "<b>cenário</b> na página (procedente, improcedente ou extinto). Sem resultado informado, a chance combina "
    "os cenários pela procedência 1G prevista e pela fração histórica de extinções entre os 1G desfavoráveis "
    f"({FRAC_EXT_FMT}).",
]))
story.append(p(
    f"<b>Um achado metodológico no 2G.</b> A primeira validação usou o mesmo split da Fase 4 (por data de "
    f"distribuição) e deu AUC {M2V1_AUC} — pior que o acaso. O teste, porém, só tinha {M2V1_N} acórdãos: "
    "processos distribuídos nos últimos meses que <i>já</i> tinham acórdão, ou seja, os excepcionalmente "
    f"rápidos. Separando treino e teste pela <b>data do acórdão</b> ({M2_N} acórdãos de mérito; teste com os "
    f"{M2_NT} mais recentes, de {M2_DE} a {M2_ATE}) e incluindo o resultado do 1G, o modelo passou a ser útil. "
    f"Sem o resultado do 1G a AUC fica em {M2SEM_AUC_LOG}: é essa variável que carrega a maior parte do sinal."
))

story.append(p("2.3 Acordos antes e depois da sentença", "H2"))
story.append(p(
    "A fonte é o campo \"acordo fechado\" do LexFlow ou a etiqueta de acordo do processo. Nos processos que só "
    "têm etiqueta, a fase vem do nome da etiqueta (quando diz pré ou pós-sentença) ou da situação do processo. "
    "<b>Pré-sentença</b> é o acordo antes de qualquer sentença; <b>pós-sentença</b>, entre a sentença e o "
    "acórdão, com o processo já em 2º grau. Acordos depois do acórdão (fase de execução) ficam fora. Como na "
    "procedência, as probabilidades são condicionais: entre os casos que se resolveram naquela etapa, a chance "
    "de ter sido por acordo. O pós-sentença usa o resultado do 1G como cenário."
))
story.append(p(
    f"Acordo é evento raro na base: {milhar(N_AC_TOTAL)} processos com acordo ({PCT_AC_TOTAL_FMT} da coorte de "
    f"modelagem; {milhar(N_SO_ETIQUETA)} deles só pela etiqueta). Entram nos modelos {milhar(N_AC_PRE)} acordos "
    f"pré-sentença, entre {milhar(N_POP_PRE)} processos resolvidos no 1G, e {milhar(N_AC_POS)} pós-sentença, entre "
    f"{milhar(N_POP_POS)} resolvidos depois da sentença."
))

story.append(CondPageBreak(7 * cm))
story.append(p("2.4 Seleção de modelos sem o teste final", "H2"))
story.append(p(
    "Nas primeiras versões, o modelo de cada probabilidade (regressão logística ou XGBoost) e a forma de exibi-la "
    "na página foram escolhidos pelo desempenho no conjunto de teste — o que tira do teste o papel de avaliação "
    "independente. A escolha foi refeita por <b>validação temporal</b> dentro dos 80% mais antigos de cada "
    "população: três dobras com janela expansiva (treino nos primeiros 50%, 60% e 70%; validação nos 10% "
    "seguintes), com uma regra fixada <b>antes</b> de rodar (<code>fase6_selecao_temporal.py</code>): vence o "
    "modelo de menor Brier médio; a página mostra a <b>previsão</b> se ele bater a taxa base, senão a previsão "
    "<b>relativa</b> se a AUC média for de pelo menos 0,60, senão o <b>histórico</b>."
))
_linhas = [["População", "AUC log. / XGB", "Brier log. / XGB / taxa base", "Modelo", "Exibição"]]
for k in ("procedencia_1g", "procedencia_2g", "acordo_pre", "acordo_pos"):
    r = _cls.loc[k]
    _linhas.append([
        ROTULO_POP[k], f"{fmt(r['auc_logistica'], 3)} / {fmt(r['auc_xgboost'], 3)}",
        f"{fmt(r['brier_logistica'], 4)} / {fmt(r['brier_xgboost'], 4)} / {fmt(r['brier_taxa_base'], 4)}",
        ROTULO_MOD[DEC[k]["modelo"]], ROTULO_EXIB[DEC[k]["exibir"]],
    ])
story.append(tabela(_linhas, [3.6 * cm, 2.9 * cm, 5 * cm, 2.3 * cm, 2.2 * cm]))
story.append(p(
    "Médias das três dobras de validação temporal (sem o teste final). Brier: menor é melhor.",
    "CorpoTabelaNota",
))
story.append(p(
    "Duas decisões mudaram em relação às escolhas feitas olhando o teste: a procedência 2G passou de regressão "
    f"logística para XGBoost (AUC média {AUC_DEC_2G} na validação), e o acordo pré-sentença deixou de ser "
    "mostrado de forma relativa (\"× a média do escritório\") e passou a percentual previsto. A mesma regra "
    "também decidiu a granularidade das categorias, descrita no capítulo da Fase 4."
))

# ---------------------------------------------------------------------------
# 3. RESULTADOS
# ---------------------------------------------------------------------------
story.append(p("3. Resultados", "H1"))
story.append(p("3.1 Desempenho no teste final", "H2"))
story.append(p(
    "O teste final só foi olhado depois das escolhas. A tabela compara cada modelo com a <b>taxa base</b> — "
    "prever para todo processo a taxa média do treino. Superar a taxa base no Brier significa que a "
    "probabilidade individual informa mais do que a média."
))
_t2_auc = M2["auc_xgb"] if MOD2 == "xgboost" else M2["auc_logistica"]
_t2_br = M2["brier_xgb"] if MOD2 == "xgboost" else M2["brier_logistica"]
_linhas = [["Previsão", "Modelo", "Teste (n / eventos)", "AUC", "Brier modelo / taxa base", "Supera a base?"],
           ["Procedência 1G", ROTULO_MOD[DEC["procedencia_1g"]["modelo"]], f"{milhar(M1['n_teste'])} sentenças", M1_AUC, f"{M1_BR} / {M1_BR_BASE}",
            "sim" if M1["brier_xgb"] < M1["brier_taxa_base"] else "não"],
           ["Procedência 2G", ROTULO_MOD[MOD2], f"{M2_NT} acórdãos", fmt(_t2_auc, 3),
            f"{fmt(_t2_br, 3)} / {M2_BR_BASE}", "sim" if _t2_br < M2["brier_taxa_base"] else "não"],
           ["Acordo pré-sentença", ROTULO_MOD[DEC["acordo_pre"]["modelo"]], f"{milhar(MPRE['n_teste'])} / {PRE_EV_TE} acordos", PRE_AUC,
            f"{PRE_BR} / {PRE_BR_BASE}", "sim" if MPRE["brier_xgb"] < MPRE["brier_taxa_base"] else "<b>não</b>"],
           ["Acordo pós-sentença", ROTULO_MOD[DEC["acordo_pos"]["modelo"]], f"{milhar(MPOS['n_teste'])} / {POS_EV_TE} acordos", POS_AUC,
            f"{POS_BR} / {POS_BR_BASE}", "sim" if MPOS["brier_logistica"] < MPOS["brier_taxa_base"] else "não"]]
story.append(tabela(_linhas, [3.4 * cm, 2 * cm, 3.4 * cm, 1.4 * cm, 3.6 * cm, 2.2 * cm], destaque_linhas={3}))
story.append(p(
    "Procedência 1G no teste do split temporal da Fase 4; procedência 2G e acordos no teste dos 20% mais "
    "recentes pela data da decisão (ou do acordo).",
    "CorpoTabelaNota",
))
story.append(p(
    f"A <b>procedência 1G</b> separa bem casos de chance baixa e alta (AUC {M1_AUC}) e supera a taxa base, mas "
    f"tende a superestimar os perfis mais favoráveis: a taxa de sucesso caiu de {M1_TX_TR} no treino para "
    f"{M1_TX_TE} no teste, em parte porque o teste só tem os processos que já foram julgados — os mais rápidos, "
    f"entre eles muitas extinções. A <b>procedência 2G</b> fica bem acima da taxa base (Brier {fmt(_t2_br, 3)} "
    f"contra {M2_BR_BASE}); no teste, a regressão logística seria um pouco melhor (AUC {M2_AUC_LOG}, Brier "
    f"{M2_BR_LOG}), mas a escolha foi feita antes, pela validação. O <b>acordo pós-sentença</b> é o mais "
    f"previsível (AUC {POS_AUC}), quase todo pelo resultado do 1G: quando o 1G é procedente, o réu fecha acordo "
    "com muito mais frequência."
))
story.append(p(
    f"<b>Ponto fraco declarado:</b> no teste final, o acordo pré-sentença <b>não</b> supera a taxa base (Brier "
    f"{PRE_BR} contra {PRE_BR_BASE}), embora ordene bem os casos (AUC {PRE_AUC}). O motivo é de época: a taxa de "
    f"acordos pré-sentença foi de {PRE_TX_TR} no treino para {PRE_TX_TE} no teste (houve um pico de {PICO_PRE_FMT} "
    f"no {PICO_PRE_QUANDO} e, nos últimos 12 meses, a taxa observada foi de {REF_NG} no NG e {REF_LA} no LA). A regra "
    "fixada antes manda mostrar a previsão, e a página a mostra — com o aviso de que, no teste mais recente, a "
    "taxa real ficou abaixo do previsto, e que o número deve ser lido como um teto provável.",
    "Destaque",
))

story.append(p("3.2 O que pesa na previsão de prazo", "H2"))
story.append(p(
    f"Importância de cada grupo de variáveis no XGBoost-AFT (ganho acumulado nas árvores): {FAT_TXT}. Onde o "
    "processo tramita (comarca e competência) pesa mais do que o assunto; o ano de distribuição entra porque "
    "o ritmo dos processos mudou ao longo do tempo."
))

story.append(CondPageBreak(8 * cm))
story.append(p("3.3 Exemplos de saída da página", "H2"))
story.append(p(
    "Calculados com a mesma lógica da página (mistura ponderada pelos seis filtros), a partir do arquivo que a "
    "página consome. Probabilidades de 2G e de acordo pós-sentença sem resultado do 1G informado (chance "
    "combinada)."
))
_linhas = [["Perfil", "Base (treino)", "Mediana (50% entre)", "Proc. 1G", "Acordo pré", "Proc. 2G", "Acordo pós"]]
for rot, e in EXEMPLOS:
    _linhas.append([rot, milhar(e["base"]), f"{e['mediana']} d ({e['p25']}–{e['p75']})", pct(e["p1"], 0),
                    pct(e["ac_pre"], 1), pct(e["p2"], 0), pct(e["ac_pos"], 1)])
story.append(tabela(_linhas, [4.6 * cm, 1.8 * cm, 3 * cm, 1.6 * cm, 1.8 * cm, 1.6 * cm, 1.8 * cm]))
story.append(p(
    f"Exemplo de leitura: para um processo do NG de matéria ESPECIFICA, em Manaus, de indenizatória, a página "
    f"prevê {ESP_FMT}. A faixa larga não é defeito do modelo: mostra o quanto a duração varia mesmo entre casos "
    "com as mesmas características.",
    "CorpoTabelaNota",
))

story.append(CondPageBreak(7 * cm))
story.append(p("3.4 Teste de uma variável nova: o réu", "H2"))
story.append(p(
    "O réu (o adverso do processo no LexFlow, agrupado pela raiz do CNPJ para juntar filiais da mesma empresa) "
    "foi testado como covariável adicional. Ele atende ao requisito de estar disponível desde o início — está "
    "preenchido em 99% dos processos com sentença e em 96% dos sem sentença, sem o vazamento que inviabiliza juiz "
    "e relator (preenchidos em 79% e 82% dos processos já decididos, contra 28% e 11% dos ainda sem decisão). Os 21 "
    "grupos de réu com pelo menos 300 processos no "
    "treino cobrem cerca de 80% da coorte; os demais formam um grupo \"Outros\". Mesma configuração, mesma "
    "validação temporal e mesmo teste final dos modelos atuais:"
))
story.append(tabela([
    ["Previsão (modelo)", "Validação: sem → com réu", "Teste final: sem → com réu", "Leitura"],
    ["Prazo (XGBoost-AFT), C-index", "backtest: 0,702 → 0,694 e 0,631 → 0,636", "0,646 → 0,646", "empate"],
    ["Procedência 1G (XGBoost), AUC / Brier", "0,690 → 0,693 / 0,1737 → 0,1728", "0,677 → 0,674 / 0,1671 → 0,1683", "empate"],
    ["Procedência 2G (XGBoost), AUC / Brier", "0,898 → 0,900 / 0,1163 → 0,1146", "0,680 → 0,701 / 0,1919 → 0,1904",
     "ganho pequeno"],
    ["Acordo pré-sentença (XGBoost), AUC / Brier", "0,779 → 0,751 / 0,0171 → 0,0185", "0,699 → 0,707 / 0,0098 → 0,0097",
     "piora"],
    ["Acordo pós-sentença (logística), AUC / Brier", "0,864 → 0,857 / 0,0407 → 0,0414", "0,914 → 0,919 / 0,0475 → 0,0460",
     "misto"],
], [4.6 * cm, 4.6 * cm, 4.6 * cm, 2.2 * cm]))
story.append(Spacer(1, 6))
story.append(p(
    "O réu ficou com cerca de 3% do peso do modelo de prazo e não trouxe ganho consistente: só a procedência 2G "
    "melhorou na validação e no teste ao mesmo tempo, e pouco. Nos acordos, onde se esperava o maior efeito (a "
    "política de acordo varia entre empresas), ele piorou o acordo pré-sentença na validação e teve efeito misto "
    "no pós-sentença. A explicação é que a informação do réu já está nas variáveis atuais: a matéria praticamente "
    "determina o réu (as matérias bancárias são quase todas contra o mesmo banco, que responde por cerca de metade "
    "da carteira; telefonia, energia e negativação vão contra outras empresas); o acordo pós-sentença é dominado "
    "pelo resultado do 1G; e o acordo pré-sentença depende mais da época (campanhas) do que de quem é o réu — o "
    "modelo acaba aprendendo quais empresas fecharam acordo numa campanha passada. Somado ao custo de incluir o "
    "réu na página (a grade de previsões seria multiplicada pelo número de grupos de réu), a variável não foi "
    "adotada. O resultado reforça o diagnóstico de generalização da Fase 5: o limite do desempenho está no tipo de "
    "informação disponível, não na quantidade de variáveis."
))

story.append(CondPageBreak(7 * cm))
story.append(p("3.5 Teste de uma variável nova: a vara", "H2"))
story.append(p(
    "No LexFlow a vara é cadastrada só pelo número (1ª, 2ª, …, Vara Única) — a \"1ª vara\" existe em toda comarca e "
    "competência. Para identificar a vara de fato, ela foi composta como comarca + competência + número (939 "
    "combinações; as 37 com pelo menos 300 processos no treino cobrem 60% dele, as demais formam \"Outras\"). O campo "
    "está preenchido em 96,7% dos processos do LexFlow (NG 94,1%, LA/AM 97,7%, LA/RJ 98,7%) e não tem vazamento: "
    "100% dos processos com sentença e 97% dos sem sentença têm a vara. Mesmo protocolo do teste do réu:"
))
story.append(tabela([
    ["Previsão (modelo)", "Validação: sem → com vara", "Teste final: sem → com vara", "Leitura"],
    ["Prazo (XGBoost-AFT), C-index", "backtest: 0,702 → 0,709 e 0,631 → 0,611; calibração piora nas duas",
     "0,646 → 0,656", "não adotar"],
    ["Procedência 1G (XGBoost), AUC / Brier", "0,690 → 0,690 / 0,1737 → 0,1737", "0,677 → 0,733 / 0,1671 → 0,1582",
     "ganho só no teste"],
    ["Procedência 2G (XGBoost), AUC / Brier", "0,898 → 0,899 / 0,1163 → 0,1175", "0,680 → 0,700 / 0,1919 → 0,1899",
     "ganho só no teste"],
    ["Acordo pré-sentença (XGBoost), AUC / Brier", "0,779 → 0,779 / 0,0171 → 0,0171", "0,699 → 0,703 / 0,0098 → 0,0096",
     "empate"],
    ["Acordo pós-sentença (logística), AUC / Brier", "0,864 → 0,866 / 0,0407 → 0,0407", "0,914 → 0,913 / 0,0475 → 0,0476",
     "empate"],
], [4.6 * cm, 4.6 * cm, 4.6 * cm, 2.2 * cm]))
story.append(Spacer(1, 6))
story.append(p(
    "Diferentemente do réu, a vara traz informação nova (o comportamento de cada juízo) e chegou a 15% do peso do "
    "modelo de prazo. Mas o efeito aparece só no período mais recente: na validação e no backtest — processos de "
    "2024 e 2025 — ela não melhora, e no backtest de jan/2025 piora o prazo; no teste final (mar–nov/2026) melhora, "
    "sobretudo a procedência 1G (AUC de 0,677 para 0,733, o maior ganho entre as variáveis testadas). A leitura mais "
    "provável é de época: varas e juizados são reorganizados e juízes mudam, de modo que o que caracteriza uma vara "
    "hoje não é o que a caracterizava em 2023–2024. Pela regra de seleção do estudo — decidir pela validação, nunca "
    "pelo teste —, a vara não foi adotada; adotá-la pelo ganho no teste repetiria o erro corrigido na Seção 2.4. Ela "
    "é, no entanto, a candidata mais promissora: a seleção deve ser refeita quando houver mais meses de dados "
    "recentes, e, se o ganho se confirmar também na validação, a vara entra nos modelos de procedência."
))

# ---------------------------------------------------------------------------
# 4. DISCUSSAO
# ---------------------------------------------------------------------------
story.append(p("4. Discussão", "H1"))
story.append(p(
    "<b>O que a ferramenta entrega.</b> Um prazo típico com faixa de incerteza validada, e quatro "
    "probabilidades que permitem comparar perfis de processo — por exemplo, mostrar que, numa mesma comarca, "
    "uma matéria tende a ser mais rápida ou mais favorável que outra, ou que o resultado do 1G muda muito a "
    "perspectiva no 2G e a chance de acordo. Essas comparações relativas são o uso mais seguro."
))
story.append(p(
    "<b>O que ela não entrega.</b> As probabilidades de procedência e de acordo são condicionais a haver aquela "
    "decisão; elas não dizem a chance de o processo chegar a ela, nem quando. A forma mais completa de responder "
    "\"qual a chance de terminar com sucesso, por acordo ou com perda até a data X\" é modelar os desfechos como "
    "<b>riscos competitivos</b> de ponta a ponta — a abordagem do Fine-Gray da Fase 3 levada à previsão "
    "individual —, que fica como trabalho futuro."
))
story.append(p(
    "<b>Época e retreino.</b> Duas coisas mudaram com o tempo na carteira: os processos ficaram mais rápidos e a "
    "taxa de acordos oscilou com campanhas. O modelo de prazo trata a primeira com o ano de distribuição; a "
    "segunda aparece como a principal fragilidade do acordo pré-sentença. Nos dois casos, o modelo precisa ser "
    "retreinado periodicamente, e a página deixa explícito de quando é o modelo em uso "
    f"(gerado em {DATA_GERACAO})."
))
story.append(p(
    "<b>Uso responsável.</b> Uma estimativa estatística apresentada com precisão de um número pode ser lida como "
    "promessa. Por isso a página mostra a base de processos por trás de cada previsão, avisa quando ela é pequena, "
    "não mostra previsão quando não há histórico e explica em cada card o que o número é e o que não é."
))

# ---------------------------------------------------------------------------
# 5. LIMITACOES
# ---------------------------------------------------------------------------
story.append(p("5. Limitações", "H1"))
story.append(lista([
    "<b>Viés de seleção das probabilidades condicionais:</b> só entram processos que já tiveram a decisão; os "
    "julgados rapidamente não são iguais aos lentos (foi isso que derrubou a primeira validação do 2G).",
    "<b>Mudança de época nos acordos:</b> o acordo pré-sentença não supera a taxa base no teste mais recente.",
    "<b>Categorias raras:</b> matérias, comarcas e competências fora das mais frequentes compartilham a previsão "
    "do grupo \"Outros\".",
    f"<b>Qualidade das etiquetas de acordo:</b> dos {N_ET_POS} processos com etiqueta \"pós-sentença\" e data de "
    f"acordo, {N_ET_POS_DISC} ({DISC_PCT}) têm a data de acordo fora da janela entre a sentença e o acórdão.",
    "<b>Foto do modelo:</b> a página usa previsões pré-calculadas de um treino específico; entre um retreino e "
    "outro, ela não acompanha mudanças recentes da carteira.",
    "<b>Sem informação do caso concreto:</b> réu, vara, juiz, tese e provas não entram no modelo.",
]))

# ---------------------------------------------------------------------------
# 6. SINTESE
# ---------------------------------------------------------------------------
story.append(p("6. Síntese", "H1"))
story.append(p(
    "A Fase 6 levou o modelo de sobrevivência validado a uma ferramenta de consulta e o complementou com "
    "estimativas de procedência e de acordo. Três decisões dão sustentação ao resultado: a faixa de incerteza "
    "foi conferida no backtest; as escolhas de modelo foram feitas por validação temporal, sem olhar o teste "
    "final; e cada previsão que não supera a taxa base no teste é declarada como tal. O 2G e o acordo "
    "pós-sentença mostraram que o resultado do 1G é a informação mais valiosa depois da sentença — por isso ele "
    "entra como cenário. Os próximos passos naturais são os riscos competitivos de ponta a ponta, variáveis do "
    "caso concreto (réu, vara) e um retreino periódico automatizado."
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(p("Referências", "H1"))
for ref in [
    "CHEN, T.; GUESTRIN, C. XGBoost: A Scalable Tree Boosting System. In: <i>Proceedings of the 22nd ACM SIGKDD "
    "International Conference on Knowledge Discovery and Data Mining</i>. New York: ACM, 2016. p. 785-794.",
    "BARNWAL, A.; CHO, H.; HOCKING, T. Survival Regression with Accelerated Failure Time Model in XGBoost. "
    "<i>Journal of Computational and Graphical Statistics</i>, v. 31, n. 4, p. 1292-1302, 2022.",
    "FINE, J. P.; GRAY, R. J. A Proportional Hazards Model for the Subdistribution of a Competing Risk. "
    "<i>Journal of the American Statistical Association</i>, v. 94, n. 446, p. 496-509, 1999.",
    "BRIER, G. W. Verification of Forecasts Expressed in Terms of Probability. <i>Monthly Weather Review</i>, "
    "v. 78, n. 1, p. 1-3, 1950.",
    "HYNDMAN, R. J.; ATHANASOPOULOS, G. <i>Forecasting: Principles and Practice</i>. 3. ed. Melbourne: OTexts, "
    "2021. (Validação com origem móvel.)",
    "STEYERBERG, E. W. <i>Clinical Prediction Models</i>. 2. ed. Cham: Springer, 2019. (Calibração, "
    "recalibração e uso responsável de modelos de previsão.)",
]:
    story.append(p(ref, "Referencia"))
story.append(Spacer(1, 10))
story.append(p(
    "Este capítulo complementa os capítulos das Fases 2 a 5, na mesma pasta de pesquisa. Scripts reprodutíveis: "
    "scripts/fase6_prototipo_dados.py, fase6_grade.py, fase6_procedencia.py, fase6_procedencia_2g.py, "
    "fase6_acordos.py, fase6_selecao_temporal.py, fase6_exportar_bundle_api.py e scripts/gerar_capitulo_fase6.py "
    "(este documento); pipeline completo em scripts/rodar_pipeline.py.",
    "CorpoTabelaNota",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Fase 6: Previsão Individualizada",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
