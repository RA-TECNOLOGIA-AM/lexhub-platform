# -*- coding: utf-8 -*-
"""
Gera Apendice_A_Qualidade_dos_Dados.pdf a partir de dados/qualidade_dados.json
(scripts/qualidade_dados.py), da foto congelada e de fase3_cox_resumo.json - nada digitado.
Mesmo padrao visual dos capitulos.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_qualidade_dados.py
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
OUT_PDF = f"{BASE_DIR}/Apendice_A_Qualidade_dos_Dados.pdf"
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
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Apêndice A: Qualidade dos dados")
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



from coorte_comum import carregar_coorte  # noqa: E402
import fase6_acordos  # noqa: E402

Q = ler("qualidade_dados.json")
F = Q["estudo"]           # foto final - a que o estudo usa (inventario, etiquetas)
E, A = Q["anterior"], F   # antes/depois p/ o efeito das correcoes (secao 3)
N = F["n_processos"]
D_ANT, D_FIN = (pd.Timestamp(Q["referencia"][k]).strftime("%d/%m/%Y") for k in ("anterior", "estudo"))
COX3 = ler("fase3_cox_resumo.json")
N_SEM_VALOR = COX3["n_descartados_valor_causa"]
_coorte = carregar_coorte()
N_DUR_ZERO = int((_coorte["duracao_dias_e1"] == 0).sum())
N_COORTE = len(_coorte)
MUD_A, MUD_S = Q["mudancas_acordao_d"], Q["mudancas_sentenca_d"]
with contextlib.redirect_stdout(io.StringIO()):
    _pre, _ = fase6_acordos.preparar()
_tri = _pre.assign(_t=pd.to_datetime(_pre["data_resolucao"]).dt.to_period("Q")).groupby("_t")["y"].agg(["size", "mean"])
_tri = _tri[_tri["size"] >= 500]
PICO_PRE, PICO_Q = pct(_tri["mean"].max(), 0), _tri["mean"].idxmax()
ULT_PRE = pct(_tri["mean"].iloc[-1], 1)
ULT_Q = _tri.index[-1]


N_FORA_ORDEM = (F["acordao_antes_da_sentenca"] + F["sentenca_antes_da_distribuicao"]
                + F["acordao_antes_da_distribuicao"] + F["datas_no_futuro"])  # limite superior (pode haver sobreposicao)


def pc(n, base=N):
    return pct(n / base, 2 if 0 < n / base < 0.001 else 1)


def data_br(iso):
    return pd.Timestamp(iso).strftime("%d/%m/%Y")


def red(chave):
    a, e = A[chave], E[chave]
    return "—" if e == 0 else f"{'+' if a - e > 0 else ''}{pct((a - e) / e, 0)}"


story = []
story.append(Spacer(1, 3 * cm))
story.append(p("Apêndice A — Qualidade dos dados", "TituloCapa"))
story.append(p("Problemas de cadastro que afetam o estudo, como foram tratados e o efeito das correções na origem",
               "SubtituloCapa"))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Todas as contagens se referem aos {milhar(N)} processos da coorte de modelagem (escritórios NG e LA/AM) "
    "presentes nas duas fotos, "
    f"em duas fotos dos mesmos processos: a <b>foto final</b> (extração de {D_FIN}, usada em todas as fases) e a "
    f"<b>foto anterior</b> ({D_ANT}, usada nas versões intermediárias), entre as quais houve correções feitas "
    "diretamente no LexFlow. Gerado por scripts/qualidade_dados.py e scripts/gerar_capitulo_qualidade_dados.py.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

story.append(p("1. Por que olhar a qualidade dos dados", "H1"))
story.append(p(
    "Os modelos das Fases 3 a 6 aprendem a partir de datas e códigos digitados no sistema de gestão do escritório, "
    "não de uma base preparada para pesquisa. Um acórdão sem data não vira evento; uma sentença com data mas sem "
    "resultado entra no prazo, mas não na taxa de procedência; uma etiqueta de acordo com a fase errada muda o "
    "que se considera acordo pré ou pós-sentença. Este apêndice mede esses problemas, registra como cada um foi "
    "tratado e mostra o efeito das primeiras correções feitas na origem."
))

story.append(p("2. Inventário dos problemas", "H1"))
story.append(p(
    f"A tabela mostra cada problema na foto final (a do estudo) e, para comparação, na foto de {D_ANT}. A última coluna resume como o "
    "estudo lidou com cada caso."
))
linhas = [["Problema", "Estudo (foto final)", f"Foto {D_ANT[:5]}", "Tratamento no estudo"]]
def L(rot, chave, trat, base=N):
    linhas.append([rot, f"{milhar(F[chave])} ({pc(F[chave], base)})", milhar(E[chave]), trat])
L("Acórdão de mérito sem data", "acordao_merito_sem_data",
  "não vira evento de 2º grau; fora da validação do modelo 2G (que precisa da data)", F["acordao_merito_total"])
L("Sentença com data, sem resultado de mérito", "sentenca_com_data_sem_resultado",
  "conta para o prazo; fica fora da taxa de procedência 1G")
L("Sentença com resultado, sem data", "sentenca_com_resultado_sem_data",
  "conta na procedência; data imputada pelo evento do estágio 1 quando preciso")
L("Acórdão de mérito sem sentença registrada", "acordao_merito_sem_sentenca",
  f"categoria própria (\"sem sentença\") no modelo 2G; {milhar(F['acordao_merito_sem_sentenca_tipo_2g'])} são "
  "recurso inominado ou apelação, em que isso é esperado")
L("Acórdão anterior à sentença (exceto anulação)", "acordao_antes_da_sentenca", "mantido; impacto pequeno")
L("Sentença anterior à distribuição", "sentenca_antes_da_distribuicao",
  "mantida; o evento do estágio 1 não usa essa data (a coorte descarta durações negativas)")
L("Acórdão anterior à distribuição", "acordao_antes_da_distribuicao", "idem")
L("Data no futuro (sentença, acórdão ou acordo)", "datas_no_futuro", "descartada como erro nos modelos da Fase 6")
linhas.append(["Desfecho no mesmo dia da distribuição", f"{milhar(N_DUR_ZERO)} ({pc(N_DUR_ZERO, N_COORTE)})", "—",
               "mantido (duração zero); suspeito de data copiada"])
L("Sem matéria", "sem_materia", "categoria \"Não informada\" (grupo \"Outros\" no modelo)")
L("Sem comarca", "sem_comarca", "idem")
L("Sem competência", "sem_competencia", "idem")
L("Sem tipo de ação (inclui agravo e mandado de segurança limpos)", "sem_tipo_acao", "grupo \"Outros\"")
linhas.append(["Sem valor de causa", milhar(N_SEM_VALOR), "—", "excluídos da modelagem (Fase 3)"])
story.append(tabela(linhas, [5.4 * cm, 2.6 * cm, 1.6 * cm, 7.4 * cm]))
story.append(p(
    "Percentuais sobre os processos da coorte de modelagem, exceto acórdão sem data (sobre os acórdãos de mérito) "
    f"e desfecho no mesmo dia (sobre a coorte inteira). \"Foto {D_ANT[:5]}\" = mesmos processos na foto anterior.",
    "CorpoTabelaNota",
))

story.append(p("2.1 Etiquetas de acordo", "H2"))
story.append(p(
    "Acordos são registrados de duas formas no LexFlow: a data de acordo fechado e etiquetas (\"ACORDO\", \"ACORDO "
    "PRÉ-SENTENÇA\", \"ACORDO PÓS-SENTENÇA\"). Quando o processo tem as duas e a etiqueta diz a fase, é possível "
    "conferir uma contra a outra:"
))
story.append(tabela([
    ["Etiqueta", "Com data de acordo", "Fase da etiqueta discorda da data", "%"],
    ["PRÉ-SENTENÇA", milhar(F["etiqueta_PRE_com_data"]), milhar(F["etiqueta_PRE_discorda_data"]),
     pct(F["etiqueta_PRE_discorda_data"] / F["etiqueta_PRE_com_data"], 0)],
    ["PÓS-SENTENÇA", milhar(F["etiqueta_POS_com_data"]), milhar(F["etiqueta_POS_discorda_data"]),
     pct(F["etiqueta_POS_discorda_data"] / F["etiqueta_POS_com_data"], 0)],
], [4 * cm, 3.6 * cm, 5.4 * cm, 2 * cm]))
story.append(Spacer(1, 6))
story.append(p(
    f"Quase metade das etiquetas \"PÓS-SENTENÇA\" discorda da data. O estudo usa a <b>data</b> sempre que ela "
    f"existe; só os {milhar(F['acordo_so_etiqueta'])} acordos sem data (apenas etiqueta) têm a fase definida pelo "
    "nome da etiqueta ou, se genérica, pela situação do processo (sem sentença de mérito = pré; com sentença e sem "
    f"acórdão = pós). Outros {milhar(F['acordo_so_data'])} acordos têm data e nenhuma etiqueta."
))

story.append(p("3. Efeito das correções na origem", "H1"))
story.append(p(
    f"Entre a foto de {D_ANT} e a foto final ({D_FIN}) foram corrigidas, no LexFlow, datas de acórdão de "
    "processos do NG. Comparando os mesmos processos nas duas fotos:"
))
story.append(lista([
    f"<b>Datas de acórdão:</b> {milhar(MUD_A['preenchidas'])} preenchidas, {milhar(MUD_A['apagadas'])} apagadas e "
    f"{milhar(MUD_A['alteradas'])} alteradas.",
    f"<b>Acórdãos de mérito sem data:</b> de {milhar(E['acordao_merito_sem_data'])} para "
    f"{milhar(A['acordao_merito_sem_data'])} ({red('acordao_merito_sem_data')}). Os acórdãos de mérito registrados "
    f"passaram de {milhar(E['acordao_merito_total'])} para {milhar(A['acordao_merito_total'])}.",
    f"<b>Datas de sentença:</b> {milhar(MUD_S['preenchidas'])} preenchidas e {milhar(MUD_S['alteradas'])} alteradas.",
]))
story.append(p(
    "Essas correções já estão nos números das Fases 2 a 6, que foram reprocessadas sobre a foto final. É também "
    "um resultado do próprio trabalho: medir a qualidade dos dados levou a correções na base de origem do "
    "escritório."
))

story.append(p("4. Mudanças ao longo do tempo", "H1"))
story.append(p(
    "Dois fenômenos não são erros de cadastro, mas afetam diretamente a modelagem e foram identificados ao longo "
    "do estudo. O primeiro é a <b>aceleração dos processos</b>: a mediana de Kaplan-Meier até o primeiro desfecho "
    "cai ano a ano pela data de distribuição:"
))
T = Q["tendencias_estudo"]
story.append(tabela(
    [["Ano de distribuição", "Processos", "% ainda sem desfecho", "Mediana até o desfecho (dias)"]] +
    [[str(t["ano"]), milhar(t["n"]), pct(t["pct_censurado"], 0),
      milhar(t["mediana_km_dias"]) if t["mediana_km_dias"] is not None else "não atingida"] for t in T],
    [4 * cm, 3 * cm, 4 * cm, 5 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "Para os anos mais recentes o acompanhamento é mais curto, mas a mediana de Kaplan-Meier já trata a censura. "
    "Esse movimento motivou incluir o ano de distribuição no XGBoost-AFT (Fase 4) e exige retreino periódico. O "
    f"segundo fenômeno são as <b>campanhas de acordo</b>: a taxa de acordo pré-sentença chegou a {PICO_PRE} no "
    f"{PICO_Q.quarter}º trimestre de {PICO_Q.year} e estava em {ULT_PRE} no trimestre mais recente "
    f"({ULT_Q.quarter}º de {ULT_Q.year}, ainda parcial). Isso depende da política do escritório, não das características do processo — por isso a "
    "previsão de acordo pré-sentença é tratada como teto provável (Fase 6)."
))

story.append(CondPageBreak(5 * cm))
story.append(p("5. Recomendações para o cadastro", "H1"))
story.append(lista([
    "Exigir o resultado de mérito ao registrar uma sentença, e a data ao registrar um acórdão — os dois maiores "
    "volumes do inventário.",
    "Validar a ordem das datas no formulário (distribuição ≤ sentença ≤ acórdão, exceto anulação) e bloquear "
    "datas no futuro.",
    "Derivar a fase da etiqueta de acordo automaticamente da data do acordo, em vez de escolher a etiqueta à mão.",
    "Tornar obrigatórios matéria, comarca, competência e valor de causa no cadastro do processo.",
    "Manter este diagnóstico como rotina: o script compara qualquer foto com os dados atuais e mostra o efeito "
    "de cada rodada de correção.",
]))

story.append(p("6. Síntese", "H1"))
story.append(p(
    "Os problemas mais volumosos são de <b>ausência</b> (sentença sem resultado, acórdão sem data, campos "
    "categóricos vazios), não de valores errados; datas fora de ordem ou no futuro são raras "
    f"({milhar(N_FORA_ORDEM)} processos, {pc(N_FORA_ORDEM)}). "
    "O estudo tratou cada caso de forma explícita e conservadora, e a primeira rodada de correções na origem "
    f"reduziu em {red('acordao_merito_sem_data').lstrip('-')} os acórdãos de mérito sem data. As etiquetas de "
    "acordo são a fonte menos confiável e foram usadas só quando não havia data."
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Apêndice A: Qualidade dos dados",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
