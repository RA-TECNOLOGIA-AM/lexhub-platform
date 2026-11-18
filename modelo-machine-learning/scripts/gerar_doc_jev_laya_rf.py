# -*- coding: utf-8 -*-
"""
Gera a documentacao tecnica comparando Random Forest (Fase 4 planejada) com os
dois modelos classificadores sugeridos pelo orientador: JEV (TypeSafe) e Laya.

Fontes (consultadas em 02/11/2026, ver Secao 6 - Referencias):
  - https://docs.typesafe.ai/introduction
  - https://docs.typesafe.ai/introduction/machine-learning-primer
  - https://docs.typesafe.ai/concepts/system-one
  - https://docs.typesafe.ai/introduction/quickstart
  - https://laya.aay.sh/docs.html

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_doc_jev_laya_rf.py
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
OUT_PDF = f"{BASE_DIR}/Avaliacao_JEV_Laya_RandomForest.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=19, leading=24, fontName="Helvetica-Bold", spaceAfter=6))
styles.add(ParagraphStyle(name="SubtituloCapa", fontSize=13, leading=17, fontName="Helvetica", spaceAfter=14, textColor=colors.HexColor("#333333")))
styles.add(ParagraphStyle(name="AutorData", fontSize=10.5, leading=14, fontName="Helvetica"))
styles.add(ParagraphStyle(name="NotaRodapeCapa", fontSize=9, leading=13, fontName="Helvetica-Oblique", textColor=colors.HexColor("#555555"), spaceBefore=18))
styles.add(ParagraphStyle(name="H1", fontSize=14, leading=18, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="H2", fontSize=11.5, leading=15, fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=14.5, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8))
styles.add(ParagraphStyle(name="CorpoTabelaNota", fontSize=8.5, leading=12, fontName="Helvetica-Oblique", textColor=colors.HexColor("#444444"), alignment=TA_JUSTIFY, spaceAfter=10))
styles.add(ParagraphStyle(name="Destaque", fontSize=10.5, leading=15, fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=8, backColor=colors.HexColor("#eef0ff"), borderPadding=8))
styles.add(ParagraphStyle(name="CelulaTabela", fontSize=8.6, leading=11.5, fontName="Helvetica"))
styles.add(ParagraphStyle(name="CelulaTabelaBold", fontSize=8.6, leading=11.5, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Referencia", fontSize=9.5, leading=14, fontName="Helvetica", leftIndent=14, firstLineIndent=-14, spaceAfter=6))

COR_CABECALHO = colors.HexColor("#2d3142")
COR_ALT = colors.HexColor("#f2f2f5")
COR_OK = "#1e8e5a"
COR_NAO = "#b3261e"
COR_PARCIAL = "#b9770e"


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.3 * cm, "TCC Luiz Reis — Avaliação técnica: Random Forest × JEV × Laya")
    canvas.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


def p(texto, estilo="Corpo"):
    return Paragraph(texto, styles[estilo])


def lista(itens):
    return ListFlowable(
        [ListItem(Paragraph(item, styles["Corpo"]), bulletColor=colors.HexColor("#2d3142")) for item in itens],
        bulletType="bullet", leftIndent=14,
    )


def tag(texto, cor_hex):
    return Paragraph(f'<font color="{cor_hex}"><b>{texto}</b></font>', styles["CelulaTabela"])


def tabela(linhas, col_widths, header=True):
    data = []
    for i, linha in enumerate(linhas):
        row = []
        for cel in linha:
            if isinstance(cel, str):
                estilo_nome = "CelulaTabelaBold" if (header and i == 0) else "CelulaTabela"
                row.append(Paragraph(cel, styles[estilo_nome]))
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
            ("BACKGROUND", (0, 0), (-1, 0), COR_CABECALHO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    for i in range(1 if header else 0, len(data)):
        if (i - (1 if header else 0)) % 2 == 1:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_ALT))
    t.setStyle(TableStyle(estilo))
    return t


story = []

# ---------------------------------------------------------------------------
# CAPA
# ---------------------------------------------------------------------------
story.append(Spacer(1, 2.8 * cm))
story.append(p("Avaliação Técnica de Alternativas para a Fase 4", "TituloCapa"))
story.append(p(
    "Random Forest (plano original) vs. JEV (TypeSafe) vs. Laya — viabilidade para classificação/previsão "
    "de desfecho processual",
    "SubtituloCapa",
))
story.append(Spacer(1, 1 * cm))
story.append(p("Autor: Luiz Reis<br/>Novembro de 2026", "AutorData"))
story.append(Spacer(1, 1.6 * cm))
story.append(p(
    "Documento preparado a pedido do orientador, que sugeriu avaliar dois modelos classificadores "
    "— JEV (TypeSafe, docs.typesafe.ai) e Laya (laya.aay.sh) — como possíveis alternativas ou "
    "complementos ao Random Forest já planejado para a Fase 4 do TCC. A análise é baseada em leitura "
    "direta da documentação oficial de ambos os produtos (consultada em 02/11/2026), não em "
    "conhecimento prévio — ver Seção 6 para as páginas exatas consultadas.",
    "NotaRodapeCapa",
))
story.append(PageBreak())

# ---------------------------------------------------------------------------
# 1. CONTEXTO
# ---------------------------------------------------------------------------
story.append(p("1. Contexto e objetivo", "H1"))
story.append(p(
    "O plano original do TCC (Fase 4) prevê um modelo de aprendizado de máquina — Random Survival "
    "Forest e/ou XGBoost-AFT — ajustado sobre a mesma coorte de processos já usada nas Fases 2 e 3 "
    "(tipo de ação, matéria, valor de causa, escritório, comarca, competência), para comparar seu "
    "poder preditivo contra o baseline estatístico (Cox/Fine-Gray). O orientador apontou dois produtos "
    "— JEV e Laya — como possíveis modelos classificadores a considerar. Este documento avalia os "
    "três (Random Forest, JEV, Laya) quanto à viabilidade técnica e metodológica para esse uso "
    "específico: prever/classificar o desfecho de um processo judicial a partir dos dados estruturados "
    "já extraídos do LexFlow."
))
story.append(p(
    "<b>Pergunta que orienta a avaliação:</b> o modelo consegue ser treinado nos ~40 mil processos "
    "históricos do LexFlow e produzir uma previsão calibrada e auditável para um processo novo, de um "
    "jeito que sustente uma seção de resultados de TCC (métricas como C-index, Brier Score, validação "
    "temporal) — ou ele resolve um problema diferente?",
    "Destaque",
))

# ---------------------------------------------------------------------------
# 2. RANDOM FOREST
# ---------------------------------------------------------------------------
story.append(p("2. Random Forest / Random Survival Forest (plano original)", "H1"))
story.append(p(
    "Random Forest é um algoritmo de aprendizado supervisionado clássico: um conjunto (ensemble) de "
    "árvores de decisão, cada uma treinada sobre uma amostra bootstrap dos dados e um subconjunto "
    "aleatório de variáveis, cuja previsão final é a média (regressão) ou votação (classificação) das "
    "árvores individuais. A variante usada em análise de sobrevivência — Random Survival Forest (RSF) "
    "— adapta o critério de divisão de cada árvore para maximizar a separação de curvas de "
    "sobrevivência entre os grupos, em vez de erro quadrático ou impureza de classe, continuando a "
    "lidar corretamente com censura."
))
story.append(p(
    "<b>Por que se encaixa no projeto:</b> RSF (ou XGBoost-AFT) é treinado diretamente sobre a mesma "
    "coorte e as mesmas covariáveis já usadas no Cox/Fine-Gray — o que permite uma comparação "
    "direta e justa de poder preditivo (mesmo C-index, mesmo split temporal, mesmos dados). É "
    "biblioteca aberta (scikit-survival, xgbse), roda localmente, sem custo de API, sem enviar dado "
    "de processo nenhum pra fora do ambiente de pesquisa, e com literatura acadêmica extensa "
    "(Ishwaran et al., 2008, é a referência original de RSF) — o tipo de citação que uma banca espera."
))

# ---------------------------------------------------------------------------
# 3. JEV
# ---------------------------------------------------------------------------
story.append(p("3. JEV (TypeSafe)", "H1"))
story.append(p("3.1 O que é", "H2"))
story.append(p(
    "JEV é descrito na própria documentação como <i>\"TypeSafe's flagship model and the first "
    "'System One' model\"</i> — uma classe de modelo que a TypeSafe define como construída para "
    "<i>\"fast, structured decisions that software can use directly\"</i>, em contraste explícito com "
    "um LLM generativo tradicional: em vez de gerar texto livre para um humano ler, o JEV recebe um "
    "<b>state</b> (os dados a avaliar, em texto livre ou JSON) e um conjunto de <b>questions</b> "
    "tipadas, e devolve respostas estruturadas diretamente consumíveis por código — sem geração nem "
    "parsing de texto. O nome é uma referência à dicotomia \"Sistema 1 / Sistema 2\" de Kahneman "
    "(pensamento rápido e intuitivo vs. lento e deliberado): o JEV se posiciona como o \"Sistema 1\" — "
    "julgamentos rápidos e focados, não raciocínio estendido."
))
story.append(p("3.2 Como funciona", "H2"))
story.append(p(
    "Cada requisição envia um <i>state</i> e uma ou mais <i>questions</i>, cada uma de um de três "
    "tipos: <b>Choice</b> (escolher uma opção de uma lista, retorna choice/probabilities/confidence), "
    "<b>Score</b> (pontuar segundo uma rubrica, retorna score/probabilities/confidence) e <b>Noul</b> "
    "(verificar se uma afirmação é verdadeira, retorna um valor de 0 a 1). As perguntas são avaliadas "
    "em paralelo contra o mesmo state numa única chamada de API (<code>POST "
    "https://api.typesafe.ai/v1/systemone</code>), com SDKs oficiais em Python e JavaScript/TypeScript, "
    "além de acesso direto via cURL. O modelo é treinado pela própria TypeSafe com uma técnica "
    "própria chamada RLCD, que a documentação descreve como treinando <i>\"TypeSafe to return "
    "decisions and calibrated probabilities instead of generated text\"</i>."
))
story.append(p("3.3 Ponto crítico para este projeto: não é treinável pelo usuário", "H2"))
story.append(p(
    "A documentação completa consultada (introdução, conceito de System One, AI/ML primer, "
    "quickstart) <b>não descreve, em nenhum momento, um mecanismo de treinamento ou fine-tuning do "
    "modelo com dados próprios do usuário</b>. O que existe é um modelo pré-treinado e fixo "
    "(mantido pela TypeSafe), consultado por inferência: você escreve, em linguagem natural, os "
    "critérios de cada <i>question</i> (ex.: a rubrica de um Score, as opções de um Choice), e o "
    "modelo julga o <i>state</i> fornecido contra esses critérios usando seu próprio conhecimento "
    "geral — não um conhecimento aprendido a partir do histórico de ~40 mil processos do LexFlow. "
    "A documentação é explícita sobre o que a calibração significa: <i>\"Calibration is measured "
    "across groups of predictions; it does not guarantee that an individual answer is correct\"</i> — "
    "uma propriedade estatística de como a TypeSafe avalia seu próprio modelo em suas próprias "
    "tarefas de benchmark, não uma métrica calculada sobre a coorte deste TCC."
))
story.append(p(
    "Isso muda fundamentalmente o que seria avaliado: em vez de \"ajustar um modelo estatístico à "
    "nossa coorte e medir seu poder preditivo\" (o que Cox, Fine-Gray e Random Forest fazem todos "
    "da mesma forma, permitindo comparação direta), usar o JEV seria \"perguntar a um serviço de "
    "julgamento de terceiros, por um prompt em linguagem natural, se um processo com tais "
    "características parece favorável\" — sem nenhuma garantia de que esse julgamento reflete os "
    "padrões empíricos reais da Vara Cível de Manaus ou do Juizado Especial Cível. Não há como "
    "calcular C-index ou Brier Score de um jeito metodologicamente comparável ao Cox/Fine-Gray/RSF, "
    "porque o JEV não está sendo <i>ajustado</i> a dado nenhum — está sendo <i>consultado</i>."
))
story.append(p("3.4 Outras limitações observadas", "H2"))
story.append(lista([
    "Entrada só em texto: a página de conceito do System One afirma \"Jev currently accepts text "
    "input only\" — imagem, áudio e vídeo \"are not supported (yet)\"; dado tabular precisaria ser "
    "serializado como texto/JSON dentro do state, perdendo a estrutura numérica que uma árvore de "
    "decisão usa diretamente.",
    "Sem explicação do raciocínio: o modelo \"do not write replies, produce code, or generate "
    "explanations of their reasoning\" — dificulta justificar o resultado numa banca.",
    "Preço e limites de uso (rate limits, quotas) não estão documentados publicamente — não dá pra "
    "orçar o custo de rodar a coorte inteira antes de testar.",
    "Dependência de serviço externo pago (requer API key, conta na TypeSafe) — introduz um ponto de "
    "falha e um custo recorrente fora do controle do pesquisador, além da questão de enviar dados de "
    "processos (mesmo pseudonimizados) para infraestrutura de terceiros.",
    "Nenhuma citação acadêmica (paper, benchmark publicado) encontrada na documentação — ao contrário "
    "de RSF/XGBoost-AFT, que têm artigos revisados por pares como referência.",
]))

# ---------------------------------------------------------------------------
# 4. LAYA
# ---------------------------------------------------------------------------
story.append(p("4. Laya", "H1"))
story.append(p(
    "O Laya <b>não é um modelo classificador</b> — é um produto completamente diferente do que o "
    "nome sugere neste contexto. A própria documentação o descreve como <i>\"an open-source, "
    "local-first AI command center\"</i>: uma ferramenta de automação que intercepta notificações de "
    "aplicativos profissionais (Gmail, Slack, Jira, GitHub, Calendar, Outlook, Notion etc.), processa "
    "cada evento num pipeline de várias etapas (Ingest → Rules → Router → Workers → Stager → Emit → "
    "...) e gera \"Action Cards\" para o usuário aprovar. Os modelos de linguagem que fazem o "
    "julgamento em cada etapa são de terceiros — Anthropic, OpenAI, Google, OpenRouter, Ollama, LM "
    "Studio — configurados pelo próprio usuário com suas próprias chaves de API; o Laya é a camada de "
    "orquestração (Engine em Python/FastAPI, UI em Svelte/Tauri, gateway n8n), não o modelo em si."
))
story.append(p(
    "Há, sim, uma etapa de \"classificação\" no pipeline (o componente Router classifica eventos por "
    "prioridade — CRITICAL/HIGH/MEDIUM/LOW — e por categoria/persona), mas é classificação de eventos "
    "de notificação (um e-mail, um PR, uma mensagem de Slack), não de dados tabulares nem de desfecho "
    "de processo. A documentação não menciona domínio jurídico, dados tabulares como entrada, nem "
    "qualquer mecanismo de treinamento ou fine-tuning — o comportamento é inteiramente baseado em "
    "prompts (customizáveis via arquivos em <code>~/.laya/prompts/</code>), com um \"learning "
    "pipeline\" que extrai regras em linguagem natural a partir de correções do usuário e as "
    "realimenta nos prompts — não há atualização de pesos de modelo nenhuma."
))
story.append(p(
    "<b>Conclusão sobre o Laya:</b> é uma ferramenta de produtividade pessoal/triagem de notificações, "
    "não um modelo preditivo e não tem nenhuma funcionalidade aplicável a prever desfecho ou duração "
    "de processos judiciais a partir de dados estruturados. Não há comparação metodológica "
    "significativa a fazer com Random Forest ou JEV neste eixo — são categorias de produto diferentes.",
    "Destaque",
))

# ---------------------------------------------------------------------------
# 5. COMPARACAO
# ---------------------------------------------------------------------------
story.append(PageBreak())
story.append(p("5. Comparação direta", "H1"))
story.append(tabela(
    [
        ["Critério", "Random Forest / RSF", "JEV", "Laya"],
        ["Treinável com dado próprio (coorte LexFlow)",
         tag("Sim", COR_OK), tag("Não documentado", COR_NAO), tag("Não se aplica", COR_NAO)],
        ["Tipo de entrada nativo",
         "Tabular/numérico", "Texto/JSON (modelo de texto)", "Eventos de notificação (JSON/texto)"],
        ["Métrica comparável ao Cox/Fine-Gray (C-index, Brier)",
         tag("Sim", COR_OK), tag("Não", COR_NAO), tag("Não se aplica", COR_NAO)],
        ["Roda localmente / sem custo de API",
         tag("Sim", COR_OK), tag("Não (API paga)", COR_NAO), tag("Parcial (LLM externo opcional)", COR_PARCIAL)],
        ["Dado sai do ambiente de pesquisa",
         tag("Não", COR_OK), tag("Sim", COR_NAO), tag("Não se aplica", COR_NAO)],
        ["Preço documentado publicamente",
         "Gratuito (biblioteca aberta)", tag("Não", COR_NAO), "Open-source; custo é do provedor de LLM"],
        ["Base acadêmica / citável",
         "Ishwaran et al. 2008 (RSF)", tag("Não encontrada", COR_NAO), tag("Não se aplica", COR_NAO)],
        ["Domínio documentado como caso de uso",
         "Genérico (estatística/ML)", "Decisões de negócio genéricas", "Triagem de notificações profissionais"],
        ["Adequação ao objetivo da Fase 4",
         tag("Alta", COR_OK), tag("Baixa", COR_NAO), tag("Nenhuma", COR_NAO)],
    ],
    [5.3 * cm, 3.6 * cm, 3.6 * cm, 3.7 * cm],
))
story.append(Spacer(1, 8))
story.append(p(
    "A linha mais decisiva da tabela é a primeira: o objetivo da Fase 4, desde o plano original, é "
    "<i>ajustar</i> um modelo aos dados históricos do LexFlow e medir seu poder preditivo contra o "
    "baseline estatístico — exatamente o que Cox e Fine-Gray já fazem. RSF cumpre esse requisito por "
    "desenho. JEV, pela documentação disponível, não oferece esse mecanismo: é consultado, não "
    "ajustado. Sem isso, não há como produzir uma seção de resultados comparável (mesma coorte, "
    "mesmo split temporal, mesma métrica) — o que inviabiliza seu uso como \"o modelo de ML da Fase "
    "4\" de um jeito que sustente a defesa do TCC."
))

# ---------------------------------------------------------------------------
# 6. RECOMENDACAO
# ---------------------------------------------------------------------------
story.append(p("6. Recomendação", "H1"))
story.append(lista([
    "<b>Manter Random Survival Forest / XGBoost-AFT como planejado</b> para a Fase 4 — é o único dos "
    "três que atende ao requisito central (treinar sobre a coorte própria e produzir uma métrica "
    "comparável ao Cox/Fine-Gray).",
    "<b>Não usar o Laya</b> — não é um modelo classificador, é uma ferramenta de automação de "
    "notificações; não há enquadramento razoável para o problema deste TCC.",
    "<b>Não usar o JEV como modelo da Fase 4</b>, pela ausência documentada de um mecanismo de "
    "treinamento com dado próprio — sem isso, os resultados não seriam cientificamente comparáveis "
    "aos demais modelos do trabalho.",
    "<b>Registrar o JEV como ideia para trabalho futuro, fora do escopo do TCC:</b> o conceito de "
    "\"System One model\" — decisões tipadas e calibradas, sem geração de texto — é "
    "conceitualmente interessante para uma função bem diferente: um assistente de triagem em "
    "produção no próprio LexHub (ex.: Sinalizar favoravelmente/desfavoravelmente um processo novo "
    "pra um advogado revisar, combinando julgamento qualitativo com os coeficientes já calibrados do "
    "Cox/RSF). Isso seria um produto de engenharia de software sobre o resultado da pesquisa, não um "
    "substituto do modelo estatístico da pesquisa em si.",
    "<b>Antes de descartar completamente</b>: se o orientador insistir em ver o JEV testado "
    "empiricamente, a forma honesta de fazer isso seria um experimento à parte, claramente rotulado "
    "como exploratório (não parte do modelo formal da Fase 4), comparando o julgamento do JEV num "
    "subconjunto pequeno de processos contra o desfecho real já conhecido — mas isso exigiria criar "
    "conta paga na TypeSafe, cujo custo e limites de uso não são públicos.",
]))

# ---------------------------------------------------------------------------
# REFERENCIAS
# ---------------------------------------------------------------------------
story.append(PageBreak())
story.append(p("7. Referências e fontes consultadas", "H1"))
story.append(p(
    "Todo o conteúdo técnico sobre JEV e Laya neste documento foi extraído diretamente das páginas "
    "abaixo (consulta em 02/11/2026), não de conhecimento prévio sobre os produtos:",
    "Corpo",
))
for ref in [
    "TypeSafe. <i>Introduction</i>. Disponível em: https://docs.typesafe.ai/introduction.",
    "TypeSafe. <i>Concepts — System One</i>. Disponível em: https://docs.typesafe.ai/concepts/system-one.",
    "TypeSafe. <i>Machine Learning Primer</i>. Disponível em: "
    "https://docs.typesafe.ai/introduction/machine-learning-primer.",
    "TypeSafe. <i>Quickstart</i>. Disponível em: https://docs.typesafe.ai/introduction/quickstart.",
    "Laya. <i>Documentation</i>. Disponível em: https://laya.aay.sh/docs.html.",
    "ISHWARAN, H. et al. Random Survival Forests. <i>The Annals of Applied Statistics</i>, v. 2, n. 3, "
    "p. 841-860, 2008. (Referência acadêmica do método já planejado para a Fase 4.)",
]:
    story.append(p(ref, "Referencia"))

story.append(Spacer(1, 10))
story.append(p(
    "Este documento complementa o Plano_TCC_Luiz.pdf e os capítulos de resultados das Fases 2 e 3, na "
    "mesma pasta de pesquisa.",
    "CorpoTabelaNota",
))

doc = SimpleDocTemplate(
    OUT_PDF, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    title="TCC Luiz Reis - Avaliação Técnica: Random Forest x JEV x Laya",
)
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {OUT_PDF}")
