# -*- coding: utf-8 -*-
"""
Gera Capitulo_Fase2_Resultados.pdf (analise exploratoria + Kaplan-Meier + log-rank)
a partir de dados/fase2_numeros.json (gerado por scripts/calcular_fase2.py).

Reconstruido em 20/10/2026: o script original que gerou a primeira versao deste
capitulo (13/10/2026) nao foi salvo - este arquivo passa a ser a fonte
reprodutivel daqui pra frente. Reescrito porque o catalogo tipo_acao do LexFlow
foi padronizado (mesma correcao documentada em gerar_capitulo_fase3.py) e a
regra de precedencia mérito recebeu a correcao da "sentenca anulada" - ambas
mudam os numeros e os nomes de categoria deste capitulo.

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_capitulo_fase2.py
(depois de rodar scripts/calcular_fase2.py, se a coorte tiver mudado)
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import json
import math

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
OUT_PDF = f"{BASE_DIR}/Capitulo_Fase2_Resultados.pdf"

with open(f"{BASE_DIR}/dados/fase2_numeros.json", encoding="utf-8") as f:
    NUM = json.load(f)

# ---------------------------------------------------------------------------
# Estilos (mesmo padrao visual do capitulo da Fase 3)
# ---------------------------------------------------------------------------
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
styles.add(ParagraphStyle(name="Referencia", fontSize=9.5, leading=14, fontName="Helvetica", leftIndent=14, firstLineIndent=-14, spaceAfter=6))

COR_CABECALHO_TABELA = colors.HexColor("#2d3142")
COR_LINHA_ALT = colors.HexColor("#f2f2f5")


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis - Fase 2: Análise Exploratória e Kaplan-Meier")
    canvas.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


def p(texto, estilo="Corpo"):
    return Paragraph(texto, styles[estilo])


def lista(itens):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["Corpo"]), bulletColor=colors.HexColor("#2d3142")) for item in itens],
        bulletType="bullet",
        leftIndent=14,
    )


def tabela_simples(linhas, col_widths, header=True):
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
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO_TABELA),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    for i in range(1 if header else 0, len(data)):
        if (i - (1 if header else 0)) % 2 == 1:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_LINHA_ALT))
    t.setStyle(TableStyle(estilo))
    return t


def fmt_num(v):
    return f"{v:,}".replace(",", ".")


def fmt_dias(v):
    if v is None or (isinstance(v, float) and math.isinf(v)):
        return "não calculável"
    return f"{int(v)} dias"


def fmt_chi2(v):
    return f"{v:.2f}".replace(".", ",")


def fmt_p_cientifico(p_valor):
    """'p = X,XX × 10^-N' (igual ao estilo ja usado no capitulo original), ou 'p < 10^-300' quando
    o float subjacente ja underflowou pra zero (chi2 grande demais pra representar em double)."""
    if p_valor == 0.0:
        return "p &lt; 10<super>-300</super>"
    expoente = math.floor(math.log10(p_valor))
    mantissa = p_valor / (10 ** expoente)
    mantissa_fmt = f"{mantissa:.2f}".replace(".", ",")
    return f"p = {mantissa_fmt} × 10<super>{expoente}</super>"


def tabela_ranking(ranking, titulo_categoria):
    data = [[titulo_categoria, "Mediana (dias)", "N"]]
    for r in ranking:
        data.append([r["categoria"], fmt_dias(r["mediana"]), fmt_num(r["n"])])
    t = Table(data, colWidths=[7.5 * cm, 4.5 * cm, 3.4 * cm], repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO_TABELA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_LINHA_ALT))
    t.setStyle(TableStyle(estilo))
    return t


E1 = NUM["estagio1"]
import sys
sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import carregar_coorte  # noqa: E402
import pandas as _pd  # noqa: E402
# RJ saiu da coorte oficial em 09/11/2026; o tamanho/censura dele vem da mesma extracao
# (09/11 09h14) guardada antes do filtro, so para registrar a decisao no texto.
_coorte_com_rj = _pd.read_parquet(f"{BASE_DIR}/backups_coorte/coorte_sobrevivencia_com_rj_20261109.parquet")
_rj = _coorte_com_rj[_coorte_com_rj["id_escritorio_assinante"] == 27]
N_RJ = len(_rj)
PCT_RJ_CENS_FMT = f"{100 * (_rj['tipo_evento_e1'] == 'CENSURADO').mean():.0f}"
N_COM_RJ = len(_coorte_com_rj)
import csv
with open(f"{BASE_DIR}/dados/fase3_cox_hazard_ratios.csv", encoding="utf-8") as _fh:
    _cox = {r["covariate"]: r for r in csv.DictReader(_fh)}
HR_RI_FMT = f"{float(_cox['tipo_RECURSO_INOMINADO']['exp(coef)']):.3f}".replace(".", ",")
_coorte_atual = carregar_coorte()
PCT_AM_FMT = f"{100 * (_coorte_atual['uf'] == 'AM').mean():.0f}"
N_PB = int((_coorte_atual["uf"] == "PB").sum())
E2 = NUM["estagio2"]

from coorte_comum import DATA_REFERENCIA_BR as DATA_FOTO, carregar_coorte as _cc_carregar  # noqa: E402
DADOS_ATE = _cc_carregar()["distribuicao_d"].max().strftime("%d/%m/%Y")  # ultima distribuicao na foto

story = []

# ---------------------------------------------------------------------------
# CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 3 * cm))
story.append(p("Fase 2 — Resultados", "TituloCapa"))
story.append(p(
    "Análise Exploratória de Sobrevivência Processual: Estatística Descritiva, Curvas de Kaplan-Meier e Teste "
    "de Log-Rank",
    "SubtituloCapa",
))
story.append(Spacer(1, 1.2 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 2 * cm))
story.append(p(
    f"Todos os números deste capítulo foram recalculados sobre a foto da coorte extraída em {DATA_FOTO} "
    f"(distribuições até {DADOS_ATE}; biblioteca lifelines, Python), como conferência independente dos valores "
    "já em produção no dashboard interativo (TypeScript, recalculado no navegador). <b>Mudanças desde a versão "
    "de 20/10/2026:</b> o marco zero (t=0) passou a ser a <b>distribuição</b> do processo, não mais a "
    "contratação; agravos e mandados de segurança deixaram de contar como tipo de ação; e, desde 06/11/2026, "
    "agravos cadastrados como processo próprio são identificados pelo número CNJ e saem da coorte; e, desde "
    "09/11/2026, o estudo cobre só os escritórios NG e LA/AM (o LA/RJ saiu da coorte) — ver Seção 2.1. As "
    "mudanças alteram praticamente todos os números do capítulo.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. INTRODUCAO
# ---------------------------------------------------------------------------
story.append(p("1. Introdução", "H1"))
story.append(p(
    "Este capítulo apresenta os resultados da Fase 2 do projeto: a análise exploratória de sobrevivência sobre "
    "a coorte de processos judiciais extraída do LexFlow. O objetivo desta fase não é ainda produzir um modelo "
    "preditivo multivariado (isso é escopo da Fase 3, com Regressão de Cox e riscos competitivos) — é "
    "responder, de forma descritiva e estatisticamente fundamentada, duas perguntas: quanto tempo um processo "
    "leva até ser resolvido, e em quais categorias (tipo de ação, matéria) esse tempo é sistematicamente maior."
))
story.append(p(
    "A análise foi estruturada em dois estágios, decisão que emergiu durante o próprio desenvolvimento do "
    "trabalho: o Estágio 1 cobre o tempo da distribuição do processo até o primeiro desfecho de mérito ou acordo; o Estágio "
    "2 cobre, apenas para quem venceu a causa com valor a receber, o tempo adicional até o pagamento efetivo. "
    "Tratar os dois estágios separadamente é necessário porque 'ganhar a causa' e 'receber o dinheiro' são "
    "eventos distintos, com dinâmicas temporais próprias — uma taxa de sucesso alta no Estágio 1 não implica "
    "necessariamente um fluxo de caixa rápido."
))

# ---------------------------------------------------------------------------
# 2. METODOLOGIA
# ---------------------------------------------------------------------------
story.append(p("2. Metodologia", "H1"))
story.append(p("2.1 Coorte e limpeza de dados", "H2"))
story.append(p(
    f"A coorte final tem {fmt_num(E1['n'])} processos (LexFlow, escritórios NG e LA/AM), após excluir processos "
    "sob segredo de justiça e processos sem data de distribuição válida. Datas fora da janela plausível (1971 "
    "até a data atual + 2 anos) foram tratadas como inválidas, o que cobre dois bugs reais da base: o "
    "'timestamp zero' (epoch Unix convertido para o fuso de Manaus) e anos de 5 dígitos produzidos por um bug "
    "de formulário em algumas sentenças."
))
story.append(p(
    "<b>Mudança do marco zero (03/11/2026):</b> até a versão anterior deste capítulo, o tempo era contado a "
    "partir da <i>contratação</i> do escritório. A contratação mede a relação comercial com o cliente, não o "
    "tempo processual: ela pode acontecer bem antes ou bem depois do ajuizamento (a mediana da diferença é zero, "
    "mas a cauda é grande para os dois lados). A <i>distribuição</i> é a data real de início da tramitação "
    "judicial e passou a ser o t=0 de todo o projeto. Ela também está preenchida em mais processos, então a "
    "coorte cresceu de cerca de 40 mil para 58.228 processos (versão de 04/11/2026, ainda com o RJ). "
    "Consequência direta naquela versão: a mediana do Estágio 1 passou de 312 para 455 dias, e a taxa de mérito "
    "favorável com proveito, de 16,9% para 13,2%. A diferença mistura dois efeitos que não dá para separar: os "
    "processos que passaram a entrar na coorte e o novo ponto de partida do relógio."
))
story.append(p(
    f"<b>Escopo NG e LA/AM (09/11/2026):</b> com o t=0 na distribuição, o escritório LA/RJ, que na coorte por "
    f"contratação tinha só 11 processos válidos, passou a ter {fmt_num(N_RJ)}, dos quais {PCT_RJ_CENS_FMT}% ainda "
    "sem desfecho. O RJ foi retirado do estudo inteiro — da própria coorte, não só dos modelos —, porque quase "
    "não tem desfechos observados e não faz parte do escopo do trabalho (escritórios NG e LA/AM). Os modelos "
    "das Fases 3 a 5 já usavam só NG e LA, então não mudam. Aqui na Fase 2 o efeito é grande: na mesma extração "
    f"de 09/11/2026, tirar o RJ leva a coorte de {fmt_num(N_COM_RJ)} para {fmt_num(E1['n'])} processos, a "
    "mediana do Estágio 1 de 437 para "
    f"{int(E1['mediana'])} dias e a taxa de mérito favorável com proveito de 13,2% para "
    f"{str(E1['pct_favoravel']).replace('.', ',')}% — os processos do RJ, quase todos recentes e sem desfecho, "
    "alongavam a mediana e diluíam a taxa."
))
story.append(p(
    "<b>Tipos de ação excluídos:</b> agravos (de instrumento, interno cível etc.) e mandados de segurança "
    "deixaram de ser tratados como tipo de ação. Agravos são incidentes processuais dentro de uma causa, não a "
    "ação principal, e o mandado de segurança é um remédio constitucional atípico no perfil dos escritórios. "
    "Processos com esses tipos de ação continuam na coorte (contam na mediana geral e nos rankings por "
    "matéria); só deixam de aparecer nos rankings por tipo de ação. Mesma regra aplicada no dashboard interativo."
))
story.append(p(
    "<b>Agravos cadastrados como processo próprio (06/11/2026):</b> o LexFlow cadastra parte dos agravos como um "
    "processo separado, com número CNJ próprio. Eles são reconhecidos pelos quatro últimos dígitos do número "
    "(código de origem 0000, 9000, 9001 ou 9002) e passaram a ser excluídos da coorte inteira, não só do "
    "ranking por tipo de ação — não são uma ação a ser resolvida, e sim um incidente de outra. A mesma regra "
    "vale para todas as análises do LexFlow em produção. Junto com a atualização dos dados até 06/11/2026, a "
    f"coorte passou de 58.228 (versão de 04/11/2026) para {fmt_num(N_COM_RJ)} processos, ainda contando o RJ."
))
story.append(p("2.2 Definição dos eventos", "H2"))
story.append(p(
    "O Estágio 1 define quatro desfechos possíveis a partir da distribuição: Acordo (compete livremente, "
    "interrompe a tramitação a qualquer momento), Mérito favorável com proveito econômico (sentença/acórdão "
    "procedente ou parcialmente procedente, com valor a receber — segue para o Estágio 2), Mérito sem proveito "
    "ou desfavorável (improcedente, extinto sem mérito, ou procedente sem valor a cobrar) e Censurado (ainda em "
    "tramitação). Sentença e acórdão não competem entre si — são sequenciais, e quando o acórdão existe ele "
    "substitui a sentença como desfecho válido, usando sempre a data mais tardia entre os dois para proteger "
    "contra um erro de registro (data do acórdão cadastrada antes da sentença)."
))
story.append(p(
    "<b>Exceção tratada em 20/10/2026:</b> quando o acórdão apenas anula a sentença e devolve o processo para "
    "o 1º grau rejulgar (categoria 'SENTENÇA ANULADA' do catálogo de mérito de 2ª instância), o desfecho válido "
    "passa a ser o da sentença nova, não o do acórdão anulador — o acórdão, nesse caso específico, não decidiu "
    "mérito nenhum. A correção afeta uma fração pequena da coorte (~0,4%) mas corrige um viés sistemático: sem "
    "ela, esses processos eram contados como 'mérito sem proveito' mesmo quando ainda aguardavam novo "
    "julgamento, ou mesmo quando a sentença nova foi favorável. Ver Capitulo_Fase3_Resultados.pdf, Seção 2.1, "
    "para o detalhe completo."
))
story.append(p("2.3 Estimador de Kaplan-Meier", "H2"))
story.append(p(
    "A probabilidade de sobrevivência S(t) foi estimada pelo estimador produto-limite de Kaplan-Meier (KAPLAN; "
    "MEIER, 1958), que lida corretamente com censura à direita — uma parcela relevante dos processos ainda não "
    "tinha desfecho na data de extração, e descartá-los ou tratar sua ausência de desfecho como 'infinito' "
    "enviesaria qualquer média simples. A mediana reportada em cada indicador é sempre a mediana de "
    "Kaplan-Meier (o tempo em que S(t) cruza 0,5), nunca uma média aritmética."
))
story.append(p("2.4 Teste de log-rank multivariado", "H2"))
story.append(p(
    "Para testar se a diferença de mediana entre categorias (tipo de ação, matéria) é estatisticamente "
    "significativa — e não apenas uma diferença visual sujeita a ruído amostral — foi aplicado o teste de "
    "log-rank multivariado (MANTEL, 1966; PETO; PETO, 1972), o mesmo implementado em "
    "lifelines.statistics.multivariate_logrank_test (Python) e em survdiff() (R). O teste compara, a cada "
    "tempo de evento observado, o número de eventos esperado em cada grupo sob a hipótese nula (nenhuma "
    "diferença entre grupos) contra o número efetivamente observado, produzindo uma estatística qui-quadrado "
    "com k−1 graus de liberdade (k = número de grupos)."
))
story.append(p(
    "<b>Implementação própria:</b> o teste foi reimplementado em TypeScript (biblioteca própria do projeto, "
    "src/lib/kaplanMeier.ts) para rodar no navegador a cada filtro aplicado no dashboard interativo. A "
    "implementação foi validada contra o lifelines antes de entrar em produção: as estatísticas qui-quadrado "
    "bateram exatas em todos os casos de teste (diferença &lt; 0,0001); o p-valor da implementação em "
    "JavaScript satura em zero para estatísticas muito altas (ex.: χ²&gt;700) por underflow de ponto flutuante "
    "do double-precision, o que não afeta a decisão prática — a interface exibe 'p &lt; 0,0001' nesses casos."
))
story.append(CondPageBreak(6 * cm))

# ---------------------------------------------------------------------------
# 3. RESULTADOS - ESTAGIO 1
# ---------------------------------------------------------------------------
story.append(p("3. Resultados — Estágio 1 (Distribuição → Mérito/Acordo)", "H1"))
story.append(p("3.1 Estatística descritiva", "H2"))
story.append(tabela_simples(
    [
        ["Indicador", "Valor"],
        ["Coorte analisada", f"{fmt_num(E1['n'])} processos"],
        ["Mediana até mérito/acordo (Kaplan-Meier)", fmt_dias(E1["mediana"])],
        ["Mérito favorável com proveito econômico", f"{fmt_num(E1['n_favoravel'])} processos ({str(E1['pct_favoravel']).replace('.', ',')}%)"],
        ["Elegíveis ao Estágio 2 (Acordo + Mérito favorável)", f"{fmt_num(E1['n_elegivel_e2'])} processos"],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 8))
story.append(p("3.2 Ranking de gargalos por Tipo de Ação", "H2"))
N_CATS_TIPO_E1 = len(E1["ranking_tipo_acao"])
story.append(p(
    f"A tabela ordena as {N_CATS_TIPO_E1} categorias de tipo de ação com maior volume (mínimo de 30 processos), "
    "já sem agravos e mandados de segurança, pela mediana de tempo até o desfecho. Nomes de categoria conforme "
    "o catálogo tipo_acao padronizado em 20/10/2026 (ver Capitulo_Fase3_Resultados.pdf, Seção 2.1). O teste "
    "de log-rank confirma que a diferença entre as categorias não é explicável por acaso amostral:"
))
story.append(tabela_ranking(E1["ranking_tipo_acao"], "Tipo de ação"))
lr = E1["logrank_tipo_acao"]
story.append(p(
    f"Teste de log-rank: χ² = {fmt_chi2(lr['chi2'])}; gl = {lr['gl']}; {fmt_p_cientifico(lr['p'])} "
    "(estatisticamente significativo).",
    "CorpoTabelaNota",
))
story.append(p("3.3 Ranking de gargalos por Matéria", "H2"))
story.append(tabela_ranking(E1["ranking_materia"], "Matéria"))
lr = E1["logrank_materia"]
story.append(p(
    f"Teste de log-rank: χ² = {fmt_chi2(lr['chi2'])}; gl = {lr['gl']}; {fmt_p_cientifico(lr['p'])} "
    "(estatisticamente significativo).",
    "CorpoTabelaNota",
))
top_tipo = E1["ranking_tipo_acao"][0]
bottom_tipo = E1["ranking_tipo_acao"][-1]
razao_tipo = top_tipo["mediana"] / bottom_tipo["mediana"]
RAZAO_TIPO_FMT = f"{razao_tipo:.1f}".replace(".", ",")
ri_e1 = next(r for r in E1["ranking_tipo_acao"] if r["categoria"] == "RECURSO INOMINADO")
indeniz = next(r for r in E1["ranking_tipo_acao"] if r["categoria"] == "INDENIZATÓRIA")
RAZAO_INDENIZ_RI_FMT = "{:.1f}".format(indeniz["mediana"] / next(r for r in E1["ranking_tipo_acao"] if r["categoria"] == "RECURSO INOMINADO")["mediana"]).replace(".", ",")
PCT_INDENIZ_FMT = f"{100 * indeniz['n'] / sum(r['n'] for r in E1['ranking_tipo_acao']):.0f}"
RAZAO_INDENIZ_RI = indeniz["mediana"] / ri_e1["mediana"]
NOTA_INDENIZ_RI = (
    "Com t=0 na distribuição, um recurso cadastrado como processo próprio de 2ª instância provavelmente começa o "
    "relógio já perto do fim da tramitação, o que explicaria parte do contraste. "
    if RAZAO_INDENIZ_RI >= 1.5 else
    "O contraste é pequeno: na versão de 04/11/2026, com o RJ, INDENIZATÓRIA levava cerca de 2 vezes o tempo de "
    "RECURSO INOMINADO; sem o RJ, cujos processos eram quase todos indenizatórias recentes e sem desfecho, a "
    "diferença quase some. "
)
story.append(p(
    f"A amplitude é relevante: processos de {top_tipo['categoria']} (mediana {int(top_tipo['mediana'])} dias, "
    f"N={fmt_num(top_tipo['n'])}) levam cerca de {RAZAO_TIPO_FMT} vezes mais tempo que os de "
    f"{bottom_tipo['categoria']} ({int(bottom_tipo['mediana'])} dias). Os extremos, porém, são categorias de "
    f"volume pequeno; o dado mais relevante é que INDENIZATÓRIA — {PCT_INDENIZ_FMT}% dos processos das "
    f"{N_CATS_TIPO_E1} categorias da tabela — tem mediana de {int(indeniz['mediana'])} dias, "
    f"{RAZAO_INDENIZ_RI_FMT} vezes a de RECURSO INOMINADO ({int(ri_e1['mediana'])} dias). "
    + NOTA_INDENIZ_RI + "Por matéria, "
    f"{E1['ranking_materia'][0]['categoria']} e {E1['ranking_materia'][1]['categoria']} "
    f"({int(E1['ranking_materia'][0]['mediana'])} e {int(E1['ranking_materia'][1]['mediana'])} dias) destoam "
    "das demais, sinalizando uma classe de disputas sistematicamente mais lenta de resolver."
))
story.append(CondPageBreak(6 * cm))

# ---------------------------------------------------------------------------
# 4. RESULTADOS - ESTAGIO 2
# ---------------------------------------------------------------------------
story.append(p("4. Resultados — Estágio 2 (Mérito Favorável/Acordo → Pagamento)", "H1"))
story.append(p("4.1 Estatística descritiva", "H2"))
story.append(tabela_simples(
    [
        ["Indicador", "Valor"],
        ["Elegíveis ao pagamento", f"{fmt_num(E2['n'])} processos"],
        ["Mediana até o pagamento (Kaplan-Meier)", fmt_dias(E2["mediana"])],
        ["Já pagos na data da extração", f"{fmt_num(E2['n_pago'])} processos"],
        ["Taxa de pagamento efetivo", f"{str(E2['pct_pago']).replace('.', ',')}%"],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    f"A taxa de {str(E2['pct_pago']).replace('.', ',')}% não deve ser lida como uma 'taxa de insucesso' — é uma "
    "fotografia do que já foi pago até a data de extração, sobre uma população que inclui vitórias recentes "
    "ainda em fase de execução. Ela tende a subir com o tempo conforme a fila avança."
))
story.append(p("4.2 Ranking de gargalos de pagamento — Por Tipo de Ação", "H2"))
story.append(tabela_ranking(E2["ranking_tipo_acao"], "Tipo de ação"))
lr = E2["logrank_tipo_acao"]
n_cats_tipo_e2 = len(E2["ranking_tipo_acao"])
_sem_mediana = [r["categoria"] for r in E2["ranking_tipo_acao"] if r["mediana"] is None or math.isinf(r["mediana"])]
NOTA_NAO_CALC_E2 = (
    f" Categorias com menos de 50% dos casos pagos até a data de extração (ex.: {_sem_mediana[0]}) aparecem na "
    "tabela com mediana 'não calculável', mas contribuem com informação válida ao teste." if _sem_mediana else ""
)
story.append(p(
    f"Teste de log-rank: χ² = {fmt_chi2(lr['chi2'])}; gl = {lr['gl']}; {fmt_p_cientifico(lr['p'])} "
    "(estatisticamente significativo). "
    f"O teste usa as {n_cats_tipo_e2} categorias de tipo de ação com volume suficiente (mínimo 30 processos) "
    f"dentro do subconjunto elegível ao pagamento — menos que as {N_CATS_TIPO_E1} do Estágio 1, porque esse subconjunto é "
    "menor." + NOTA_NAO_CALC_E2,
    "CorpoTabelaNota",
))
story.append(p("4.3 Ranking de gargalos de pagamento — Por Matéria", "H2"))
story.append(tabela_ranking(E2["ranking_materia"], "Matéria"))
lr = E2["logrank_materia"]
story.append(p(
    f"Teste de log-rank: χ² = {fmt_chi2(lr['chi2'])}; gl = {lr['gl']}; {fmt_p_cientifico(lr['p'])} "
    "(estatisticamente significativo).",
    "CorpoTabelaNota",
))
_calc_e2 = sorted(
    [r for r in E2["ranking_materia"] if r["mediana"] is not None and not math.isinf(r["mediana"])],
    key=lambda r: r["mediana"], reverse=True,
)
lenta, segunda, terceira = _calc_e2[0], _calc_e2[1], _calc_e2[2]
MATERIA_GARGALO_E2 = lenta["categoria"]
_pos_rmc = next((i for i, r in enumerate(_calc_e2) if r["categoria"] == "RMC"), None)
NOTA_RMC = ", e RMC segue entre os dois mais lentos" if _pos_rmc is not None and _pos_rmc <= 1 else ""
RAZAO_GARGALO_FMT = f"{lenta['mediana'] / segunda['mediana']:.1f}".replace(".", ",")
story.append(p(
    f"O achado mais acionável desta fase está aqui: a matéria {lenta['categoria']} leva mediana de "
    f"{int(lenta['mediana'])} dias até o pagamento (N={fmt_num(lenta['n'])}) — {RAZAO_GARGALO_FMT} vezes a "
    f"seguinte, {segunda['categoria']} ({int(segunda['mediana'])} dias), que por sua vez já é bem mais lenta que "
    f"{terceira['categoria']} ({int(terceira['mediana'])} dias) e o restante do ranking (no máximo "
    f"{int(_calc_e2[3]['mediana'])} dias). Na versão anterior deste capítulo (coorte de 04/11/2026), RMC "
    "aparecia isolada no topo; com a coorte atual, o gargalo mais extremo é o de "
    f"{lenta['categoria']}{NOTA_RMC}. Esse gargalo não tem uma explicação óbvia a "
    "partir dos dados já observados e merece investigação operacional direta — é exatamente o tipo de achado "
    "que uma análise exploratória bem conduzida deve produzir."
))

# ---------------------------------------------------------------------------
# 5. DISCUSSAO
# ---------------------------------------------------------------------------
story.append(p("5. Discussão", "H1"))
story.append(p(
    "Os resultados confirmam a validade da analogia com engenharia de confiabilidade que fundamenta este "
    "trabalho: assim como um componente físico pode falhar por diferentes modos com tempos característicos "
    "distintos, um processo judicial percorre uma 'vida útil' até o desfecho cuja duração depende "
    "sistematicamente de sua categoria. O teste de log-rank, em todos os quatro recortes testados (Estágio 1 "
    "× tipo de ação, Estágio 1 × matéria, Estágio 2 × tipo de ação, Estágio 2 × matéria), rejeitou a hipótese "
    "nula com margem larga, confirmando que as diferenças visuais observadas nas curvas de Kaplan-Meier "
    "refletem heterogeneidade real na população de processos, não ruído de amostragem."
))
story.append(p(
    "Esse resultado tem um limite importante: log-rank e Kaplan-Meier são métodos univariados — cada teste "
    "compara uma única dimensão por vez (só tipo de ação, ou só matéria), sem controlar pela outra. É "
    "inteiramente possível que parte do efeito atribuído a 'tipo de ação' seja, na verdade, reflexo de uma "
    "matéria específica estar concentrada naquele tipo de ação (confundimento). Separar esses efeitos exige um "
    "modelo multivariado — exatamente o objeto da Fase 3 (Regressão de Cox e riscos competitivos de "
    "Fine-Gray), que confirmou esse exato limite: o contraste de tipo de ação mais marcante desta fase "
    f"(RECURSO INOMINADO mais rápido que INDENIZATÓRIA: {int(ri_e1['mediana'])} contra {int(indeniz['mediana'])} "
    "dias) se inverte quando competência entra no modelo — no Cox, RECURSO INOMINADO passa a ter "
    f"HR={HR_RI_FMT}, ou seja, MAIS lento que a referência. A rapidez vista aqui vinha da competência (Turma "
    "Recursal) e do relógio começar já na 2ª instância, não do tipo de ação em si — ver "
    "Capitulo_Fase3_Resultados.pdf, Seção 5."
))

# ---------------------------------------------------------------------------
# 6. LIMITACOES
# ---------------------------------------------------------------------------
story.append(p("6. Limitações", "H1"))
story.append(lista([
    "Correlação, não causa: uma categoria aparecer como mais lenta no ranking não prova que a categoria em si "
    "causa a demora — pode refletir fatores concomitantes (comarca, juiz, complexidade do caso) não "
    "controlados nesta fase.",

    f"UF não entra como dimensão própria: {PCT_AM_FMT}% da coorte é do AM; as demais UFs (a maior é a PB, com "
    f"{fmt_num(N_PB)} processos) têm volume pequeno, e a comarca já captura a variação geográfica.",

    "Escopo restrito a NG e LA/AM: os resultados descrevem esses dois escritórios e não se generalizam para o "
    "LA/RJ, retirado da coorte por quase não ter desfechos observados.",

    "Categorias sem mediana calculável no Estágio 2: algumas categorias de tipo de ação e matéria têm menos de "
    "50% dos casos pagos até a data de extração — a mediana nesses grupos ainda não existe estatisticamente, "
    "embora o teste de log-rank continue válido usando a informação censurada.",

    f"Dados de pesquisa, não produção: os números deste capítulo são um retrato de {DATA_FOTO}; o dashboard "
    "interativo os atualiza continuamente a partir do mesmo endpoint de produção, então números futuros do "
    "mesmo gráfico podem diferir ligeiramente sem que isso indique erro.",

    "Qualidade de dado como processo contínuo: quatro correções (padronização de tipo_acao, precedência da "
    "sentença anulada, marco zero na distribuição, agravos identificados pelo número CNJ) foram descobertas depois da primeira versão deste capítulo — é razoável supor que "
    "outras inconsistências ainda não identificadas existam na base (ver Capitulo_Fase3_Resultados.pdf, "
    "Seção 6).",
]))

# ---------------------------------------------------------------------------
# 7. SINTESE
# ---------------------------------------------------------------------------
story.append(p("7. Síntese e encaminhamento para a Fase 3", "H1"))
story.append(p(
    f"A Fase 2 cumpriu seu objetivo: produziu uma descrição estatisticamente fundamentada de quanto tempo a "
    f"esteira processual leva para resolver um caso ({int(E1['mediana'])} dias de mediana geral no Estágio 1, "
    f"mais {int(E2['mediana'])} dias de mediana no Estágio 2 para quem vence com valor a receber) e de onde, "
    "especificamente, esse tempo se concentra — com significância estatística confirmada por log-rank em "
    "todas as quatro comparações testadas. O achado do gargalo de pagamento em processos de matéria "
    f"{MATERIA_GARGALO_E2} é o "
    "resultado mais diretamente acionável desta fase. A Fase 3 formalizou essas relações num modelo "
    "multivariado de riscos competitivos (Cox; Fine-Gray), controlando tipo de ação, matéria e demais "
    "covariáveis disponíveis simultaneamente, e produzindo — pela primeira vez no projeto — uma previsão "
    "individualizada por processo, não apenas uma média por categoria."
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(p("Referências", "H1"))
for ref in [
    "KAPLAN, E. L.; MEIER, P. Nonparametric Estimation from Incomplete Observations. <i>Journal of the American Statistical Association</i>, v. 53, n. 282, p. 457-481, 1958.",
    "MANTEL, N. Evaluation of Survival Data and Two New Rank Order Statistics Arising in Its Consideration. <i>Cancer Chemotherapy Reports</i>, v. 50, n. 3, p. 163-170, 1966.",
    "PETO, R.; PETO, J. Asymptotically Efficient Rank Invariant Test Procedures. <i>Journal of the Royal Statistical Society: Series A</i>, v. 135, n. 2, p. 185-207, 1972.",
    "COX, D. R. Regression Models and Life-Tables. <i>Journal of the Royal Statistical Society: Series B</i>, v. 34, n. 2, p. 187-220, 1972.",
    "FINE, J. P.; GRAY, R. J. A Proportional Hazards Model for the Subdistribution of a Competing Risk. <i>Journal of the American Statistical Association</i>, v. 94, n. 446, p. 496-509, 1999.",
    "BARLOW, R. E.; PROSCHAN, F. <i>Statistical Theory of Reliability and Life Testing</i>. New York: Holt, Rinehart and Winston, 1975.",
]:
    story.append(p(ref, "Referencia"))

story.append(Spacer(1, 10))
story.append(p(
    "Este capítulo complementa o Plano_TCC_Luiz.pdf (metodologia completa), o Capitulo_Fase3_Resultados.pdf e "
    "o dashboard interativo em produção (LexHub → Sobrevivência Processual), ambos na mesma pasta de pesquisa. "
    "Script reprodutível: scripts/calcular_fase2.py (números) + scripts/gerar_capitulo_fase2.py (este "
    "documento).",
    "Corpo",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Fase 2: Análise Exploratória e Kaplan-Meier",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
