# -*- coding: utf-8 -*-
"""
Gera Capitulo_7_Discussao_e_Conclusao.pdf - discussao geral e conclusao do TCC, costurando
as Fases 2 a 6 e o Apendice A. Mesmo padrao visual dos capitulos.

Fontes (nada digitado): dados/fase2_numeros.json, fase3_cox_resumo.json,
fase3_finegray_resumo.json, fase4_*.csv, fase5_*.csv/json, fase6_*.json,
historico_versoes.json, qualidade_dados.json e os backups das versoes anteriores
(backups_fases_pre_distribuicao/, backups_fases_pre_ampliacao/).

Referencias: as de direito/jurimetria foram conferidas na web em 10/11/2026 (Aletras et
al. 2016; Katz, Bommarito e Blackman 2017; Medvedeva, Vols e Wieling 2020; Nunes 2016;
CNJ Justica em Numeros 2024) - nenhum numero de outros trabalhos e citado.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_conclusao.py
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
OUT_PDF = f"{BASE_DIR}/Capitulo_7_Discussao_e_Conclusao.pdf"
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
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Capítulo 7: Discussão geral e conclusão")
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
# Numeros (todos lidos de arquivo)
# ---------------------------------------------------------------------------
def csv(nome, pasta="dados"):
    return pd.read_csv(f"{BASE_DIR}/{pasta}/{nome}")


F2 = ler("fase2_numeros.json")
COX3, FG3 = ler("fase3_cox_resumo.json"), ler("fase3_finegray_resumo.json")
HIST = ler("historico_versoes.json")
QUAL = ler("qualidade_dados.json")
SEL = ler("fase6_selecao_temporal.json")
P1 = ler("fase6_procedencia.json")["metricas"]
P2 = ler("fase6_procedencia_2g.json")
AC = ler("fase6_acordos.json")["metricas"]
FATORES = ler("fase6_prototipo_previsoes.json")["fatores"]
BT_INFO = {d["origem"]: d for d in ler("fase5_backtest_info.json")}

N_COORTE = F2["n_total"]
E1, E2 = F2["estagio1"], F2["estagio2"]
MED_E1, MED_E2 = milhar(E1["mediana"]), milhar(E2["mediana"])
PCT_FAV = f"{E1['pct_favoravel']:.1f}".replace(".", ",") + "%"
PCT_PAGO = f"{E2['pct_pago']:.1f}".replace(".", ",") + "%"
N_MOD, N_DESC = COX3["n_modelo"], COX3["n_descartados_valor_causa"]
C3 = fmt(COX3["cindex"])
PH_V, PH_N = COX3["n_covariaveis_ph_violadas"], COX3["n_covariaveis"]
FG_INT, FG_AC, FG_DESF = FG3["evento_interesse"], FG3["concorrente_acordo"], FG3["concorrente_merito_desfav"]

cox4 = csv("fase4_cox_mesmo_split_metricas.csv").iloc[0]
xgb4 = csv("fase4_xgboost_metricas.csv").iloc[0]
rsf4 = csv("fase4_rsf_tunada_metricas.csv").iloc[0]
N_TR, N_TE = int(cox4["n_treino"]), int(cox4["n_teste"])
C_COX, C_XGB, C_RSF = fmt(cox4["cindex_teste"], 4), fmt(xgb4["cindex_teste"], 4), fmt(rsf4["cindex_teste"], 4)
ibs = csv("fase4_brier_resultado.csv").set_index("modelo")["ibs"]
IBS_COX, IBS_RSF, IBS_XGB = fmt(ibs["Cox"], 4), fmt(ibs["RSF_tunada"], 4), fmt(ibs["XGBoost_AFT"], 4)
ic = csv("fase5_bootstrap_ic.csv").set_index("modelo")
IC_XGB = f"[{fmt(ic.loc['XGBoost_AFT', 'ic_2.5%'])}; {fmt(ic.loc['XGBoost_AFT', 'ic_97.5%'])}]"
IC_COX = f"[{fmt(ic.loc['Cox', 'ic_2.5%'])}; {fmt(ic.loc['Cox', 'ic_97.5%'])}]"
vit = csv("fase5_bootstrap_vitorias.csv").iloc[0]
VIT_XC = pct(vit["xgb_vs_cox"] / vit["n_validas"], 0)
VIT_XR = pct(vit["xgb_vs_rsf"] / vit["n_validas"], 0)
cal90 = csv("fase5_calibracao.csv")
cal90["d"] = cal90["s_previsto_medio"] - cal90["s_observado_km"]
_d = cal90.groupby("modelo")["d"]
CAL_XGB = f"{fmt(_d.min()['XGBoost_AFT'])} a {fmt(_d.max()['XGBoost_AFT'])}"
CAL_COX = f"{fmt(_d.min()['Cox'])} a {fmt(_d.max()['Cox'])}"

btm = csv("fase5_backtest_metricas.csv")
btc = csv("fase5_backtest_calibracao.csv")
btc["e"] = (btc["previsto"] - btc["observado"]).abs()
ORIG = sorted(btm["origem"].unique())


def bt_c(origem, modelo):
    return fmt(btm[(btm["origem"] == origem) & (btm["modelo"] == modelo)]["cindex"].iloc[0], 3)


def bt_e(modelo, h):
    v = btc[(btc["modelo"] == modelo) & (btc["horizonte"] == h)]["e"]
    return fmt(v.min(), 2) + "–" + fmt(v.max(), 2)


def orig_br(o):
    return pd.Timestamp(o).strftime("%m/%Y")


SEG = {o: milhar(BT_INFO[o]["seguimento_min_teste_dias"]) for o in ORIG}
cob = HIST["cobertura_faixas_backtest"]
COB50 = f"{pct(min(v['faixa_50'] for v in cob.values()), 0)} a {pct(max(v['faixa_50'] for v in cob.values()), 0)}"

# historico de versoes (discriminacao no teste; vitorias XGB x Cox)
def _v(pasta):
    x = csv("fase4_xgboost_metricas.csv", pasta).iloc[0]["cindex_teste"]
    c = csv("fase4_cox_mesmo_split_metricas.csv", pasta).iloc[0]["cindex_teste"]
    w = csv("fase5_bootstrap_vitorias.csv", pasta).iloc[0]
    return x, c, 100 * w["xgb_vs_cox"] / w["n_validas"]


V1 = _v("backups_fases_pre_distribuicao")
IBS_HIST = "; ".join(
    f"{rot}: {fmt(b['XGBoost_AFT'], 3)} contra {fmt(b['Cox'], 3)} do Cox"
    for rot, b in (
        ("contratação", csv("fase4_brier_resultado.csv", "backups_fases_pre_distribuicao").set_index("modelo")["ibs"]),
        ("distribuição 8/8", csv("fase4_brier_resultado.csv", "backups_fases_pre_ampliacao").set_index("modelo")["ibs"]),
        ("versão final", ibs),
    )
)
V2 = _v("backups_fases_pre_ampliacao")
h_a, h_r = HIST["24mat_8com_config_antiga"], HIST["24mat_8com_config_revista"]
V3 = (h_a["cindex_teste_xgb"], h_r["cindex_teste_cox"], h_a["pct_vitorias_xgb_vs_cox"])
V4 = (h_r["cindex_teste_xgb"], h_r["cindex_teste_cox"], h_r["pct_vitorias_xgb_vs_cox"])
V5 = (xgb4["cindex_teste"], cox4["cindex_teste"], 100 * vit["xgb_vs_cox"] / vit["n_validas"])
F2_OLD = json.load(open(f"{BASE_DIR}/backups_fases_pre_distribuicao/fase2_numeros.json", encoding="utf-8"))
MED_E1_CONTRAT = milhar(F2_OLD["estagio1"]["mediana"])
C_24_8, C_24_14 = fmt(V4[0], 4), fmt(V5[0], 4)
C_ANTIGA = fmt(V3[0], 4)

# Fase 6
AUC_1G, BR_1G, BB_1G = fmt(P1["1G"]["auc_xgb"], 2), fmt(P1["1G"]["brier_xgb"], 3), fmt(P1["1G"]["brier_taxa_base"], 3)
AUC_2G_V1 = fmt(P1["2G"]["auc_xgb"], 2)
_m2 = P2["metricas"]["com_resultado_1g"]
_k2 = "xgb" if P2["modelo_final"] == "xgboost" else "logistica"
AUC_2G, BR_2G, BB_2G = fmt(_m2[f"auc_{_k2}"], 2), fmt(_m2[f"brier_{_k2}"], 3), fmt(_m2["brier_taxa_base"], 3)
_kp = "xgb" if AC["pre"]["modelo_final"] == "xgboost" else "logistica"
_kq = "xgb" if AC["pos"]["modelo_final"] == "xgboost" else "logistica"
AUC_PRE, BR_PRE, BB_PRE = fmt(AC["pre"][f"auc_{_kp}"], 2), fmt(AC["pre"][f"brier_{_kp}"], 4), fmt(AC["pre"]["brier_taxa_base"], 4)
AUC_POS, BR_POS, BB_POS = fmt(AC["pos"][f"auc_{_kq}"], 2), fmt(AC["pos"][f"brier_{_kq}"], 4), fmt(AC["pos"]["brier_taxa_base"], 4)
TX_PRE_TR, TX_PRE_TE = pct(AC["pre"]["taxa_treino"], 1), pct(AC["pre"]["taxa_teste"], 1)
FAT = ", ".join(f"{f['nome'].lower()} ({f['pct']:.0f}%)" for f in FATORES[:5])
from coorte_comum import TOP_COMARCA as _TC, TOP_MATERIA as _TM  # noqa: E402
GRAN = f"{len(_TM)} matérias / {len(_TC)} comarcas"  # configuracao ADOTADA (ver Fase 4, Secao 2.4)

import rodar_pipeline  # noqa: E402
N_ETAPAS = len(rodar_pipeline.ETAPAS)

# Qualidade
QE, QA = QUAL["anterior"], QUAL["estudo"]   # antes (foto 09/11) / depois (foto final, a do estudo)
Q_SEM_DATA_E, Q_SEM_DATA_A = milhar(QE["acordao_merito_sem_data"]), milhar(QA["acordao_merito_sem_data"])
Q_RED = pct(1 - QA["acordao_merito_sem_data"] / QE["acordao_merito_sem_data"], 0)
Q_SENT_SEM_RES = milhar(QA["sentenca_com_data_sem_resultado"])
Q_ET_POS = pct(QA["etiqueta_POS_discorda_data"] / QA["etiqueta_POS_com_data"], 0)
TEND = QUAL["tendencias_estudo"]
ACEL_DE, ACEL_ATE = TEND[0], TEND[-1]
ACEL = (f"{milhar(ACEL_DE['mediana_km_dias'])} dias para os distribuídos em {ACEL_DE['ano']} a "
        f"{milhar(ACEL_ATE['mediana_km_dias'])} dias em {ACEL_ATE['ano']}")

story = []
story.append(Spacer(1, 3 * cm))
story.append(p("Capítulo 7 — Discussão geral e conclusão", "TituloCapa"))
story.append(p("Previsão de prazo e desfecho de processos judiciais com análise de sobrevivência e aprendizado "
               "de máquina: o que o estudo mostrou", "SubtituloCapa"))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    "Este capítulo costura os resultados das Fases 2 a 6 e do Apêndice A. Os números citados são lidos dos mesmos "
    "arquivos de resultado usados nos capítulos anteriores (scripts/gerar_capitulo_conclusao.py).",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# 1
story.append(p("1. Retomada do problema", "H1"))
story.append(p(
    "O trabalho partiu de uma pergunta prática de um escritório de advocacia de massa: para um processo com "
    "determinadas características, quanto tempo até o primeiro desfecho (decisão de mérito ou acordo) e qual a "
    "chance de esse desfecho ser favorável? O tempo até o desfecho é um dado com censura — muitos processos ainda "
    "não terminaram — e os desfechos competem entre si (acordo, mérito favorável, mérito desfavorável). Por isso o "
    "estudo usou análise de sobrevivência com riscos competitivos. A hipótese central foi que modelos de "
    "aprendizado de máquina para sobrevivência — Random Survival Forest (RSF) e XGBoost com tempo de falha "
    "acelerado (XGBoost-AFT) — superariam o modelo de Cox em discriminação e em calibração."
))
story.append(p(
    f"A base final reúne {milhar(N_COORTE)} processos dos escritórios NG e LA/AM, com o relógio iniciado na "
    "distribuição, extraídos do sistema de gestão do escritório (LexFlow) e congelados numa foto com hash "
    "conferido para garantir reprodutibilidade."
))

# 2
story.append(p("2. O que cada fase mostrou", "H1"))
story.append(p("2.1 Fase 2 — descrição", "H2"))
story.append(p(
    f"A mediana até o primeiro desfecho é de {MED_E1} dias (Kaplan-Meier), e {PCT_FAV} dos processos chegam a um "
    f"mérito favorável com proveito econômico. Entre os que chegam a esse ponto, a mediana até o pagamento é de "
    f"{MED_E2} dias, com {PCT_PAGO} já pagos. As diferenças entre tipos de ação, matérias e comarcas são "
    "estatisticamente claras (log-rank), o que justificou a modelagem multivariada."
))
story.append(p("2.2 Fase 3 — modelos clássicos", "H2"))
story.append(p(
    f"O Cox, ajustado em {milhar(N_MOD)} processos ({milhar(N_DESC)} sem valor de causa ficaram de fora), "
    f"atinge C-index de {C3} nos próprios dados. O pressuposto de riscos proporcionais foi rejeitado em "
    f"{PH_V} das {PH_N} covariáveis — o efeito de comarca, competência e matéria muda ao longo do tempo. O Fine-Gray "
    f"separou o desfecho de interesse ({milhar(FG_INT)} méritos favoráveis) dos concorrentes ({milhar(FG_AC)} "
    f"acordos e {milhar(FG_DESF)} méritos desfavoráveis) e mostrou que vários fatores que aceleram o processo não "
    "aceleram o sucesso."
))
story.append(p("2.3 Fase 4 — aprendizado de máquina", "H2"))
story.append(p(
    f"No split temporal ({milhar(N_TR)} processos de treino, {milhar(N_TE)} de teste), o C-index no teste foi "
    f"{C_XGB} para o XGBoost-AFT, {C_COX} para o Cox e {C_RSF} para a RSF. Em calibração a diferença é muito maior: "
    f"Brier integrado de {IBS_XGB} (XGBoost-AFT), {IBS_RSF} (RSF) e {IBS_COX} (Cox)."
))
story.append(p("2.4 Fase 5 — validação", "H2"))
story.append(p(
    f"No bootstrap pareado do teste, o XGBoost-AFT vence o Cox em {VIT_XC} e a RSF em {VIT_XR} das reamostragens "
    f"(IC 95% do C-index: {IC_XGB}, contra {IC_COX} do Cox). Na calibração a 90 dias o erro do XGBoost-AFT por "
    f"quartil fica entre {CAL_XGB}; o do Cox, entre {CAL_COX}. O backtest — treinar só com o que se sabia numa "
    f"data passada e acompanhar o semestre seguinte por pelo menos {SEG[ORIG[0]]} e {SEG[ORIG[1]]} dias — "
    f"confirmou a vantagem em prazos longos: C-index de {bt_c(ORIG[0], 'XGBoost_AFT')} e "
    f"{bt_c(ORIG[1], 'XGBoost_AFT')} (Cox: {bt_c(ORIG[0], 'Cox')} e {bt_c(ORIG[1], 'Cox')}), e erro de calibração "
    f"por quartil a 365 dias de {bt_e('XGBoost_AFT', 365)} contra {bt_e('Cox', 365)} do Cox."
))
story.append(p("2.5 Fase 6 — previsão individualizada", "H2"))
story.append(p(
    "Os modelos viraram a página Previsão Individualizada do LexHub: prazo típico com faixa de incerteza, "
    f"chance de procedência em 1º e 2º grau e chance de acordo antes e depois da sentença. A faixa dos 50% "
    f"centrais conteve {COB50} dos processos reais no backtest. No teste final, a procedência 1G tem AUC de "
    f"{AUC_1G} (Brier {BR_1G} contra {BB_1G} da taxa base), a 2G {AUC_2G} ({BR_2G} contra {BB_2G}) e o acordo "
    f"pós-sentença {AUC_POS} ({BR_POS} contra {BB_POS}). O acordo pré-sentença ordena os casos (AUC {AUC_PRE}), "
    f"mas não supera a taxa base ({BR_PRE} contra {BB_PRE}). Os fatores que mais pesam no prazo são {FAT}."
))

# 3
story.append(p("3. Resposta à hipótese", "H1"))
story.append(p(
    "<b>A hipótese se confirma para o XGBoost-AFT e não se confirma para a RSF.</b> O XGBoost-AFT é o melhor "
    "modelo em discriminação, com diferença modesta em magnitude mas estatisticamente clara, e o melhor por larga "
    "margem em calibração — a propriedade que importa para uma ferramenta que mostra prazos e probabilidades. A "
    "RSF tem Brier integrado menor que o do Cox, mas fica atrás dele em discriminação.",
    "Destaque",
))
story.append(p(
    "A ordem entre Cox e XGBoost-AFT em discriminação, porém, <b>dependeu da especificação</b>. A tabela mostra o "
    "C-index no teste e a vitória no bootstrap em cada versão do estudo:"
))
def _lin(rot, v):
    return [rot, fmt(v[0], 4), fmt(v[1], 4), f"{v[2]:.1f}".replace(".", ",") + "%"]
story.append(tabela([
    ["Versão", "XGBoost-AFT", "Cox", "XGBoost vence Cox"],
    _lin("Relógio a partir da contratação", V1),
    _lin("Relógio a partir da distribuição, 8 matérias / 8 comarcas", V2),
    _lin("24 matérias / 8 comarcas, XGBoost sem ano de distribuição", V3),
    _lin("24 / 8, XGBoost com ano de distribuição e nível inicial", V4),
    _lin(f"Versão final ({GRAN}, escolhida sem o teste)", V5),
], [8.6 * cm, 2.6 * cm, 2.2 * cm, 3.6 * cm], destaque_linhas={5}))
story.append(p(
    "As duas primeiras linhas usam coortes anteriores (antes da exclusão dos agravos pelo número CNJ e do RJ); as "
    "demais, a foto final. Versões 3 e 4 recalculadas por scripts/historico_versoes.py.",
    "CorpoTabelaNota",
))
story.append(p(
    "A vantagem em discriminação oscilou de clara para empate técnico e de volta para clara conforme o marco zero, "
    "a granularidade das categorias e o tratamento da época mudaram. Já a vantagem em calibração apareceu em todas "
    f"as versões em que o Brier integrado foi medido ({IBS_HIST}). A conclusão robusta do trabalho é, portanto, sobre calibração; a de discriminação vale para a "
    "especificação final, escolhida sem olhar o teste."
))

# 4
DIAG = ler("diagnostico_generalizacao.json")  # scripts/diagnostico_generalizacao.py
_dcr = {r["rodadas"]: r for r in DIAG["curva_rodadas"]}
DG_GAP_A, DG_GAP_B = fmt(_dcr[min(_dcr)]["gap"]), fmt(_dcr[max(_dcr)]["gap"])
DG_R_A, DG_R_B = min(_dcr), max(_dcr)
DG_TE10, DG_TE100 = fmt(DIAG["curva_aprendizado"][0]["teste"]), fmt(DIAG["curva_aprendizado"][-1]["teste"])
DG_PERM = fmt(DIAG["permutacao"]["teste_medio"])
story.append(p("4. Lições metodológicas", "H1"))
story.append(p(
    "Talvez a contribuição mais útil do trabalho esteja menos nos números finais e mais no que foi preciso "
    "corrigir para chegar a eles. Cada item abaixo mudou o resultado de forma mensurável."
))
story.append(lista([
    f"<b>Marco zero.</b> Contar o tempo a partir da contratação mede a relação com o escritório, não o processo. "
    f"Trocar para a distribuição mudou a mediana (era {MED_E1_CONTRAT} dias na coorte antiga) e a própria ordem "
    "entre os modelos.",
    "<b>Teste curto engana.</b> O teste temporal só acompanhava os processos por poucos meses; as previsões de prazo "
    "longo só puderam ser validadas com o backtest, que simula estar numa data passada.",
    f"<b>A época importa.</b> Os processos ficaram mais rápidos ({ACEL}) e os acordos dependem de campanhas. Sem a "
    "variável de ano de distribuição, o modelo previa o ritmo antigo — e isso exige retreino periódico.",
    "<b>Nível inicial do XGBoost-AFT.</b> Com taxa de aprendizado baixa, o nível das previsões dependia de quantas "
    "rodadas o early stopping escolhia; iniciar na mediana de Kaplan-Meier do treino tornou o modelo estável.",
    f"<b>Escolher sem olhar o teste.</b> Granularidade e modelos de procedência e acordo foram reescolhidos por "
    f"validação que não usa o teste final. Três decisões mudaram, e no teste a escolha limpa ficou um pouco atrás "
    f"da que o teste preferiria ({C_24_14} contra {C_24_8}) — o custo honesto de uma avaliação independente.",
    f"<b>Probabilidades condicionais e viés de seleção.</b> A primeira validação da procedência 2G deu AUC de "
    f"{AUC_2G_V1} porque o teste só continha os acórdãos rápidos; validar pela data do acórdão e incluir o "
    "resultado do 1G tornou o modelo útil.",
    f"<b>Qualidade dos dados.</b> {Q_SENT_SEM_RES} sentenças sem resultado, acórdãos sem data e etiquetas de acordo "
    f"inconsistentes ({Q_ET_POS} das \"pós-sentença\" discordam da data). Medir isso levou a correções na origem, "
    f"que reduziram os acórdãos de mérito sem data de {Q_SEM_DATA_E} para {Q_SEM_DATA_A} ({Q_RED} a menos).",
    f"<b>Aprender, não decorar.</b> O C-index de treino fica acima do de teste, o que costuma levantar a suspeita "
    f"de memorização. O diagnóstico de generalização mostrou o contrário: a diferença já existe com {DG_R_A} rodadas "
    f"({DG_GAP_A}) e quase não cresce até {DG_R_B} ({DG_GAP_B}), enquanto o teste segue subindo; ela vem dos "
    f"processos antigos, mais fáceis de ordenar; o teste quase não muda com 10 vezes mais dados ({DG_TE10} para "
    f"{DG_TE100}); e, com os desfechos embaralhados, o C-index cai para {DG_PERM}, o nível do acaso. O limite do "
    "desempenho está nas variáveis disponíveis, não no volume de dados nem em memorização.",
    f"<b>Reprodutibilidade.</b> Foto do banco congelada com hash conferido, pipeline único com {N_ETAPAS} "
    "etapas (scripts/rodar_pipeline.py), histórico de versões recalculado e versões de bibliotecas fixadas.",
]))

# 5
story.append(p("5. Relação com a literatura", "H1"))
story.append(p(
    "A previsão em direito com aprendizado de máquina tem se concentrado em prever o <i>resultado</i> de decisões "
    "a partir do texto ou de atributos dos casos, sobretudo em cortes superiores: a Corte Europeia de Direitos "
    "Humanos (ALETRAS et al., 2016; MEDVEDEVA; VOLS; WIELING, 2020) e a Suprema Corte dos Estados Unidos (KATZ; "
    "BOMMARITO; BLACKMAN, 2017). No Brasil, a jurimetria propõe o uso sistemático da estatística para entender o "
    "funcionamento do sistema jurídico (NUNES, 2016), e o Conselho Nacional de Justiça publica anualmente "
    "indicadores agregados de tempo e volume de tramitação (CNJ, 2024)."
))
story.append(p(
    "Este trabalho se diferencia em três pontos. Primeiro, o alvo é o <i>tempo</i> até o desfecho, tratado como "
    "dado censurado, e não só o resultado — por isso a base metodológica é a análise de sobrevivência (KAPLAN; "
    "MEIER, 1958; COX, 1972; FINE; GRAY, 1999) e suas extensões com árvores (ISHWARAN et al., 2008; BARNWAL; CHO; "
    "HOCKING, 2022). Segundo, a fonte são dados de gestão de um escritório, com todos os seus problemas de "
    "cadastro, e não bases de tribunais. Terceiro, a ênfase está em <b>calibração</b> (GRAF et al., 1999; "
    "STEYERBERG, 2019) e em <b>validação temporal</b> (HYNDMAN; ATHANASOPOULOS, 2021) — porque uma ferramenta que "
    "mostra prazos e probabilidades a pessoas precisa que os números signifiquem o que dizem, e não apenas que "
    "ordenem bem os casos (HARRELL; LEE; MARK, 1996)."
))

# 6
story.append(p("6. Contribuições", "H1"))
story.append(lista([
    "<b>Acadêmica:</b> um estudo de sobrevivência com riscos competitivos aplicado a processos de massa, com "
    "comparação entre modelos clássicos e de aprendizado de máquina e um conjunto de lições sobre validação "
    "(marco zero, backtest, época, seleção sem o teste, viés de seleção).",
    "<b>Prática:</b> a página Previsão Individualizada no LexHub, com prazo, faixa de incerteza, procedência e "
    "acordos, e o dashboard de Sobrevivência Processual.",
    "<b>Dados:</b> um diagnóstico reprodutível da qualidade do cadastro, que já resultou em correções na base de "
    "origem, e recomendações objetivas para o formulário do sistema.",
]))

# 7
story.append(p("7. Limitações gerais", "H1"))
story.append(lista([
    "Um único grupo de escritórios (NG e LA/AM), com carteira concentrada no Amazonas e em temas bancários; a "
    "generalização para outros perfis não foi testada. O RJ ficou de fora por quase não ter desfechos.",
    "Dados de gestão, não de tribunal: datas e códigos digitados à mão, com as inconsistências do Apêndice A.",
    "As probabilidades de procedência e acordo são condicionais (dado que haverá sentença, acórdão ou "
    "resolução); não respondem à chance de cada desfecho até uma data.",
    "Dependência de época: o modelo precisa de retreino periódico, e a previsão de acordo pré-sentença é um teto "
    f"provável (a taxa caiu de {TX_PRE_TR} no treino para {TX_PRE_TE} no teste).",
    "Os números do estudo vêm de uma foto congelada; correções feitas depois na origem só entram numa foto nova.",
    "Faltam variáveis potencialmente fortes, como o réu (banco ou empresa) e a vara.",
    "Os riscos competitivos foram modelados explicitamente só na Fase 3 (Fine-Gray); os modelos de aprendizado "
    "de máquina tratam qualquer desfecho como evento.",
]))

# 8
story.append(p("8. Trabalhos futuros", "H1"))
story.append(lista([
    "Riscos competitivos de ponta a ponta, estimando a chance de cada desfecho até uma data e eliminando o viés das "
    "probabilidades condicionais.",
    "Novas variáveis conhecidas desde a distribuição. O réu foi testado e não trouxe ganho consistente (a matéria já "
    "carrega essa informação — Fase 6, Seção 3.4). A vara (comarca + competência + número) melhorou a procedência 1G "
    "só no período mais recente (AUC 0,677 para 0,733 no teste) e não na validação — é a candidata a reavaliar quando "
    "houver mais meses de dados (Fase 6, Seção 3.5). Uma versão mais promissora é o ritmo recente da vara (fração "
    "dos processos distribuídos nela entre um e dois anos antes que se resolveram em até um ano): melhorou a "
    "procedência 1G na validação e no teste (AUC 0,690 para 0,722 na validação; 0,677 para 0,682 no teste) e, de "
    "leve, o acordo pré-sentença (AUC 0,779 para 0,794 na validação; 0,699 para 0,701 no teste), mas piorou o "
    "prazo no backtest, por se confundir com o ano de distribuição. Não foi incorporada porque exigiria refazer o "
    "estudo e pedir a vara na ferramenta; fica como primeira candidata para a próxima versão dos modelos de "
    "probabilidade. A composição do pedido (valores de dano moral e material) não trouxe ganho: metade da coorte "
    "não tem esses valores preenchidos. Variáveis só preenchidas depois do desfecho — como juiz e relator no "
    "cadastro atual — não podem entrar: elas vazam a informação do resultado. Só seriam usáveis se registradas já na "
    "distribuição do processo.",
    "Retreino automático periódico da ferramenta, com monitoramento da calibração.",
    "Escolher a escala e a distribuição do XGBoost-AFT pelo backtest (hoje fixadas).",
    "Estender ao RJ quando houver desfechos suficientes.",
    "Recalibração dinâmica do nível de acordos conforme a política vigente do escritório.",
]))

# 9
story.append(p("9. Conclusão", "H1"))
story.append(p(
    "O trabalho mostrou que é possível prever o tempo até o desfecho de processos de massa com dados de gestão de "
    "um escritório, com qualidade suficiente para uso prático, e que um modelo de aprendizado de máquina para "
    "sobrevivência (XGBoost-AFT) supera o modelo de Cox — de forma consistente em calibração e, na especificação "
    "final, também em discriminação. A RSF não confirmou a hipótese."
))
story.append(p(
    "Mais do que a escolha de algoritmo, o que determinou a qualidade das previsões foram decisões de desenho: "
    "quando o relógio começa, como validar previsões de prazo longo, como lidar com a mudança de ritmo ao longo "
    "do tempo, como evitar escolher o modelo olhando o teste e como tratar dados de cadastro imperfeitos. Essas "
    "lições valem para qualquer aplicação de previsão em dados jurídicos operacionais. O resultado é uma "
    "ferramenta em uso, com números validados e honestos sobre os próprios limites, e um processo de pesquisa "
    "reprodutível do dado bruto ao texto."
))

# Referencias
story.append(CondPageBreak(6 * cm))
story.append(p("Referências", "H1"))
for ref in [
    "ALETRAS, N.; TSARAPATSANIS, D.; PREOTIUC-PIETRO, D.; LAMPOS, V. Predicting judicial decisions of the European "
    "Court of Human Rights: a Natural Language Processing perspective. <i>PeerJ Computer Science</i>, v. 2, e93, "
    "2016.",
    "BARNWAL, A.; CHO, H.; HOCKING, T. Survival regression with accelerated failure time model in XGBoost. "
    "<i>Journal of Computational and Graphical Statistics</i>, v. 31, n. 4, p. 1292-1302, 2022.",
    "CONSELHO NACIONAL DE JUSTIÇA (CNJ). <i>Justiça em Números 2024</i>. Brasília: CNJ, 2024.",
    "COX, D. R. Regression models and life-tables. <i>Journal of the Royal Statistical Society: Series B</i>, v. 34, "
    "n. 2, p. 187-220, 1972.",
    "FINE, J. P.; GRAY, R. J. A proportional hazards model for the subdistribution of a competing risk. "
    "<i>Journal of the American Statistical Association</i>, v. 94, n. 446, p. 496-509, 1999.",
    "GRAF, E.; SCHMOOR, C.; SAUERBREI, W.; SCHUMACHER, M. Assessment and comparison of prognostic classification "
    "schemes for survival data. <i>Statistics in Medicine</i>, v. 18, n. 17-18, p. 2529-2545, 1999.",
    "HARRELL, F. E.; LEE, K. L.; MARK, D. B. Multivariable prognostic models: issues in developing models, "
    "evaluating assumptions and adequacy, and measuring and reducing errors. <i>Statistics in Medicine</i>, v. 15, "
    "n. 4, p. 361-387, 1996.",
    "HYNDMAN, R. J.; ATHANASOPOULOS, G. <i>Forecasting: Principles and Practice</i>. 3. ed. Melbourne: OTexts, 2021.",
    "ISHWARAN, H.; KOGALUR, U. B.; BLACKSTONE, E. H.; LAUER, M. S. Random survival forests. <i>The Annals of "
    "Applied Statistics</i>, v. 2, n. 3, p. 841-860, 2008.",
    "KAPLAN, E. L.; MEIER, P. Nonparametric estimation from incomplete observations. <i>Journal of the American "
    "Statistical Association</i>, v. 53, n. 282, p. 457-481, 1958.",
    "KATZ, D. M.; BOMMARITO, M. J.; BLACKMAN, J. A general approach for predicting the behavior of the Supreme "
    "Court of the United States. <i>PLOS ONE</i>, v. 12, n. 4, e0174698, 2017.",
    "MEDVEDEVA, M.; VOLS, M.; WIELING, M. Using machine learning to predict decisions of the European Court of "
    "Human Rights. <i>Artificial Intelligence and Law</i>, v. 28, n. 2, p. 237-266, 2020.",
    "NUNES, M. G. <i>Jurimetria: como a estatística pode reinventar o Direito</i>. São Paulo: Revista dos "
    "Tribunais, 2016.",
    "STEYERBERG, E. W. <i>Clinical Prediction Models</i>. 2. ed. Cham: Springer, 2019.",
]:
    story.append(p(ref, "Referencia"))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Capítulo 7: Discussão geral e conclusão",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
