# -*- coding: utf-8 -*-
"""
Gera Capitulo_Fase3_Resultados.pdf (Cox + Fine-Gray) a partir dos resultados
salvos em dados/fase3_cox_hazard_ratios.csv e dados/fase3_finegray_subdist_hr.csv.

Reconstruido em 13/10/2026 para incorporar comarca e competencia como novas
covariaveis (ver scripts/fase3_cox.py / fase3_finegray.py). O script anterior
que gerou a primeira versao deste capitulo nao foi salvo — este arquivo passa
a ser a fonte reprodutivel daqui pra frente; rode de novo sempre que os
modelos forem reajustados.

Nota (ver memoria do projeto): nunca usar caracteres Unicode de sobrescrito/
subscrito (ex. ⁻³⁰⁷, ₀) em texto do ReportLab — viram caixas pretas na fonte
Helvetica base-14. Usar sempre as tags <super>/<sub>.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_fase3.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import csv
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
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
OUT_PDF = f"{BASE_DIR}/Capitulo_Fase3_Resultados.pdf"

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=20, leading=25, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle(name="SubtituloCapa", fontSize=13, leading=17, fontName="Helvetica", spaceAfter=14, textColor=colors.HexColor("#333333")))
styles.add(ParagraphStyle(name="AutorData", fontSize=10.5, leading=14, fontName="Helvetica"))
styles.add(ParagraphStyle(name="NotaRodapeCapa", fontSize=9, leading=13, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceBefore=18))
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=18, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8, keepWithNext=1))
styles.add(ParagraphStyle(name="H2", fontSize=11.5, leading=15, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6, keepWithNext=1))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=14.5, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="CorpoTabelaNota", fontSize=8.5, leading=12, fontName="Helvetica-Oblique", textColor=colors.HexColor("#444444"), alignment=TA_JUSTIFY, spaceAfter=10))
styles.add(ParagraphStyle(name="Referencia", fontSize=9.5, leading=14, fontName="Helvetica", leftIndent=14, firstLineIndent=-14, spaceAfter=6))

COR_CABECALHO_TABELA = colors.HexColor("#2d3142")
COR_LINHA_ALT = colors.HexColor("#f2f2f5")
COR_REFERENCIA = colors.HexColor("#e8e6ff")


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Fase 3: Cox Proportional Hazards e Fine-Gray")
    canvas.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


def ler_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt_hr(v):
    return f"{float(v):.3f}".replace(".", ",")


def fmt_p(v):
    p = float(v)
    if p < 0.0001:
        return "<0,0001"
    return f"{p:.4f}".replace(".", ",")


def fmt_p_prosa(v):
    """Como 'p=0,1260' ou 'p&lt;0,0001', pronto pra uso dentro de texto corrido (Paragraph faz parse XML)."""
    s = fmt_p(v).replace("<", "&lt;")
    return f"p{s}" if s.startswith("&lt;") else f"p={s}"


def tabela_indicadores(pares):
    data = [["Indicador", "Valor"]] + [[k, v] for k, v in pares]
    t = Table(data, colWidths=[9 * cm, 7.4 * cm])
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO_TABELA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_LINHA_ALT))
    t.setStyle(TableStyle(estilo))
    return t


def p(texto, estilo="Corpo"):
    return Paragraph(texto, styles[estilo])


def lista(itens):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["Corpo"]), bulletColor=colors.HexColor("#2d3142")) for item in itens],
        bulletType="bullet",
        leftIndent=14,
    )


# ---------------------------------------------------------------------------
# Carrega os resultados atuais (fonte unica de verdade: os CSVs gerados pelos
# scripts de modelagem — nunca digitar numero a mao aqui)
# ---------------------------------------------------------------------------
cox_rows = {r["covariate"]: r for r in ler_csv(f"{BASE_DIR}/dados/fase3_cox_hazard_ratios.csv")}
fg_rows = {r["covariate"]: r for r in ler_csv(f"{BASE_DIR}/dados/fase3_finegray_subdist_hr.csv")}

LABEL_COV = {
    # Nomes de tipo_acao atualizados em 20/10/2026 (padronizacao do catalogo no LexFlow).
    "tipo_Outros": "Outros (tipo de ação)",
    "tipo_APELAÇÃO_CÍVEL": "APELAÇÃO CÍVEL",
    "tipo_EMBARGOS_DE_DECLARAÇÃO_CÍVEL": "EMBARGOS DE DECLARAÇÃO CÍVEL",
    "tipo_CUMPRIMENTO_DE_SENTENÇA": "CUMPRIMENTO DE SENTENÇA",
    "tipo_PETIÇÃO_CÍVEL": "PETIÇÃO CÍVEL",
    "tipo_EMBARGOS": "EMBARGOS",
    "tipo_RECURSO_INOMINADO": "RECURSO INOMINADO",
    "mat_SLN": "SLN (matéria)",
    "mat_MORA": "MORA (matéria)",
    "mat_CESTA": "CESTA (matéria)",
    "mat_ESPECIFICA": "ESPECIFICA (matéria)",
    "mat_ANP": "ANP (matéria)",
    "mat_RMC": "RMC (matéria)",
    "mat_COI_BOLETO": "COI_BOLETO (matéria)",
    "mat_PARC_CRED_PESS": "PARC_CRED_PESS (matéria)",
    "com_Outros": "Outros (comarca)",
    "com_IRANDUBA": "IRANDUBA (comarca)",
    "com_ITACOATIARA": "ITACOATIARA (comarca)",
    "com_PARINTINS": "PARINTINS (comarca)",
    "com_TEFÉ": "TEFÉ (comarca)",
    "com_SÃO_GABRIEL_DA_CACHOEIRA": "SÃO GABRIEL DA CACHOEIRA (comarca)",
    "com_MANACAPURU": "MANACAPURU (comarca)",
    "com_BENJAMIN_CONSTANT": "BENJAMIN CONSTANT (comarca)",
    "comp_Outros": "Outros (competência)",
    "comp_Vara_Cível": "Vara Cível (competência)",
    "comp_Câmara_Cível": "Câmara Cível (competência)",
    "comp_Turma_Recursal": "Turma Recursal (competência)",
    "log_valor_causa": "log(valor_causa)",
    "esc_NG": "esc_NG (vs. LA)",
}
def rotulo_cov(k):
    """Rotulo legivel: usa LABEL_COV quando existe; senao deriva do prefixo (24 materias desde 04/11/2026)."""
    if k in LABEL_COV:
        return LABEL_COV[k]
    for prefixo, sufixo in (("mat_", "matéria"), ("com_", "comarca"), ("comp_", "competência"), ("tipo_", None)):
        if k.startswith(prefixo):
            nome = k[len(prefixo):].replace("_", " " if prefixo != "mat_" else "_")
            return f"{nome} ({sufixo})" if sufixo else nome
    return k


def linha_ref(texto):
    return (f"[{texto}]", {"exp(coef)": "1.000", "exp(coef) lower 95%": None, "exp(coef) upper 95%": None, "p": "1"})


CELULA_NOME = ParagraphStyle(name="CelulaNome", fontSize=8.6, leading=10.5, fontName="Helvetica")
CELULA_NOME_REF = ParagraphStyle(name="CelulaNomeRef", fontSize=8.6, leading=10.5, fontName="Helvetica-Oblique")


def tabela_hr(linhas, titulo_cov="Covariável"):
    header = [titulo_cov, "HR", "IC 95%", "p"]
    data = [header]
    for nome, row in linhas:
        eh_ref = row["exp(coef) lower 95%"] is None
        cel_nome = Paragraph(nome, CELULA_NOME_REF if eh_ref else CELULA_NOME)
        if eh_ref:
            data.append([cel_nome, "1,000", "—", "—"])
        else:
            ic = f"{fmt_hr(row['exp(coef) lower 95%'])} - {fmt_hr(row['exp(coef) upper 95%'])}"
            data.append([cel_nome, fmt_hr(row["exp(coef)"]), ic, fmt_p(row["p"])])
    t = Table(data, colWidths=[7.4 * cm, 2.1 * cm, 4.5 * cm, 2.4 * cm], repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO_TABELA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.3),
    ]
    for i, (nome, row) in enumerate(linhas, start=1):
        if row["exp(coef) lower 95%"] is None:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_REFERENCIA))
        elif i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_LINHA_ALT))
    t.setStyle(TableStyle(estilo))
    return t


def ordem_por_hr(rows_dict):
    """Covariaveis em ordem decrescente de HR, com a linha de referencia (HR=1) no ponto em que o HR
    cruza 1 - gerado a partir do CSV, para a tabela nunca ficar defasada quando o modelo e reajustado."""
    ordenadas = sorted(rows_dict, key=lambda k: -float(rows_dict[k]["exp(coef)"]))
    acima = [k for k in ordenadas if float(rows_dict[k]["exp(coef)"]) >= 1]
    abaixo = [k for k in ordenadas if float(rows_dict[k]["exp(coef)"]) < 1]
    return acima + ["__REF__"] + abaixo


COX_DESTAQUE = ordem_por_hr(cox_rows)
FG_DESTAQUE = ordem_por_hr(fg_rows)


def montar_linhas(chaves, rows_dict):
    out = []
    for k in chaves:
        if k == "__REF__":
            out.append(linha_ref("referência: INDENIZATÓRIA / Outros (matéria) / MANAUS / Juizado Especial Cível / LA"))
        else:
            out.append((rotulo_cov(k), rows_dict[k]))
    return out


# ---------------------------------------------------------------------------
# Numeros fixos desta rodada (ver scripts/fase3_cox.py e fase3_finegray.py —
# saida completa em dados/fase3_cox_hazard_ratios.csv / fase3_finegray_subdist_hr.csv)
# ---------------------------------------------------------------------------
with open(f"{BASE_DIR}/dados/fase3_cox_resumo.json", encoding="utf-8") as _fh:
    COX_RES = json.load(_fh)
with open(f"{BASE_DIR}/dados/fase3_finegray_resumo.json", encoding="utf-8") as _fh:
    FG_RES = json.load(_fh)

N_MODELO = COX_RES["n_modelo"]
N_DESCARTADOS_VALOR_CAUSA = COX_RES["n_descartados_valor_causa"]
PCT_DESCARTADOS = COX_RES["pct_descartados"]
EVENTOS_COX = COX_RES["eventos"]
CENSURADOS_COX = COX_RES["censurados"]
CINDEX = COX_RES["cindex"]
LOGLIK_COX = COX_RES["loglik"]
AIC_COX = COX_RES["aic"]
N_COVARIAVEIS_COX = COX_RES["n_covariaveis"]
N_COVARIAVEIS_PH_VIOLADAS = COX_RES["n_covariaveis_ph_violadas"]

FG_EVENTO_INTERESSE = FG_RES["evento_interesse"]
FG_CONCORRENTE_ACORDO = FG_RES["concorrente_acordo"]
FG_CONCORRENTE_MERITO_DESFAV = FG_RES["concorrente_merito_desfav"]
FG_CENSURADOS = FG_RES["censurados"]
FG_LONG_LINHAS = FG_RES["linhas_longas"]
FG_LOGLIK = FG_RES["loglik"]

# Pre-formatados (nunca encadear .replace(".", ",") depois de strings adjacentes implicitas)
CINDEX_FMT = f"{CINDEX:.3f}".replace(".", ",")
N_MODELO_FMT = f"{N_MODELO:,}".replace(",", ".")
PCT_DESCARTADOS_FMT = f"{PCT_DESCARTADOS:.2f}".replace(".", ",")
N_DESCARTADOS_FMT = f"{N_DESCARTADOS_VALOR_CAUSA:,}".replace(",", ".")

import sys  # noqa: E402
sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import TOP_COMARCA, TOP_COMPETENCIA, TOP_MATERIA, TOP_TIPO_ACAO, carregar_coorte  # noqa: E402
_coorte = carregar_coorte()
_ngla = _coorte[_coorte["id_escritorio_assinante"].isin([20, 21])]
N_COMARCAS = _ngla["comarca"].nunique()
N_COMPETENCIAS = _ngla["competencia"].nunique()
import pandas as _pd  # noqa: E402
# RJ saiu da coorte oficial em 09/11/2026 - tamanho/censura vem da mesma extracao guardada antes do filtro
_rj = _pd.read_parquet(f"{BASE_DIR}/backups_coorte/coorte_sobrevivencia_com_rj_20261109.parquet")
_rj = _rj[_rj["id_escritorio_assinante"] == 27]
N_RJ_FMT = f"{len(_rj):,}".replace(",", ".")
PCT_RJ_CENS_FMT = f"{100 * (_rj['tipo_evento_e1'] == 'CENSURADO').mean():.0f}"
N_TOP_MATERIA, N_TOP_COMARCA, N_TOP_COMP, N_TOP_TIPO = len(TOP_MATERIA), len(TOP_COMARCA), len(TOP_COMPETENCIA), len(TOP_TIPO_ACAO)
_ngla_mod = _ngla[_ngla["valor_causa"].notna()]
PCT_COBERTURA_MATERIA_FMT = f"{100 * _ngla_mod['materia'].isin(TOP_MATERIA).mean():.0f}"

# C-index (in-sample) das versoes anteriores, lidos dos backups - nunca digitados
def _cindex_backup(pasta):
    with open(f"{BASE_DIR}/{pasta}/fase3_cox_resumo.json", encoding="utf-8") as _fh:
        return json.load(_fh)["cindex"]
CINDEX_041126_8MAT_FMT = f"{_cindex_backup('backups_fases_pre_ampliacao'):.3f}".replace(".", ",")
CINDEX_041126_24MAT_FMT = f"{_cindex_backup('backups_fases_hibrido_parcial_041126'):.3f}".replace(".", ",")
import json as _json_hist  # noqa: E402
with open(f"{BASE_DIR}/dados/historico_versoes.json", encoding="utf-8") as _fh_hist:
    HIST = _json_hist.load(_fh_hist)  # versoes anteriores recalculadas por historico_versoes.py
# 24 materias / 8 comarcas na coorte de 09/11, antes do ponto 1a trocar para 14 comarcas
# (recalculado sobre a foto congelada por historico_versoes.py - nao digitado)
CINDEX_091126_24_8_FMT = f"{HIST['fase3_cox_24mat_8com_insample']['cindex']:.3f}".replace(".", ",")
PCT_COBERTURA_COMARCA_FMT = f"{100 * _ngla_mod['comarca'].isin(TOP_COMARCA).mean():.0f}"


def milhar(v):
    return f"{v:,}".replace(",", ".")


def n_pct(v):
    pct = f"{100 * v / N_MODELO:.1f}".replace(".", ",")
    return f"{milhar(v)} ({pct}%)"


def dec2(v):
    return f"{v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")



def hr(rows, k):
    return fmt_hr(rows[k]["exp(coef)"])


def pp(rows, k):
    return fmt_p_prosa(rows[k]["p"])


def _rotulo_com(k):
    return k.replace("com_", "").replace("_", " ")


# Leitura de comarca gerada dos HRs (14 comarcas desde 09/11/2026 - nao digitar nomes a mao)
_com_cox = {k: r for k, r in cox_rows.items() if k.startswith("com_") and k != "com_Outros"}
COM_RAPIDAS = sorted([k for k, r in _com_cox.items() if float(r["p"]) < 0.05 and float(r["exp(coef)"]) > 1],
                     key=lambda k: -float(_com_cox[k]["exp(coef)"]))
COM_LENTAS = sorted([k for k, r in _com_cox.items() if float(r["p"]) < 0.05 and float(r["exp(coef)"]) < 1],
                    key=lambda k: float(_com_cox[k]["exp(coef)"]))
COM_NEUTRAS = [k for k, r in _com_cox.items() if float(r["p"]) >= 0.05]
COM_RAPIDAS_FG_MANTEM = [k for k in COM_RAPIDAS if k in fg_rows and float(fg_rows[k]["p"]) < 0.05
                         and float(fg_rows[k]["exp(coef)"]) > 1]
_ex_fg = next((k for k in COM_RAPIDAS if k in fg_rows and k not in COM_RAPIDAS_FG_MANTEM), None)


def _lista_hr(ks, rows):
    return ", ".join(f"{_rotulo_com(k)} (HR={hr(rows, k)})" for k in ks)

_hr_cumpr = float(fg_rows["tipo_CUMPRIMENTO_DE_SENTENÇA"]["exp(coef)"])
DESC_CUMPR = "mais que o dobro" if _hr_cumpr > 2 else "quase o dobro" if _hr_cumpr > 1.7 else "bem mais"

from coorte_comum import DATA_REFERENCIA_BR as DATA_FOTO, carregar_coorte as _cc_carregar  # noqa: E402
DADOS_ATE = _cc_carregar()["distribuicao_d"].max().strftime("%d/%m/%Y")  # ultima distribuicao na foto

story = []

# ---------------------------------------------------------------------------
# PAGINA 1 - CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 3 * cm))
story.append(p("Fase 3 — Resultados", "TituloCapa"))
story.append(p("Modelagem Multivariada de Sobrevivência: Regressão de Cox e Riscos Competitivos de Fine-Gray", "SubtituloCapa"))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Modelos reajustados sobre a foto da coorte extraída em {DATA_FOTO} (distribuições até {DADOS_ATE}; "
    "biblioteca lifelines, Python), restrita aos escritórios NG e LA. <b>Mudanças desde a versão de "
    "20/10/2026:</b> o marco zero (t=0) passou a ser a distribuição do processo, não mais a contratação; agravos "
    "e mandados de segurança deixaram de contar como tipo de ação, e agravos cadastrados como processo próprio "
    "saíram da coorte (identificados pelo número CNJ); e a covariável matéria passou de 8 para "
    f"{N_TOP_MATERIA} categorias (ver Seção 2.1). Todos os números e boa parte das conclusões mudaram; as "
    "mudanças de leitura estão apontadas na Seção 5.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. INTRODUCAO
# ---------------------------------------------------------------------------
story.append(p("1. Introdução", "H1"))
story.append(p(
    "A Fase 2 identificou, de forma univariada, que tipo de ação e matéria explicam diferenças estatisticamente "
    "significativas no tempo de tramitação — mas apontou um limite claro: log-rank e Kaplan-Meier testam uma "
    "dimensão por vez, sem controlar pela outra. Esta fase resolve essa limitação ajustando dois modelos "
    "multivariados sobre a mesma coorte: uma Regressão de Cox (COX, 1972), que estima o efeito de cada "
    "covariável sobre o tempo até qualquer desfecho mantendo as demais constantes, e um modelo de riscos "
    "competitivos de Fine-Gray (FINE; GRAY, 1999), que isola especificamente o efeito das covariáveis sobre a "
    "probabilidade de atingir o desfecho mais relevante operacionalmente — mérito favorável com proveito "
    "econômico — tratando os demais desfechos (acordo, mérito sem proveito ou desfavorável) como riscos "
    "concorrentes."
))

# ---------------------------------------------------------------------------
# 2. METODOLOGIA
# ---------------------------------------------------------------------------
story.append(p("2. Metodologia", "H1"))
story.append(p("2.1 Escopo e covariáveis", "H2"))
story.append(p(
    f"Os modelos foram ajustados sobre {N_MODELO_FMT} processos (coorte vigente, restrita a NG e LA; "
    f"{N_DESCARTADOS_FMT} processos sem valor de causa registrado foram descartados, {PCT_DESCARTADOS_FMT}% da "
    "base). As covariáveis categóricas de alta cardinalidade (tipo de ação, matéria, comarca e competência) "
    f"foram reduzidas às categorias de maior volume de cada dimensão — {N_TOP_TIPO} para tipo de ação (já sem "
    f"agravos e mandados de segurança, que caem em 'Outros'), {N_TOP_MATERIA} para matéria, {N_TOP_COMARCA} para "
    f"comarca, {N_TOP_COMP} para competência —, com as demais agrupadas em 'Outros'. O valor de causa entrou como log(1+valor), dada a distribuição de "
    "cauda longa típica de variáveis monetárias. A categoria de referência de cada dimensão é sempre a mais "
    "frequente (INDENIZATÓRIA para tipo de ação, 'Outros' para matéria, MANAUS para comarca, Juizado Especial "
    "Cível para competência — e LA para escritório, por ser o de maior volume; o modelo reporta o coeficiente de "
    "NG em relação a essa referência)."
))
story.append(p(
    "<b>Novidade desta atualização:</b> comarca e competência entram como covariáveis plenas pela primeira vez — "
    "antes ficavam de fora por falta de uma estratégia de agrupamento validada para a alta cardinalidade "
    f"({N_COMARCAS} comarcas e {N_COMPETENCIAS} competências distintas na coorte NG+LA atual). O critério de bucketização por volume, já usado "
    "para tipo de ação e matéria desde a Fase 2, se mostrou adequado também aqui."
))
story.append(p(
    "<b>Duas correções de dado em 20/10/2026:</b> (1) o catálogo <i>tipo_acao</i> do LexFlow foi padronizado na "
    "origem (mesmo conceito, grafia nova — ex.: 'APELAÇÃO' → 'APELAÇÃO CÍVEL'), o que mudou as 8 categorias de "
    "maior volume usadas no bucket desta variável; os nomes desta versão já refletem o catálogo padronizado. "
    "(2) a regra de precedência mérito (Seção 1, Fase 2) assumia que, quando existe acórdão, ele é sempre o "
    "desfecho de mérito válido — mas isso é falso quando o acórdão apenas anula a sentença e devolve o processo "
    "para o 1º grau rejulgar (categoria 'SENTENÇA ANULADA' do catálogo <i>acordao_merito_segundo_grau</i>, "
    "id=8): nesse caso o desfecho de verdade é o da sentença nova, não o do acórdão anulador. Na coorte da "
    "época (t=0 na contratação), a correção afetou ~142 dos ~40 mil processos (0,36%) — pequeno em volume, mas 25 deles mudaram de classificação "
    "(19 de 'sem proveito' para 'censurado', 6 de 'sem proveito' para 'favorável com proveito' — o sinal mais "
    "sério dos dois). Achado e correção do próprio pesquisador, a partir de um caso real observado durante a "
    "triagem de inconsistências de data da Fase 1."
))
story.append(p(
    "<b>Duas mudanças em 03-04/11/2026:</b> (1) o t=0 passou da contratação para a <b>distribuição</b> do "
    "processo — a contratação mede a relação comercial com o escritório, não o tempo de tramitação judicial; a "
    f"coorte NG+LA modelada passou de ~39,8 mil para {N_MODELO_FMT} processos; (2) agravos e mandados de "
    "segurança deixaram de ser categorias de tipo de ação (são incidentes processuais / remédio atípico, não a "
    "ação principal) e passaram a cair em 'Outros'. Os buckets de todas as dimensões foram recalculados sobre a "
    "coorte nova."
))
story.append(p(
    "<b>Matéria ampliada (04/11/2026):</b> até então, só as 8 matérias de maior volume tinham categoria "
    "própria, e o 'Outros' de matéria juntava quase metade da coorte (49% do treino da Fase 4), com tempos "
    "muito diferentes entre si — de cerca de 180 dias de mediana (SVA) a mais de 600 (JUROS_ABUSIVOS). O "
    "critério passou a ser objetivo: <b>toda matéria com pelo menos 300 processos</b> na coorte de modelagem "
    f"vira categoria própria, o que dá {N_TOP_MATERIA} matérias e cobre {PCT_COBERTURA_MATERIA_FMT}% dos "
    "processos (antes 51%). O mesmo critério aplicado a comarca chegou a ser descartado numa comparação feita "
    "olhando o conjunto de teste e, refeita a escolha sem o teste (backtest, Fase 4, Seção 2.4), foi adotado: "
    f"comarca passou a ter {N_TOP_COMARCA} categorias, cobrindo {PCT_COBERTURA_COMARCA_FMT}% dos processos. "
    f"Competência ({N_TOP_COMP} categorias, cerca de 96% da "
    "coorte) e tipo de ação não mudaram. A referência de matéria segue sendo 'Outros', ainda a categoria mais "
    "frequente, mas agora formada só pelas matérias pequenas."
))
story.append(p(
    "<b>Agravos identificados pelo número CNJ (06/11/2026):</b> parte dos agravos é cadastrada no LexFlow "
    "como processo próprio; eles são reconhecidos pelos quatro últimos dígitos do número CNJ (0000, 9000, 9001 "
    "ou 9002) e passaram a ser excluídos da coorte inteira, junto com a atualização dos dados até 06/11/2026 "
    "(ver Capitulo_Fase2_Resultados.pdf, Seção 2.1)."
))
story.append(p(
    "<b>Escopo NG e LA/AM (09/11/2026):</b> o estudo inteiro cobre só os escritórios NG e LA/AM — o LA/RJ foi "
    f"excluído da própria coorte (.sql oficial). Com o t=0 na distribuição ele tinha {N_RJ_FMT} processos, "
    f"{PCT_RJ_CENS_FMT}% ainda sem desfecho: poucos eventos para estimar qualquer efeito e fora do escopo do "
    "trabalho. Como os modelos desta fase já usavam só NG e LA sobre as mesmas linhas, nenhum número deste "
    "capítulo mudou com a exclusão."
))
story.append(p(
    "Fase, subfase, juiz de 1ª instância e relator de 2ª instância permanecem fora do modelo formal. O motivo é "
    "metodológico, não de disponibilidade de dado: fase e subfase (status processual) refletem o estado "
    "<i>atual</i> do processo — não um atributo fixado na distribuição — e juiz/relator só são preenchidos depois "
    "que a instância correspondente já decidiu o mérito. Tratar essas 4 variáveis como covariáveis de t=0 "
    "introduziria viés de causalidade reversa (lookahead): o modelo aprenderia, por exemplo, que 'processos na "
    "fase X são mais rápidos' quando na verdade X só existe porque o processo já terminou rápido. Essas 4 "
    "dimensões continuam disponíveis como ranking descritivo no dashboard interativo do projeto (seção "
    "'Exploratório'), sempre com a ressalva de que não sustentam leitura causal."
))
story.append(p("2.2 Regressão de Cox", "H2"))
story.append(p(
    "O modelo de Cox estima h(t|X) = h<sub>0</sub>(t)·exp(β·X), em que h<sub>0</sub>(t) é o hazard basal não "
    "especificado e exp(β<sub>i</sub>) é a razão de risco (hazard ratio, HR) associada à covariável X<sub>i</sub> "
    "— HR&gt;1 significa maior velocidade de chegar a qualquer desfecho (tempo mais curto); HR&lt;1, o oposto. "
    "Foi usado um penalizador L2 leve (0,01) para estabilizar categorias de menor volume sem distorcer "
    "materialmente as estimativas."
))
story.append(p("2.3 Riscos competitivos de Fine-Gray", "H2"))
story.append(p(
    "Nenhuma biblioteca Python disponível neste ambiente implementa Fine-Gray nativamente (lifelines tem apenas "
    "Cox causa-específico e o estimador não-paramétrico de Aalen-Johansen; scikit-survival não estava "
    "disponível). O modelo foi implementado por meio da técnica de Cox ponderado por IPCW (inverse probability "
    "of censoring weighting) descrita em GESKUS (2011), matematicamente equivalente à formulação original de "
    "Fine &amp; Gray: sujeitos que experimentam um risco concorrente (acordo ou mérito sem proveito/desfavorável, "
    "quando o evento de interesse é mérito favorável com proveito) permanecem artificialmente no conjunto de "
    "risco após seu próprio evento, com peso temporal w(t) = G(t)/G(T<sub>i</sub>), em que G é a curva de "
    "Kaplan-Meier da distribuição de censura (censura tratada como evento; qualquer desfecho real tratado como "
    "censura, para essa estimativa auxiliar). O horizonte de acompanhamento foi truncado em 1.800 dias (mesmo "
    "horizonte usado no dashboard interativo) por censura administrativa, evitando que uma cauda rala de poucos "
    "processos muito antigos inflasse artificialmente o custo computacional."
))
story.append(p(
    "<b>Validação da implementação:</b> antes de aplicar aos dados reais, a implementação foi testada contra uma "
    "propriedade matemática exata — na ausência de qualquer risco competitivo (todo sujeito é 'evento de "
    "interesse' ou censurado), o peso IPCW é trivialmente 1 para todos, e o Fine-Gray deve coincidir exatamente "
    "com um Cox padrão ajustado nos mesmos dados. Em dado simulado (n=600, 2 covariáveis), a diferença absoluta "
    "entre os coeficientes dos dois ajustes foi menor que 2×10<super>-6</super> (seis ordens de grandeza abaixo "
    "de qualquer diferença praticamente relevante) — confirmando a corretude da implementação antes do uso na "
    "base real. Essa validação não precisou ser refeita nesta atualização: acrescentar covariáveis não muda a "
    "lógica de ponderação IPCW, só o vetor X."
))
story.append(CondPageBreak(6 * cm))

# ---------------------------------------------------------------------------
# 3. RESULTADOS - COX
# ---------------------------------------------------------------------------
story.append(p("3. Resultados — Regressão de Cox", "H1"))
story.append(p("3.1 Ajuste geral", "H2"))
story.append(tabela_indicadores([
    ("N (processos)", N_MODELO_FMT),
    ("Eventos observados", n_pct(EVENTOS_COX)),
    ("Censurados", n_pct(CENSURADOS_COX)),
    ("Índice de concordância (C-index)", CINDEX_FMT),
    ("Log-likelihood", dec2(LOGLIK_COX)),
    ("AIC", dec2(AIC_COX)),
]))
story.append(Spacer(1, 6))
story.append(p(
    f"Um C-index de {CINDEX_FMT} indica capacidade discriminativa moderada — acima do acaso (0,5) e de todas "
    "as versões anteriores: 0,644 na primeira (sem comarca/competência), 0,674 com comarca/competência e t=0 na "
    f"contratação, {CINDEX_041126_8MAT_FMT} com t=0 na distribuição e 8 matérias (coorte de 04/11/2026) e "
    f"{CINDEX_041126_24MAT_FMT} com as {N_TOP_MATERIA} matérias na mesma coorte de 04/11, {CINDEX_091126_24_8_FMT} "
    f"com {N_TOP_MATERIA} matérias e 8 comarcas na coorte de 09/11 e {CINDEX_FMT} com as {N_TOP_COMARCA} comarcas "
    "(versão atual). A troca do marco zero "
    "mudou bastante os números descritivos (Fase 2), mas quase nada a capacidade do modelo de ordenar quem "
    "resolve primeiro; o ganho recente vem das categorias ampliadas. <b>Atenção:</b> este C-index é medido nos "
    "mesmos dados usados no ajuste (in-sample) — mais categorias quase sempre o aumentam. Na avaliação fora da "
    "amostra da Fase 4, com split temporal, o Cox com mais categorias praticamente <i>não</i> melhora — a "
    "leitura completa está naquele capítulo. Ainda assim, o "
    "índice permanece distante de um modelo fortemente preditivo (haveria de superar ~0,7 para isso) — o que é "
    "esperado, já que decisões judiciais individuais (identidade do juiz, complexidade específica do caso) "
    "seguem fora do modelo por desenho (ver Seção 2.1)."
))
story.append(p("3.2 Hazard ratios", "H2"))
story.append(tabela_hr(montar_linhas(COX_DESTAQUE, cox_rows)))
story.append(p(
    f"Tabela completa — as {N_COVARIAVEIS_COX} covariáveis do modelo (mesmos números em "
    "dados/fase3_cox_hazard_ratios.csv). HR&gt;1 = tempo até qualquer desfecho mais curto que a referência; "
    "HR&lt;1 = mais longo.",
    "CorpoTabelaNota",
))
story.append(p("3.3 Suposição de riscos proporcionais", "H2"))
story.append(p(
    f"O teste de Schoenfeld (GRAMBSCH; THERNEAU, 1994) rejeitou a suposição de riscos proporcionais para a "
    f"maioria das covariáveis ({N_COVARIAVEIS_PH_VIOLADAS} das {N_COVARIAVEIS_COX}; na primeira versão do "
    "modelo eram 13 das 18 — proporção semelhante, mesmo com mais covariáveis). Isso não invalida as estimativas "
    "pontuais de HR como resumo médio do efeito ao longo do tempo, mas indica que o efeito real de cada "
    "covariável provavelmente varia conforme o processo avança — por exemplo, o efeito de 'log(valor_causa)' "
    "pode ser mais forte nos primeiros meses e esmaecer depois. Esse padrão é parcialmente um artefato esperado "
    "do tamanho amostral: o teste de Schoenfeld ganha poder estatístico com N, detectando desvios de "
    "proporcionalidade pequenos demais para importar na prática junto com desvios genuínos. Esse é exatamente "
    "o tipo de limitação que motiva comparar este modelo paramétrico com uma alternativa não-paramétrica livre "
    "da suposição de proporcionalidade — objeto da Fase 4 (Random Survival Forest)."
))
story.append(CondPageBreak(6 * cm))

# ---------------------------------------------------------------------------
# 4. RESULTADOS - FINE-GRAY
# ---------------------------------------------------------------------------
story.append(p("4. Resultados — Riscos Competitivos de Fine-Gray", "H1"))
fg_concorrentes = FG_CONCORRENTE_ACORDO + FG_CONCORRENTE_MERITO_DESFAV


story.append(p(
    f"Evento de interesse: mérito favorável com proveito econômico ({milhar(FG_EVENTO_INTERESSE)} processos). "
    f"Riscos concorrentes: acordo ({milhar(FG_CONCORRENTE_ACORDO)}) e mérito sem proveito ou desfavorável "
    f"({milhar(FG_CONCORRENTE_MERITO_DESFAV)}). Censurados: {milhar(FG_CENSURADOS)}. O dataset ponderado (IPCW) "
    f"expandido para o ajuste teve {milhar(FG_LONG_LINHAS)} linhas, construído a partir dos {N_MODELO_FMT} "
    "sujeitos originais."
))
story.append(KeepTogether(tabela_indicadores([
    ("N (processos)", N_MODELO_FMT),
    ("Eventos de interesse", n_pct(FG_EVENTO_INTERESSE)),
    ("Riscos concorrentes", n_pct(fg_concorrentes)),
    ("Censurados", n_pct(FG_CENSURADOS)),
    ("Log-likelihood (Cox ponderado)", dec2(FG_LOGLIK)),
])))
story.append(Spacer(1, 6))
story.append(CondPageBreak(5 * cm))
story.append(Paragraph("4.1 Hazard ratios de subdistribuição", ParagraphStyle("H2_solto", parent=styles["H2"], keepWithNext=0)))
story.append(tabela_hr(montar_linhas(FG_DESTAQUE, fg_rows)))
story.append(p(
    "HR de subdistribuição &gt;1 = maior velocidade de chegar especificamente ao mérito favorável com proveito "
    "econômico (não apenas 'a qualquer desfecho', diferente da Tabela da Seção 3.2); &lt;1 = menor velocidade. "
    f"Tabela completa — as {N_COVARIAVEIS_COX} covariáveis do modelo (mesmos números em "
    "dados/fase3_finegray_subdist_hr.csv).",
    "CorpoTabelaNota",
))
story.append(CondPageBreak(6 * cm))

# ---------------------------------------------------------------------------
# 5. DISCUSSAO
# ---------------------------------------------------------------------------
story.append(p("5. Discussão", "H1"))
story.append(p(
    "O achado mais nítido desta fase segue sendo 'Cumprimento de Sentença': HR de subdistribuição de "
    f"{hr(fg_rows, 'tipo_CUMPRIMENTO_DE_SENTENÇA')} — {DESC_CUMPR} de velocidade para chegar a um mérito "
    "favorável com proveito econômico, comparado à referência. Isso é coerente com a própria natureza da "
    "classificação: um processo rotulado como 'Cumprimento de Sentença' já teve, por definição, uma fase de "
    "conhecimento resolvida — o modelo está, em parte, capturando esse estágio processual mais avançado "
    "embutido na própria variável tipo de ação, não um efeito causal independente."
))
story.append(p(
    "O padrão mais consistente do capítulo é o contraste entre 'lentidão geral' (tempo até QUALQUER desfecho, "
    "Seção 3.2) e 'lentidão para o sucesso' (tempo até especificamente o desfecho favorável, Seção 4.1). Com o "
    "t=0 na distribuição, ele aparece de forma mais nítida em <b>competência</b> e em <b>APELAÇÃO CÍVEL</b>:"
))
story.append(lista([
    f"Vara Cível: HR Cox={hr(cox_rows, 'comp_Vara_Cível')} (bem mais lenta que Juizado Especial Cível para "
    f"qualquer desfecho), mas HR de subdistribuição={hr(fg_rows, 'comp_Vara_Cível')} — para o desfecho "
    "favorável, a diferença é muito menor.",
    f"Turma Recursal: HR Cox={hr(cox_rows, 'comp_Turma_Recursal')} (ligeiramente mais rápida que a referência "
    f"para qualquer desfecho), mas HR de subdistribuição={hr(fg_rows, 'comp_Turma_Recursal')} "
    f"({pp(fg_rows, 'comp_Turma_Recursal')}) — mais lenta para chegar ao sucesso. O sinal se inverte.",
    f"APELAÇÃO CÍVEL: HR Cox={hr(cox_rows, 'tipo_APELAÇÃO_CÍVEL')} ({pp(cox_rows, 'tipo_APELAÇÃO_CÍVEL')}, "
    f"sem diferença para qualquer desfecho), mas HR de subdistribuição={hr(fg_rows, 'tipo_APELAÇÃO_CÍVEL')} "
    f"({pp(fg_rows, 'tipo_APELAÇÃO_CÍVEL')}) — não tramita mais devagar, mas demora mais para virar mérito "
    "favorável.",
]))
story.append(p(
    "<b>Mudança de leitura em relação à versão de 20/10/2026:</b> naquela versão, o caso mais limpo do padrão "
    "era o <b>escritório</b> — NG não era significativamente mais lento que LA no Cox, mas era no Fine-Gray — e "
    "APELAÇÃO não mostrava contraste nenhum. Com o t=0 na distribuição, NG passa a ser mais lento nos dois "
    f"modelos (HR Cox={hr(cox_rows, 'esc_NG')}, {pp(cox_rows, 'esc_NG')}; HR de "
    f"subdistribuição={hr(fg_rows, 'esc_NG')}, {pp(fg_rows, 'esc_NG')}). O efeito continua um pouco mais forte "
    "para o desfecho favorável, mas deixou de ser um contraste 'presente num modelo, ausente no outro'. A "
    "explicação plausível (não testada aqui) é que parte do que parecia uma dificuldade específica do NG em "
    "converter casos em sucesso fosse efeito de medir o tempo a partir da contratação, que não coincide com o "
    "início da tramitação. Já APELAÇÃO, que antes não mostrava contraste, agora mostra: o mesmo padrão "
    "aparecendo e sumindo em variáveis diferentes conforme a definição do relógio é um aviso de que esses "
    "efeitos são sensíveis à especificação e não devem ser lidos como causais."
))
_mats = {k: v for k, v in cox_rows.items() if k.startswith("mat_")}
_mais_rapidas_cox = sorted(_mats, key=lambda k: -float(cox_rows[k]["exp(coef)"]))[:3]
_fg_sucesso = [k for k in sorted(_mats, key=lambda k: -float(fg_rows[k]["exp(coef)"]))
               if float(fg_rows[k]["exp(coef)"]) > 1.15 and float(fg_rows[k]["p"]) < 0.05]
story.append(p(
    "Matéria, agora com " + str(N_TOP_MATERIA) + " categorias, mostra o mesmo padrão em escala maior. No Cox, "
    "as matérias mais rápidas do modelo para qualquer desfecho incluem categorias que antes estavam escondidas "
    "em 'Outros' — " + ", ".join(f"{rotulo_cov(k).replace(' (matéria)', '')} (HR={hr(cox_rows, k)})" for k in _mais_rapidas_cox)
    + " —, mas no Fine-Gray quase todas ficam perto de 1 (" + ", ".join(
        f"{rotulo_cov(k).replace(' (matéria)', '')} {hr(fg_rows, k)}" for k in _mais_rapidas_cox)
    + "): resolvem rápido, mas não necessariamente a favor. As matérias que de fato chegam mais rápido ao "
    "mérito favorável com proveito são outras: " + ", ".join(
        f"{rotulo_cov(k).replace(' (matéria)', '')} (HR de subdistribuição={hr(fg_rows, k)})" for k in _fg_sucesso)
    + f". No outro extremo, SLN e MORA seguem as mais lentas nos dois modelos (HR Cox={hr(cox_rows, 'mat_SLN')} "
    f"e {hr(cox_rows, 'mat_MORA')}), coerente com o ranking descritivo da Fase 2. Era exatamente essa "
    "heterogeneidade que o 'Outros' antigo apagava."
))
story.append(p(
    "Comarca revela uma heterogeneidade genuína que a Fase 2 não conseguia enxergar (a variável nem existia no "
    f"modelo). No Cox, com as {N_TOP_COMARCA} comarcas, várias do interior são <i>mais rápidas</i> que MANAUS para "
    f"qualquer desfecho — {_lista_hr(COM_RAPIDAS, cox_rows)} —, enquanto "
    f"{_lista_hr(COM_LENTAS, cox_rows)} são mais lentas"
    + (f" e {', '.join(_rotulo_com(k) for k in COM_NEUTRAS)} não diferem da referência" if COM_NEUTRAS else "")
    + ". Várias das comarcas que só ganharam categoria própria agora aparecem nos dois extremos — eram "
    "justamente as diferenças que o 'Outros' de comarca apagava. No Fine-Gray, "
    + (("as comarcas mais rápidas mantêm o efeito") if len(COM_RAPIDAS_FG_MANTEM) == len(COM_RAPIDAS) else
       (f"nenhuma das {len(COM_RAPIDAS)} comarcas mais rápidas mantém o efeito para o mérito favorável — "
        "todas perdem significância ou ficam abaixo de 1") if not COM_RAPIDAS_FG_MANTEM else
       (f"só {len(COM_RAPIDAS_FG_MANTEM)} das {len(COM_RAPIDAS)} comarcas mais rápidas mantêm o efeito para o "
        "mérito favorável; as demais perdem significância ou ficam abaixo de 1"))
    + (f" (ex.: {_rotulo_com(_ex_fg)}, HR de subdistribuição={hr(fg_rows, _ex_fg)})" if _ex_fg else "")
    + " — o mesmo padrão geral-vs-específico: comarca afeta principalmente a velocidade até QUALQUER desfecho "
    "(o que inclui mérito desfavorável e extinção), não a velocidade até o sucesso. A leitura deve ser "
    "cautelosa: o N "
    "por comarca fora de Manaus é modesto e os intervalos de confiança são largos."
))

# ---------------------------------------------------------------------------
# 6. LIMITACOES
# ---------------------------------------------------------------------------
story.append(p("6. Limitações", "H1"))
story.append(lista([
    "Suposição de riscos proporcionais violada para a maioria das covariáveis no modelo de Cox "
    f"({N_COVARIAVEIS_PH_VIOLADAS} de {N_COVARIAVEIS_COX}) — os HRs reportados são uma média ao longo do "
    "tempo, não necessariamente um efeito constante.",

    "Ausência de variância robusta (sandwich) no Fine-Gray: a implementação de CoxTimeVaryingFitter usada não "
    "suporta erro-padrão robusto combinado com pesos neste momento (limitação da versão instalada da "
    "biblioteca); os intervalos de confiança reportados usam o erro-padrão não-robusto, que tende a ser "
    "ligeiramente otimista (mais estreito) do que o IPCW exigiria rigorosamente.",

    "Fase, subfase, juiz (1ª instância) e relator (2ª instância) ficam fora do modelo formal por serem "
    "conhecidos apenas após o desfecho de mérito na instância correspondente (ver Seção 2.1) — candidatos a "
    "uma análise causal mais cuidadosa (ex.: efeito fixo de julgador, com desenho que evite viés de seleção) "
    "em trabalho futuro, fora do escopo desta fase.",

    "Categoria 'Outros' de comarca e competência agrega heterogeneidade real: competências como 'Juizado "
    "Especial da Fazenda Pública' ou 'Juizado Especial Federal' têm volume pequeno demais (pouco mais de 100 "
    "processos cada na coorte NG+LA) para uma categoria própria robusta e caem todas em comp_Outros, que "
    f"aparece como a mais lenta do modelo (HR Cox={hr(cox_rows, 'comp_Outros')}).",

    "Estudo restrito a NG e LA/AM (LA/RJ excluído da coorte — ver Seção 2.1): os coeficientes de escritório "
    "comparam apenas NG vs. LA, e os resultados não se generalizam para o RJ.",

    "Horizonte truncado em 1.800 dias no Fine-Gray — processos com follow-up além disso são tratados como "
    "censurados administrativamente naquele ponto, por tratabilidade computacional.",

    "Sensibilidade à definição do relógio: a troca do t=0 (contratação → distribuição) mudou quais "
    "covariáveis mostram o contraste 'geral vs. sucesso' (Seção 5), mesmo com o C-index praticamente igual. "
    "Os HRs devem ser lidos como associações dentro desta especificação, não como efeitos estáveis.",

    f"Categorias de volume muito pequeno geram estimativas instáveis: EMBARGOS (tipo de ação) tem HR Cox="
    f"{hr(cox_rows, 'tipo_EMBARGOS')} e HR de subdistribuição de {hr(fg_rows, 'tipo_EMBARGOS')} — nenhum "
    "processo dessa categoria teve o evento de interesse, e o coeficiente diverge (o penalizador L2 só o "
    "mantém finito). Esses valores não devem ser interpretados.",

    "Qualidade de dado como processo contínuo: quatro correções (padronização de tipo_acao, regra de "
    "precedência da sentença anulada, marco zero na distribuição, agravos identificados pelo número CNJ) foram "
    "descobertas depois da primeira rodada do modelo, não "
    "antes. É razoável supor que outras inconsistências ainda não identificadas existam na base — a triagem de "
    "qualidade de dado (Inconsistencias_Datas_Processo.csv) é tratada como um processo recorrente, não uma "
    "etapa única, e futuras rodadas do modelo podem continuar incorporando correções.",
]))

# ---------------------------------------------------------------------------
# 7. SINTESE
# ---------------------------------------------------------------------------
story.append(p("7. Síntese e encaminhamento para a Fase 4", "H1"))
story.append(p(
    "A Fase 3 soma, ao longo das suas versões, duas melhorias metodológicas (comarca e competência como "
    f"covariáveis plenas; matéria e comarca ampliadas para {N_TOP_MATERIA} e {N_TOP_COMARCA} categorias) e quatro correções de dado "
    "(padronização do catálogo tipo_acao; precedência mérito para 'sentença anulada'; t=0 na distribuição em "
    "vez da contratação; agravos identificados pelo número CNJ). O C-index in-sample foi de 0,644 (versão "
    f"original) para 0,674 com comarca/competência, {CINDEX_041126_8MAT_FMT} com o novo marco zero e "
    f"{CINDEX_FMT} na versão atual. O que mudou com o novo marco zero foi a leitura dos HRs: o padrão "
    "'lentidão geral ≠ lentidão para o sucesso' continua presente, mas hoje se apoia em competência (Vara "
    "Cível, Turma Recursal) e em APELAÇÃO CÍVEL, e não mais no escritório, que passou a ser mais lento nos dois "
    f"modelos. O Cox estabelece o piso de comparação para a Fase 4 — lá medido fora da amostra, com split "
    "temporal: avaliar se "
    "modelos não-paramétricos (Random Survival Forest, XGBoost-AFT), livres da suposição de riscos "
    "proporcionais e capazes de capturar interações não especificadas manualmente, conseguem superá-lo — e "
    "por quanto."
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(p("Referências", "H1"))
for ref in [
    "COX, D. R. Regression Models and Life-Tables. <i>Journal of the Royal Statistical Society: Series B</i>, v. 34, n. 2, p. 187-220, 1972.",
    "FINE, J. P.; GRAY, R. J. A Proportional Hazards Model for the Subdistribution of a Competing Risk. <i>Journal of the American Statistical Association</i>, v. 94, n. 446, p. 496-509, 1999.",
    "GESKUS, R. B. Cause-Specific Cumulative Incidence Estimation and the Fine and Gray Model Under Both Left Truncation and Right Censoring. <i>Biometrics</i>, v. 67, n. 1, p. 39-49, 2011.",
    "GRAMBSCH, P. M.; THERNEAU, T. M. Proportional Hazards Tests and Diagnostics Based on Weighted Residuals. <i>Biometrika</i>, v. 81, n. 3, p. 515-526, 1994.",
    "HARRELL, F. E. et al. Evaluating the Yield of Medical Tests. <i>JAMA</i>, v. 247, n. 18, p. 2543-2546, 1982. (Índice de concordância.)",
    "KAPLAN, E. L.; MEIER, P. Nonparametric Estimation from Incomplete Observations. <i>Journal of the American Statistical Association</i>, v. 53, n. 282, p. 457-481, 1958.",
]:
    story.append(p(ref, "Referencia"))

story.append(Spacer(1, 10))
story.append(p(
    "Este capítulo complementa o Capitulo_Fase2_Resultados.pdf e o Plano_TCC_Luiz.pdf, na mesma pasta de "
    "pesquisa. Scripts completos e reprodutíveis em scripts/fase3_cox.py, scripts/fase3_finegray.py, "
    "scripts/validar_finegray.py e scripts/gerar_capitulo_fase3.py (este documento).",
    "Corpo",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Fase 3: Cox Proportional Hazards e Fine-Gray",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
