"""Marketing (banco NG) + LexPre: a soma do comercial que passou do banco NG legado para o LexPre.

Desde set/2026 os atendimentos comerciais da NG são registrados no LexPre; a tabela public.actions do banco NG
parou de receber atendimentos em 22/10/2026. Sem a soma, o Marketing (banco NG) zera clientes, leads, indicação,
retorno, campanha e CAC no período novo. Aqui entram, somados aos do legado, os números do Marketing (LexPre) do
escritório da NG (cálculo da v1 em app/analyses/NG/marketing_lexpre.py), com a correspondência:

  * campanha do LexPre (canal "anúncio"; a campanha RA foi descontinuada) -> campanha NG do legado;
  * contagens e valores: somados; gráficos: somados pelo nome (sem diferença de maiúsculas);
  * médias (idade): ponderadas pela quantidade de clientes de cada lado;
  * razões (conversão, ticket, aproveitamento, CPL, taxa de fechamento): recalculadas sobre as somas, com a regra
    do legado (ex.: ticket = valor de causa ÷ ações);
  * CAC e ROAS: os dois lados dividem o mesmo valor gasto (a tabela de anúncios da NG), então o ROAS soma e o
    CAC combina pelos clientes (gasto ÷ CAC de cada lado);
  * Facebook Ads (gasto, cliques, pageview, leads e a série por dia): a mesma tabela nos dois, não soma;
  * funil de pipeline e dispositivo: só existem no legado (o LexPre não tem essas etapas nem o dispositivo).

Conferido em 25/11/2026: de 135 clientes fechados no legado e 524 assinados no LexPre (NG) desde 15/08/2026, só 5
nomes aparecem nos dois, em meses diferentes (clientes que voltaram): a soma não conta o mesmo contrato duas vezes.
"""

from typing import Any

P_NG = "marketing_ng_"
P_LX = "marketing_lexpre_ng_"

# Campanha do LexPre -> campanha NG do legado.
RENOMEAR = {
    "campanha": "campanha_ng",
    "protocolados_campanha": "protocolados_ng",
    "valor_causa_campanha": "valor_causa_ng",
    "leads_campanha": "leads_ng",
    "acoes_campanha": "acoes_ng",
}

# Contagens e valores que somam (nomes do legado, sem o prefixo).
SOMA = (
    "total_clientes",
    "triados_total_clientes",
    "clientes_campanha",
    "leads",
    "indicacao_ativa",
    "indicacao_passiva",
    "retorno_ativa",
    "retorno_passiva",
    "total_trackeamento",
    "processos_assinados",
    "org_leads_facebook",
    "org_leads_instagram",
    "org_leads_site",
    "org_leads_google",
    "org_total_leads",
    "org_contratos",
    "org_acoes",
    "org_valor_causa",
    *RENOMEAR.values(),
)

# Gráficos que não somam: a mesma tabela de anúncios nos dois lados, ou só existem no legado.
GRAFICOS_SEM_SOMA = {"investimento_cliques_leads", "funil_pipeline", "dispositivo", "triados_dispositivo"}
# Gráficos RA x NG do legado: o LexPre entra na parte NG.
GRAFICOS_RA_NG = {"rubrica_campanha", "rubrica_protocolado"}
# Roscas por campanha: "Campanha" do LexPre = "NG" do legado.
GRAFICOS_POR_CAMPANHA = {"total_clientes_campanha", "protocolo_resolvido_total", "valor_causa_total"}


def _num(v: Any) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else 0.0


def _div(a: float, b: float, casas: int = 2) -> float:
    return round(a / b, casas) if b else 0.0


def _chave(nome: Any) -> str:
    return str(nome or "").strip().upper()


def _somar_pontos(
    legado: list[dict] | None, lexpre: list[dict] | None, renomear: dict[str, str] | None = None
) -> list[dict]:
    """Soma duas séries {name, value} pelo nome (sem diferença de maiúsculas; vale o nome do legado), da maior
    para a menor."""
    total: dict[str, dict] = {}
    for p in legado or []:
        total[_chave(p.get("name"))] = {"name": p.get("name"), "value": _num(p.get("value"))}
    for p in lexpre or []:
        nome = (renomear or {}).get(str(p.get("name")), p.get("name"))
        item = total.setdefault(_chave(nome), {"name": nome, "value": 0.0})
        item["value"] += _num(p.get("value"))
    pontos = [
        {"name": p["name"], "value": int(p["value"]) if float(p["value"]).is_integer() else p["value"]}
        for p in total.values()
    ]
    return sorted(pontos, key=lambda p: p["value"], reverse=True)


