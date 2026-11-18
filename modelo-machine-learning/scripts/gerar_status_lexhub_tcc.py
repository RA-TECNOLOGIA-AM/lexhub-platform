# -*- coding: utf-8 -*-
"""
Gera o documento de status "LexHub + TCC" para reuniao de acompanhamento com o
orientador: visao geral da plataforma, o que ja foi desenvolvido da pesquisa,
status consolidado por fase e perspectiva de finalizacao.

Fontes usadas (nao digitar numero a mao sem checar aqui primeiro):
  - TCC - Luiz/Plano_TCC_Luiz.pdf (plano original de 8 fases)
  - TCC - Luiz/Capitulo_Fase2_Resultados.pdf (achados Fase 2)
  - TCC - Luiz/Capitulo_Fase3_Resultados.pdf / dados/fase3_*.csv (achados Fase 3)
  - Levantamento direto no codigo (LexHub/api_dashboards) em 18/10/2026: endpoint
    da API, contagem de dashboards, controle de acesso, git log.

Atualizado em 19/10/2026: Fase 1 concluida (pseudonimizacao do numero de
processo via hash, ver scripts/atualizar_dashboard_tcc.py).

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_status_lexhub_tcc.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = ML_DIR
OUT_PDF = f"{BASE_DIR}/Status_LexHub_TCC_Outubro2026.pdf"

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=21, leading=26, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle(name="SubtituloCapa", fontSize=13, leading=17, fontName="Helvetica", spaceAfter=14, textColor=colors.HexColor("#333333")))
styles.add(ParagraphStyle(name="AutorData", fontSize=10.5, leading=14, fontName="Helvetica"))
styles.add(ParagraphStyle(name="NotaRodapeCapa", fontSize=9, leading=13, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceBefore=18))
styles.add(ParagraphStyle(name="PartTitulo", fontSize=17, leading=21, fontName="Helvetica-Bold", textColor=colors.HexColor("#2d3142"), spaceBefore=4, spaceAfter=4))
styles.add(ParagraphStyle(name="PartSubtitulo", fontSize=11, leading=15, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceAfter=14))
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=18, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="H2", fontSize=11.5, leading=15, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=14.5, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="CorpoTabelaNota", fontSize=8.5, leading=12, fontName="Helvetica-Oblique", textColor=colors.HexColor("#444444"), alignment=TA_JUSTIFY, spaceAfter=10))
styles.add(ParagraphStyle(name="Destaque", fontSize=10.5, leading=15, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8, backColor=colors.HexColor("#eef0ff"), borderPadding=8))
styles.add(ParagraphStyle(name="CelulaTabela", fontSize=8.8, leading=11, fontName="Helvetica"))
styles.add(ParagraphStyle(name="CelulaTabelaBold", fontSize=8.8, leading=11, fontName="Helvetica-Bold"))

COR_CABECALHO_TABELA = colors.HexColor("#2d3142")
COR_LINHA_ALT = colors.HexColor("#f2f2f5")
COR_CONCLUIDO = "#1e8e5a"
COR_PARCIAL = "#b9770e"
COR_PENDENTE = "#999999"


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.3 * cm, "LexHub + TCC Luiz Reis — Status do projeto (Outubro/2026)")
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
    """linhas[0] é o cabecalho se header=True. Celulas longas podem vir como Paragraph."""
    data = []
    for i, linha in enumerate(linhas):
        row = []
        for cel in linha:
            if isinstance(cel, str):
                estilo = "CelulaTabelaBold" if (header and i == 0) else "CelulaTabela"
                row.append(Paragraph(cel, styles[estilo]))
            else:
                row.append(cel)
        data.append(row)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO_TABELA),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    for i in range(1 if header else 0, len(data)):
        if (i - (1 if header else 0)) % 2 == 1:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_LINHA_ALT))
    t.setStyle(TableStyle(estilo))
    return t


def status_tag(texto, cor_hex):
    return Paragraph(f'<font color="{cor_hex}"><b>{texto}</b></font>', styles["CelulaTabela"])


story = []

# ===========================================================================
# CAPA
# ===========================================================================
story.append(Spacer(1, 2.6 * cm))
story.append(p("LexHub + Pesquisa de TCC", "TituloCapa"))
story.append(p(
    "Status do Projeto — Visão da Plataforma, Progresso da Pesquisa e Perspectiva de Finalização",
    "SubtituloCapa",
))
story.append(Spacer(1, 1 * cm))
story.append(p("Autor: Luiz Reis<br/>Reunião de acompanhamento — Outubro de 2026", "AutorData"))
story.append(Spacer(1, 1.6 * cm))
story.append(p(
    "Este documento foi preparado para a reunião de acompanhamento com o orientador, já aprovado "
    "para a linha de pesquisa <i>Modelagem de Sobrevivência com Riscos Competitivos aplicada ao "
    "LexHub</i>. Ele cobre, nesta ordem: (1) o que é a plataforma LexHub hoje, em produção real; "
    "(2) o que já foi desenvolvido da pesquisa de TCC sobre essa base; (3) um status consolidado "
    "por fase do plano original; e (4) a perspectiva de prazo para as fases restantes.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ===========================================================================
# SUMARIO EXECUTIVO
# ===========================================================================
story.append(p("Sumário Executivo", "H1"))
story.append(p(
    "O LexHub é um sistema de Business Intelligence em produção real, usado hoje por três "
    "escritórios de advocacia (NG, LA e RJ), com <b>89 dashboards</b> ativos sobre dados do sistema "
    "de gestão processual LexFlow. O TCC usa essa base — já auditada, validada e em uso diário — "
    "como fonte de dados para uma pesquisa de modelagem de sobrevivência com riscos competitivos, "
    "aplicando o mesmo ferramental da engenharia de confiabilidade (tempo até falha, múltiplos "
    "modos de falha) ao tempo até desfecho de processos judiciais."
))
story.append(p("Dos 8 fases do plano original, o status atual é:", "Corpo"))
story.append(tabela_simples(
    [
        ["Fase", "Status"],
        ["Fase 0 — Alinhamento institucional", status_tag("CONCLUÍDA", COR_CONCLUIDO)],
        ["Fase 1 — Extração e anonimização", status_tag("CONCLUÍDA", COR_CONCLUIDO)],
        ["Fase 2 — Exploratória e Kaplan-Meier", status_tag("CONCLUÍDA", COR_CONCLUIDO)],
        ["Fase 3 — Cox e Fine-Gray", status_tag("CONCLUÍDA", COR_CONCLUIDO)],
        ["Fase 4 — Modelo de aprendizado de máquina", status_tag("NÃO INICIADA", COR_PENDENTE)],
        ["Fase 5 — Validação", status_tag("NÃO INICIADA", COR_PENDENTE)],
        ["Fase 6 — Protótipo aplicado (opcional)", status_tag("NÃO INICIADA", COR_PENDENTE)],
        ["Fase 7 — Escrita e defesa", status_tag("EM ANDAMENTO (parcial)", COR_PARCIAL)],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "<b>Destaque:</b> as Fases 2 e 3 não são apenas análises em notebook — estão expostas como um "
    "dashboard interativo real, em produção, dentro do próprio LexHub "
    "(<i>Sobrevivência Processual</i>), consumindo um endpoint de API dedicado e recalculando "
    "Kaplan-Meier e log-rank ao vivo no navegador a cada filtro.",
    "Destaque",
))
story.append(PageBreak())

# ===========================================================================
# PARTE 1 — O LEXHUB COMO PLATAFORMA
# ===========================================================================
story.append(p("Parte 1", "PartTitulo"))
story.append(p("O LexHub como Plataforma", "PartSubtitulo"))

story.append(p("1.1 O que é e para quem", "H1"))
story.append(p(
    "O LexHub é um sistema de Business Intelligence interno construído para escritórios de "
    "advocacia — hoje atende três operações (<b>NG</b>, <b>LA</b> e <b>RJ</b>) — sobre dados do "
    "LexFlow, o sistema de gestão processual onde cada processo judicial é cadastrado e "
    "acompanhado. Ele transforma dado operacional bruto (processos, atividades, prazos, "
    "comissionamento, campanhas de marketing, etc.) em dashboards de indicadores para gestores, "
    "comercial, jurídico e áreas de suporte."
))
story.append(p("1.2 Arquitetura técnica", "H1"))
story.append(p(
    "A plataforma segue uma arquitetura cliente-servidor clássica, com duas partes principais:"
))
story.append(tabela_simples(
    [
        ["Camada", "Tecnologia", "Papel"],
        ["Frontend", "React + TypeScript (Vite)",
         "Interface dos dashboards, autenticação, controle de acesso por cargo/escritório."],
        ["Backend / API", "Python (FastAPI)",
         "Extrai e transforma os dados, aplica regras de negócio (comissionamento, KPIs), expõe "
         "endpoints REST com cache."],
        ["Banco de dados", "PostgreSQL (Supabase) — 3 bases (ng, laadv, lexflow)",
         "Armazena o dado operacional de cada escritório/sistema de origem."],
        ["Cache", "Memória local + Redis",
         "Evita reprocessar consultas pesadas a cada acesso; a maioria dos dashboards atualiza em "
         "minutos, não em tempo real puro."],
    ],
    [3.2 * cm, 5.6 * cm, 7.6 * cm],
))
story.append(Spacer(1, 8))
story.append(p("1.3 Escala em produção", "H1"))
story.append(p(
    "O sistema cobre hoje <b>89 dashboards</b> registrados, organizados em 6 macro-setores "
    "(Estratégico, Jurídico, Marketing/Comercial, Pré-processual, Intermediárias e Tech — esta "
    "última é onde vive o dashboard do TCC). A distribuição por escritório reflete o tamanho de "
    "cada operação:"
))
story.append(tabela_simples(
    [
        ["Escritório / Área", "Dashboards (páginas)"],
        ["NG", "33"],
        ["LA", "30"],
        ["RJ", "17"],
        ["Geral (cross-escritório, inclui o do TCC)", "3"],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 8))
story.append(p("1.4 Controle de acesso e segurança", "H1"))
story.append(p(
    "O acesso é controlado por cargo (função) do usuário: perfis <b>Desenvolvedor</b> e "
    "<b>Gestor</b> têm acesso amplo; os demais cargos só enxergam os dashboards especificamente "
    "liberados para sua função e escritório. Há suporte a usuários com acesso cruzado entre "
    "escritórios (ex.: alguém que atende NG e LA ao mesmo tempo). O login aceita e-mail/senha ou "
    "conta Google corporativa (restrita a domínios autorizados), com expiração automática de "
    "sessão após 10 horas."
))
story.append(p("1.5 Ritmo de desenvolvimento", "H1"))
story.append(p(
    "O LexHub não é um projeto estático: os dois repositórios (frontend e backend) recebem "
    "commits com frequência quase diária — ajustes de regra de negócio, novos indicadores, e "
    "recentemente uma API pública própria (autenticação por token, usada por sistemas externos) e "
    "login corporativo via Google. É dentro desse sistema vivo e em produção real que a pesquisa "
    "de TCC está inserida — não é um ambiente isolado criado só para o trabalho acadêmico."
))
story.append(Spacer(1, 10))

# ===========================================================================
# PARTE 2 — O PROJETO DE TCC
# ===========================================================================
story.append(p("Parte 2", "PartTitulo"))
story.append(p("O Projeto de TCC", "PartSubtitulo"))

story.append(p("2.1 Tema e a ponte com Engenharia Elétrica/Eletrônica", "H1"))
story.append(p(
    "<b>Título proposto:</b> <i>Modelagem de Sobrevivência com Riscos Competitivos para Previsão "
    "de Prazo e Desfecho de Processos Judiciais: um Estudo de Caso em Engenharia de Confiabilidade "
    "Aplicada.</i>"
))
story.append(p(
    "A ponte com o curso não é estilística, é matemática: análise de sobrevivência com riscos "
    "competitivos é ferramenta central da engenharia de confiabilidade — estimar o tempo até a "
    "falha de um componente (MTBF, distribuição de Weibull) e, havendo mais de um modo de falha "
    "possível, qual modo ocorrerá primeiro. A única mudança de domínio é que o \"componente\" é um "
    "processo judicial, e os \"modos de falha\" são os tipos de desfecho (acordo, mérito favorável, "
    "mérito desfavorável). O ferramental — função de risco, função de sobrevivência, dados "
    "censurados, riscos competitivos — é idêntico."
))
story.append(p("2.2 Plano de 8 fases (proposta original)", "H1"))
story.append(tabela_simples(
    [
        ["Fase", "Duração estimada", "Entregável principal"],
        ["0 — Alinhamento institucional", "2 semanas",
         "Validar linha de pesquisa com o orientador; checar exigência de comitê de ética."],
        ["1 — Extração e anonimização", "3-4 semanas",
         "ETL isolado do LexFlow; exclusão de segredo de justiça; pseudonimização de dados pessoais."],
        ["2 — Exploratória e Kaplan-Meier", "3 semanas",
         "Estatística descritiva, curvas de sobrevivência por categoria, teste de log-rank."],
        ["3 — Cox e Fine-Gray", "4 semanas",
         "Modelo multivariado clássico (Cox) + riscos competitivos (Fine-Gray)."],
        ["4 — Modelo de aprendizado de máquina", "4-5 semanas",
         "Random Survival Forest e/ou XGBoost-AFT, comparado ao baseline estatístico."],
        ["5 — Validação", "2-3 semanas",
         "C-index, Brier Score, calibração, validação temporal (sem vazamento de futuro)."],
        ["6 — Protótipo aplicado (opcional)", "3-4 semanas",
         "Escore do modelo exposto como indicador no LexHub; extensão física (ESP32) se exigida."],
        ["7 — Escrita e defesa", "paralela às fases 4-6",
         "Redação contínua da monografia."],
    ],
    [4.6 * cm, 3 * cm, 8.8 * cm],
))
story.append(p(
    "Estimativa total do plano original: cerca de 24-26 semanas de trabalho técnico, cabendo em "
    "dois semestres (TCC I e TCC II), com a escrita acontecendo em paralelo às fases finais — não "
    "concentrada só no fim.",
    "CorpoTabelaNota",
))
story.append(PageBreak())

story.append(p("2.3 O que já foi desenvolvido, em detalhe", "H1"))

story.append(p("Fase 0 — Alinhamento institucional", "H2"))
story.append(p(
    "<b>Concluída.</b> As autorizações necessárias foram obtidas e o orientador já aprovou a linha "
    "de pesquisa. Esta reunião é a continuidade desse alinhamento, não o primeiro contato."
))

story.append(p("Fase 1 — Extração e anonimização", "H2"))
story.append(p(
    "<b>Concluída.</b> A extração exclui processos sob segredo de justiça (483 casos) e corrige "
    "dois bugs reais de dados encontrados na base (timestamp zero em datas de contratação; anos com "
    "dígito a mais em algumas sentenças). A pseudonimização de <i>pessoa</i>/<i>adverso_processo</i> "
    "prevista no plano original não chegou a ser necessária na prática: a extração real nunca fez "
    "join com nome/CPF de cliente ou parte adversa — só campos do processo em si (tipo de ação, "
    "matéria, valor de causa, comarca). O único identificador real que restava era o número do "
    "processo (consultável publicamente no site do tribunal, logo dado pessoal para fins de LGPD); "
    "desde 19/10/2026 ele é trocado por um hash SHA-256 truncado logo após a extração, antes de "
    "qualquer gravação em disco — o valor original nunca chega a tocar os arquivos de pesquisa. "
    "O endpoint de produção consumido pelo dashboard nunca expôs esse campo para começar. Duas "
    "decisões ficam registradas por transparência: a lista de triagem de inconsistências de data "
    "mantém o número de processo em texto puro de propósito (é uso operacional interno, para alguém "
    "corrigir o cadastro na origem, não faz parte da coorte de pesquisa); e os nomes de juiz/relator "
    "permanecem reais, por serem registro público de decisão judicial de agente público, não dado "
    "pessoal de cliente/parte adversa — fica à disposição do orientador decidir se prefere uma "
    "postura mais conservadora aqui."
))

story.append(p("Fase 2 — Exploratória e Kaplan-Meier", "H2"))
story.append(p(
    "<b>Concluída</b> — e com um passo além do que o plano original previa: em vez de ficar só em "
    "notebook/relatório, os resultados viram um <b>dashboard interativo em produção real</b> dentro "
    "do LexHub (\"Sobrevivência Processual\"), que qualquer usuário autorizado pode abrir, filtrar e "
    "explorar. Principais números (coorte de 40.023 processos, NG/LA/RJ):"
))
story.append(tabela_simples(
    [
        ["Indicador", "Valor"],
        ["Mediana até mérito/acordo (Estágio 1)", "312 dias"],
        ["Mérito favorável com proveito econômico", "6.759 processos (16,9%)"],
        ["Elegíveis ao Estágio 2 (acordo + mérito favorável)", "7.252 processos"],
        ["Mediana até o pagamento (Estágio 2)", "223 dias"],
        ["Taxa de pagamento efetivo já observada", "34,7%"],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "Dois achados de log-rank confirmados estatisticamente (não só visualmente): tipo de ação "
    "explica diferença real de tempo (χ²=444,38; gl=7; p=7,16×10<super>-92</super>) — APELAÇÃO CÍVEL "
    "leva 589 dias de mediana contra 174 dias de EMBARGOS, cerca de 3,4x mais lento, coerente com "
    "APELAÇÃO CÍVEL ser recurso de 2ª instância. Matéria também (χ²=3.561,99; gl=7; "
    "p&lt;10<super>-300</super>) — MORA e SLN destoam das demais, acima de 650 dias. O achado mais "
    "acionável: a matéria <b>RMC leva mediana de 595 dias até o pagamento</b> — mais que o dobro de "
    "qualquer outra matéria do ranking com mediana calculável — sem explicação processual óbvia, "
    "candidato direto a investigação operacional."
))

story.append(p("Fase 3 — Cox e Fine-Gray", "H2"))
story.append(p(
    "<b>Concluída</b>, com duas extensões recentes: comarca/competência como novas covariáveis, e duas "
    "correções de qualidade de dado (padronização do catálogo tipo_acao no LexFlow; correção da regra "
    "de precedência para o caso \"sentença anulada\" — quando o acórdão só anula e devolve pro 1º grau, "
    "o desfecho válido passa a ser o da sentença nova, não o do acórdão). Diferente da Fase 2 "
    "(univariada, uma dimensão por vez), este é um modelo multivariado: controla tipo de ação, matéria, "
    "valor de causa, escritório, comarca e competência simultaneamente."
))
story.append(tabela_simples(
    [
        ["Indicador", "Valor"],
        ["N (processos modelados)", "39.774"],
        ["Índice de concordância (C-index) do Cox", "0,674"],
        ["Covariáveis no modelo", "30 (dummies de 6 dimensões + log(valor de causa))"],
        ["Evento de interesse no Fine-Gray (mérito favorável)", "6.757 processos (17,0%)"],
    ],
    [10 * cm, 6.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "O achado multivariado mais revelador <b>não aparecia</b> na análise univariada da Fase 2 — só "
    "emerge ao controlar as demais variáveis ao mesmo tempo, e ficou mais nítido depois das correções "
    "de dado: o escritório NG deixou de ser estatisticamente significativo no Cox geral (tempo até "
    "QUALQUER desfecho; HR=1,027; p=0,126) mas segue fortemente significativo no Fine-Gray "
    "(especificamente para mérito favorável; HR de subdistribuição=0,863; p&lt;0,0001) — evidência "
    "mais limpa do que uma simples diferença de magnitude, sugerindo que NG não tramita mais devagar "
    "em geral, mas tem dificuldade específica em converter casos em desfecho favorável. O mesmo "
    "padrão \"lentidão geral ≠ lentidão para o sucesso\" se repete, de forma independente, em "
    "competência (Vara Cível). O contraste que uma versão anterior deste modelo via em APELAÇÃO não "
    "sobreviveu à padronização do catálogo — tratado com transparência no capítulo como um achado "
    "que não se confirmou."
))
story.append(p(
    "Como nenhuma biblioteca Python disponível implementa Fine-Gray nativamente, o modelo foi "
    "implementado manualmente (técnica de Cox ponderado por IPCW, Geskus 2011) e "
    "<b>validado matematicamente</b> antes de usar nos dados reais: em um caso simulado sem risco "
    "competitivo, a implementação precisa coincidir exatamente com um Cox padrão — e coincidiu, com "
    "diferença menor que 2×10<super>-6</super>.",
    "Corpo",
))

story.append(p("2.4 Arquitetura do pipeline de pesquisa", "H1"))
story.append(p(
    "Um ponto técnico que vale destacar na reunião: a pesquisa não roda num ambiente isolado — ela "
    "está integrada à mesma infraestrutura de produção do LexHub. Até meados de outubro, o "
    "dashboard carregava um arquivo gerado por um script local (rodando na máquina do pesquisador); "
    "isso foi migrado para um <b>endpoint de API dedicado</b> "
    "(<i>GET /tcc_sobrevivencia_processual</i>), com cache, seguindo exatamente o mesmo padrão dos "
    "outros 88 dashboards do sistema. O cálculo estatístico (Kaplan-Meier, log-rank) continua "
    "rodando no navegador do usuário, recalculado a cada filtro — a API só entrega o dado bruto da "
    "coorte em formato compacto."
))
story.append(PageBreak())

# ===========================================================================
# PARTE 3 — STATUS CONSOLIDADO
# ===========================================================================
story.append(p("Parte 3", "PartTitulo"))
story.append(p("Status Consolidado por Fase", "PartSubtitulo"))

story.append(tabela_simples(
    [
        ["Fase", "Status", "Observação"],
        ["0 — Alinhamento institucional", status_tag("Concluída", COR_CONCLUIDO),
         "Autorizações obtidas; orientador já aprovou a linha de pesquisa."],
        ["1 — Extração e anonimização", status_tag("Concluída", COR_CONCLUIDO),
         "Extração, limpeza e pseudonimização do número de processo (hash SHA-256) concluídas em "
         "19/10/2026."],
        ["2 — Exploratória e Kaplan-Meier", status_tag("Concluída", COR_CONCLUIDO),
         "Capítulo de resultados redigido + dashboard interativo em produção."],
        ["3 — Cox e Fine-Gray", status_tag("Concluída", COR_CONCLUIDO),
         "Capítulo de resultados redigido, validado matematicamente; comarca/competência já "
         "incorporadas."],
        ["4 — Modelo de aprendizado de máquina", status_tag("Não iniciada", COR_PENDENTE),
         "Random Survival Forest / XGBoost-AFT — próximo passo técnico."],
        ["5 — Validação", status_tag("Não iniciada", COR_PENDENTE),
         "Depende da Fase 4 estar pronta para comparação."],
        ["6 — Protótipo aplicado (opcional)", status_tag("Não iniciada", COR_PENDENTE),
         "Só necessária se o colegiado exigir componente de hardware."],
        ["7 — Escrita e defesa", status_tag("Em andamento", COR_PARCIAL),
         "Dois capítulos de resultados já redigidos em paralelo às fases (2 e 3); escrita segue "
         "junto das próximas fases, como planejado."],
    ],
    [4.4 * cm, 2.6 * cm, 9.4 * cm],
))
story.append(Spacer(1, 10))
story.append(p(
    "Em resumo: das 8 fases planejadas, <b>4 estão concluídas</b> (0, 1, 2, 3), <b>1 está em "
    "andamento</b> (7) e <b>3 ainda não começaram</b> (4, 5, 6 — sendo a 6 opcional). O projeto já "
    "fechou toda a base do trabalho técnico central e está pronto para iniciar a Fase 4 (modelagem "
    "preditiva), no cronograma original de ~24-26 semanas."
))
story.append(PageBreak())

# ===========================================================================
# PARTE 4 — PERSPECTIVA DE FINALIZACAO
# ===========================================================================
story.append(p("Parte 4", "PartTitulo"))
story.append(p("Perspectiva de Finalização", "PartSubtitulo"))

story.append(p("4.1 Trabalho técnico restante", "H1"))
story.append(tabela_simples(
    [
        ["Fase", "Estimativa original", "Nota"],
        ["4 — Modelo de ML", "4-5 semanas", "Random Survival Forest e/ou XGBoost-AFT."],
        ["5 — Validação", "2-3 semanas", "C-index, Brier Score, split temporal."],
        ["6 — Protótipo (se exigido)", "3-4 semanas", "Só entra se o colegiado pedir hardware."],
    ],
    [4.6 * cm, 3.4 * cm, 8.4 * cm],
))
story.append(Spacer(1, 6))
story.append(p(
    "Com a Fase 1 já concluída, e sem a Fase 6 (que é condicional), restam aproximadamente "
    "<b>6 a 8 semanas</b> de trabalho técnico central para fechar o núcleo preditivo do TCC "
    "(fases 4 e 5). A escrita da monografia continua em paralelo, como já vem acontecendo — os "
    "capítulos de resultados das Fases 2 e 3 já estão redigidos, então os da Fase 4/5 seguem o "
    "mesmo padrão."
))
story.append(p("4.2 Pendências a resolver com o orientador/colegiado", "H1"))
story.append(lista([
    "<b>Componente de hardware:</b> confirmar se o colegiado aceita a linha "
    "\"confiabilidade/sobrevivência aplicada\" sem exigir um protótipo físico, ou se a Fase 6 "
    "(painel ESP32) precisa entrar como obrigatória.",
    "<b>Comitê de ética:</b> confirmar se o uso de dado real de terceiros (já pseudonimizado desde "
    "19/10/2026) exige submissão formal a um CEP.",
    "<b>Divisão TCC I / TCC II:</b> alinhar quais entregáveis mínimos cada etapa exige, para "
    "encaixar o cronograma das fases restantes nos dois semestres.",
]))
story.append(p("4.3 Riscos já identificados e como estão sendo tratados", "H1"))
story.append(lista([
    "<b>Viés de seleção</b> nos casos já decididos (tendem a ser os mais rápidos): é exatamente o "
    "motivo de usar sobrevivência com censura em vez de classificação binária — já tratado desde a "
    "Fase 2.",
    "<b>Missingness não aleatório</b> em comarca/juiz: resolvido para comarca (agora covariável "
    "plena na Fase 3, ~97% de cobertura real na coorte); juiz/relator ficam fora do modelo formal "
    "por um motivo metodológico mais forte — são preenchidos só depois do desfecho, o que "
    "introduziria viés de causalidade reversa.",
    "<b>Vazamento temporal</b> (treinar com informação do futuro): split temporal obrigatório já "
    "planejado para a Fase 5, ainda não iniciada.",
    "<b>Dados pessoais:</b> resolvido em 19/10/2026 — número de processo pseudonimizado por hash "
    "SHA-256 nos arquivos de pesquisa; nenhum dado de cliente/parte adversa chegou a ser extraído.",
]))
story.append(p("4.4 Para a reunião", "H1"))
story.append(p(
    "Como o orientador já aprovou a linha de pesquisa, esta reunião é uma oportunidade de mostrar "
    "a plataforma funcionando de verdade (o dashboard interativo pode ser aberto ao vivo), "
    "apresentar os achados já consolidados das Fases 2 e 3, e alinhar as três pendências institucionais "
    "da seção 4.2 — que são, hoje, o principal fator que define o cronograma das fases restantes."
))

story.append(Spacer(1, 16))
story.append(p(
    "Documentos de apoio (mesma pasta de pesquisa): Plano_TCC_Luiz.pdf (plano completo), "
    "Capitulo_Fase2_Resultados.pdf, Capitulo_Fase3_Resultados.pdf, "
    "Roteiro_Apresentacao_Orientador.pdf.",
    "CorpoTabelaNota",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="LexHub + TCC Luiz Reis - Status do Projeto",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