def _somar_ra_ng(legado: list[dict] | None, lexpre: list[dict] | None) -> list[dict]:
    """Rubricas RA x NG do legado + as do LexPre na parte NG."""
    total: dict[str, dict] = {}
    for p in legado or []:
        total[_chave(p.get("name"))] = {
            "name": p.get("name"),
            "ra": int(_num(p.get("ra"))),
            "ng": int(_num(p.get("ng"))),
        }
    for p in lexpre or []:
        item = total.setdefault(_chave(p.get("name")), {"name": p.get("name"), "ra": 0, "ng": 0})
        item["ng"] += int(_num(p.get("value")))
    return sorted(total.values(), key=lambda p: p["ra"] + p["ng"], reverse=True)


def somar_lexpre(ng: dict[str, Any], lexpre: dict[str, Any]) -> dict[str, Any]:
    """A resposta do Marketing (banco NG) (DashboardResponse da v1, model_dump) com o LexPre somado.

    `lexpre` = a resposta do Marketing (LexPre) do escritório da NG ({"stats": ..., "charts": ...})."""
    out = dict(ng)
    s = dict(ng.get("stats") or {})
    lx_stats = lexpre.get("stats") or {}

    def lx(campo: str) -> float:
        return _num(lx_stats.get(P_LX + campo))

    def legado(campo: str) -> float:
        return _num(s.get(P_NG + campo))

    lx_ng = {RENOMEAR.get(c, c): lx(c) for c in (*SOMA, *RENOMEAR)}

    # Médias de idade ponderadas pelas quantidades de antes da soma.
    for media, base in (("media_idade", "total_clientes"), ("triados_media_idade", "triados_total_clientes")):
        n_leg, n_lx = legado(base), lx(base)
        if n_leg + n_lx:
            s[P_NG + media] = round((legado(media) * n_leg + lx(media) * n_lx) / (n_leg + n_lx), 2)

    for campo in SOMA:
        soma = legado(campo) + lx_ng.get(campo, 0.0)
        s[P_NG + campo] = int(soma) if soma.is_integer() else soma

    # CAC: mesmo gasto dos dois lados -> clientes = gasto ÷ CAC; ROAS: valor ÷ gasto -> soma.
    gasto = legado("facebook_valor_gasto")
    for cac in ("facebook_cac_campanha", "facebook_cac_geral"):
        clientes = sum(_div(gasto, v, 6) for v in (legado(cac), lx(cac)) if v > 0)
        s[P_NG + cac] = _div(gasto, clientes, 6) if clientes else 0.0
    for roas in ("facebook_roas_campanha", "facebook_roas_geral"):
        s[P_NG + roas] = legado(roas) + lx(roas)

    # Razões recalculadas sobre as somas (regras do legado).
    def g(campo: str) -> float:
        return _num(s.get(P_NG + campo))

    s[P_NG + "conversao_ng"] = _div(g("campanha_ng") * 100, g("leads_ng"))
    s[P_NG + "ticket_medio_ng"] = _div(g("valor_causa_ng"), g("acoes_ng"))
    s[P_NG + "aproveitamento_ng"] = _div(g("acoes_ng"), g("campanha_ng"))
    s[P_NG + "cpl_ng"] = _div(gasto, g("leads_ng"))
    s[P_NG + "org_aproveitamento"] = _div(g("org_acoes"), g("org_contratos"))
    s[P_NG + "org_taxa_fechamento"] = _div(g("org_contratos") * 100, g("org_total_leads"))
    s[P_NG + "org_ticket_medio"] = _div(g("org_valor_causa"), g("org_acoes"))
    out["stats"] = s

    # Gráficos: somados pelo nome.
    for chave_lx, pontos in (lexpre.get("charts") or {}).items():
        nome = chave_lx.removeprefix(P_LX)
        if nome in GRAFICOS_SEM_SOMA:
            continue
        if nome in GRAFICOS_RA_NG:
            out[P_NG + nome] = _somar_ra_ng(ng.get(P_NG + nome), pontos)
            # O "Rubricas (ações NG)" da Performance é a campanha NG: o LexPre entra nele também.
            if nome == "rubrica_campanha":
                out[P_NG + "ind_rubricas"] = _somar_pontos(ng.get(P_NG + "ind_rubricas"), pontos)
            continue
        if P_NG + nome not in ng:
            continue  # gráfico que o legado não tem
        renomear = {"Campanha": "NG"} if nome in GRAFICOS_POR_CAMPANHA else None
        out[P_NG + nome] = _somar_pontos(ng.get(P_NG + nome), pontos, renomear)
    return out
