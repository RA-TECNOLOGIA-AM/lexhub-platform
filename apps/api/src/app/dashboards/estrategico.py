"""Estratégico (área Estratégico) — a página da v1 GERAL/Estrategico.tsx, por unidade.

A v1 não tem rota própria: a página fazia até 24 chamadas (Comercial, Protocolo e os setores do pré-protocolo de cada
escritório, nos bancos legados e no LexPre, e o Jurídico do LexFlow com e sem período) e somava no navegador. Aqui a
API faz as mesmas chamadas, com as rotas copiadas sem mudança, e devolve as somas prontas.

Diferença da v1 (regra da V2: cada unidade vê só o próprio escritório): a v1 juntava NG, LA e RJ numa tela com o
filtro de escritório (NGAM, NGPA, NGPB, LAAM, LARJ). Aqui cada unidade vê os próprios números; na NG os escritórios
NGAM/NGPA/NGPB viram o filtro de UF (AM, PA, PB), como a v1 fazia por baixo. O LexPre entra em toda unidade que tem o
banco ligado (a v1 ainda não somava o LexPre do RJ).

Seções (as da v1):
  01 Comercial — contratos e ações fechadas no período (legado + LexPre) e as séries mês a mês / dia a dia (sem
     período);
  02 Protocolo — represados no pré-protocolo (estoque de agora: org. de documentos, pendências, protocolo e
     peticionamento), protocolados, valor de causa e ticket médio no período, e as séries;
  03 Jurídico com período e 04 Jurídico fixo — /estrategico_geral da v1 (LexFlow, cópia em
     app/analyses/v1_dashboard_estrategico_geral.py) com o escritório da unidade, com e sem o período.

Rotas da v1 por unidade:
  NG — banco NG: /comercial, /protocolo, /org-documentos, /pendencias, /peticionamento (uma chamada por UF escolhida,
       somadas, como a v1); LexPre escritório 1; Jurídico "Nicolas Gomes" (com as UFs).
  LA — banco LAADV: /comercial_LA (cópia em app/analyses/v1_dashboard_comercial_la.py), /protocolo_LA, /org_doc_LA,
       /pendencia_LA, /peticionamento_LA; LexPre escritório 2; Jurídico "Luis Albert AM".
  RJ — banco NG: /comercial_RJ, /protocolo_RJ, /org_doc_RJ, /pendencias_RJ, /peticionamento_RJ; LexPre escritório 3;
       Jurídico "Luis Albert RJ".

Fora desta versão: o filtro de área de atuação da v1 (o legado filtra por id da tabela dele e o LexPre/LexFlow pelo
nome; falta o de-para).
"""

import re
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date
from types import ModuleType
from typing import Any

from app.analyses import v1_dashboard_comercial_la as v1_comercial_la
from app.analyses import v1_dashboard_estrategico_geral as v1_juridico
from app.analyses import v1_dashboard_generico_la as v1_la
from app.analyses import v1_dashboard_generico_ng as v1_ng
from app.analyses.NG import comercial_lexpre as com_lexpre
from app.analyses.NG import (
    org_doc_lexpre,
    pendencia_setor_lexpre,
    peticionamento_lexpre,
    protocolo_setor_lexpre,
)
from app.analyses.NG import protocolo_lexpre as prot_lexpre
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardInputError, DashboardModule, NotReady

FILTRO_UF = "uf_estrategico"  # só NG: AM | PA | PB (os escritórios NGAM/NGPA/NGPB da v1)
FILTRO_COMARCA = "comarca_estrategico"  # só o Jurídico
FILTRO_SITUACAO = "situacao_estrategico"  # só o Jurídico: ATIVO | ARQUIVADO | SUSPENSO/SOBRESTADO
UFS_NG = ("AM", "PA", "PB")
SITUACOES = ("ATIVO", "ARQUIVADO", "SUSPENSO/SOBRESTADO")


@dataclass(frozen=True)
class Legado:
    """As rotas da v1 de um banco legado e os nomes dos campos que elas devolvem."""

    banco: str  # 'ng' | 'laadv'
    comercial: tuple[ModuleType, str]
    protocolo: tuple[ModuleType, str]
    org_doc: tuple[ModuleType, str]
    pendencias: tuple[ModuleType, str]
    peticionamento: tuple[ModuleType, str]
    campos: dict[str, str]  # nome comum -> nome na rota
    uf: dict[str, str]  # rota -> parâmetro de UF (só NG)


CAMPOS_NG = {
    "contratos": "clientes_todos",
    "contratos_anterior": "clientes_todos_periodo_anterior",
    "acoes": "acoes_fechadas",
    "acoes_anterior": "acoes_fechadas_periodo_anterior",
    "contratos_por_mes": "contratos_fechados_por_mes",
    "acoes_por_mes": "processos_fechados_por_mes",
    "contratos_por_dia": "contratos_fechados_por_dia",
    "acoes_por_dia": "acoes_fechadas_por_dia",
    "protocolados": "protocolos_resolvidos",
    "protocolados_anterior": "protocolos_resolvidos_periodo_anterior",
    "valor_causa": "valor_causa_protocolo_novo",
    "valor_causa_anterior": "valor_causa_protocolo_periodo_anterior",
    "ticket_medio": "ticket_medio_protocolos_resolvidos",
    "protocolados_por_mes": "protocolados_por_mes",
    "protocolados_por_dia": "protocolados_por_dia",
    "valor_causa_por_mes": "valor_causa_protocolados_por_mes",
    "valor_causa_por_dia": "valor_causa_protocolados_por_dia",
    "represados_org_doc": "nao_organizados",
    "represados_pendencias": "pendencias_nao_resolvidas",
    "represados_protocolo": "nao_protocolados",
    "represados_peticionamento": "nao_peticionados",
}
CAMPOS_LA = {
    "contratos": "clientes_todos_LA",
    "contratos_anterior": "clientes_total_periodo_anterior_LA",
    "acoes": "acoes_fechadas_LA",
    "acoes_anterior": "acoes_fechadas_periodo_anterior_LA",
    "contratos_por_mes": "contratos_fechados_por_mes_LA",
    "acoes_por_mes": "processos_fechados_por_mes_LA",
    "contratos_por_dia": "contratos_fechados_por_dia_LA",
    "acoes_por_dia": "acoes_fechadas_por_dia_LA",
    "protocolados": "protocolos_resolvidos_LA",
    "protocolados_anterior": "protocolos_resolvidos_periodo_anterior_LA",
    "valor_causa": "valor_causa_protocolado_LA",
    "valor_causa_anterior": "valor_causa_protocolado_periodo_anterior_LA",
    "ticket_medio": "ticket_medio_protocolos_resolvidos_LA",
    "protocolados_por_mes": "protocolados_por_mes_LA",
    "protocolados_por_dia": "protocolados_por_dia_LA",
    "valor_causa_por_mes": "valor_causa_protocolados_por_mes_LA",
    "valor_causa_por_dia": "valor_causa_protocolados_por_dia_LA",
    "represados_org_doc": "nao_organizados_LA",
    "represados_pendencias": "pendencias_nao_resolvidas_LA",
    "represados_protocolo": "protocolos_represados_LA",
    "represados_peticionamento": "nao_confeccionados_LA",
}

UF_NG = {
    "comercial": "uf_comercial_ng",
    "protocolo": "uf_protocolo",
    "org-documentos": "uf_org_doc",
    "pendencias": "uf_pendencias",
    "peticionamento": "uf_peticionamento",
}


@dataclass(frozen=True)
class Rota:
    legado: Legado
    escritorio_juridico: str  # ESCRITORIO (razão social) no LexFlow, como a v1 mandava
    tem_uf: bool


ROTAS = {
    "NG": Rota(
        Legado(
            "ng",
            (v1_ng, "comercial"),
            (v1_ng, "protocolo"),
            (v1_ng, "org-documentos"),
            (v1_ng, "pendencias"),
            (v1_ng, "peticionamento"),
            CAMPOS_NG,
            UF_NG,
        ),
        "Nicolas Gomes",
        True,
    ),
    "LA": Rota(
        Legado(
            "laadv",
            (v1_comercial_la, "comercial_LA"),
            (v1_la, "protocolo_LA"),
            (v1_la, "org_doc_LA"),
            (v1_la, "pendencia_LA"),
            (v1_la, "peticionamento_LA"),
            CAMPOS_LA,
            {},
        ),
        "Luis Albert AM",
        False,
    ),
    "RJ": Rota(
        Legado(
            "ng",
            (v1_ng, "comercial_RJ"),
            (v1_ng, "protocolo_RJ"),
            (v1_ng, "org_doc_RJ"),
            (v1_ng, "pendencias_RJ"),
            (v1_ng, "peticionamento_RJ"),
            CAMPOS_NG,
            {},
        ),
        "Luis Albert RJ",
        False,
    ),
}

# Queries do LexPre do resumo (v1: _build_comercial_lexpre_resumo_estrategico_geral).
QUERIES_LEXPRE = (
    "comercial_lexpre_NG",
    "demanda_rubrica_reunida_lexpre_NG",
    "log_setor_demanda_lexpre_NG",
)

# --------------------------------------------------------------------------------------------------------------------
# Séries mensais e diárias: cada banco escreve o mês de um jeito ("jan 2026", "2026-01", "01/2026"...); a soma junta
# pelo mês de verdade, como a v1 (formatMonthlyDataByYear / parseDailyChartDate), e devolve "AAAA-MM" e "AAAA-MM-DD".
# --------------------------------------------------------------------------------------------------------------------

_MESES = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


def _ano(texto: str) -> int:
    return int(f"20{texto}") if len(texto) == 2 else int(texto)


def chave_mes(nome: str) -> str | None:
    """O mês de um ponto ("jan 2026", "janeiro 26", "2026-01", "01/2026", "2026/01") como "AAAA-MM"."""
    s = str(nome or "").strip()
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})(?:-\d{1,2})?", s):
        ano, mes = int(m[1]), int(m[2])
    elif m := re.search(r"(\w+)\s+(\d{4}|\d{2})$", s):
        nome_mes = m[1].lower()
        idx = next(
            (
                i
                for i, n in enumerate(_MESES)
                if n.startswith(nome_mes) or nome_mes.startswith(n[:3])
            ),
            None,
        )
        if idx is None:
            return None
        ano, mes = _ano(m[2]), idx + 1
    elif m := re.fullmatch(r"(\d{1,2})/(\d{4}|\d{2})", s):
        ano, mes = _ano(m[2]), int(m[1])
    elif m := re.fullmatch(r"(\d{4})/(\d{1,2})", s):
        ano, mes = int(m[1]), int(m[2])
    else:
        return None
    return f"{ano:04d}-{mes:02d}" if 1 <= mes <= 12 else None


def chave_dia(nome: str) -> str | None:
    """O dia de um ponto ("2026-01-05", "05/01/2026", "2026/01/05") como "AAAA-MM-DD".

    V2: o ano na frente é lido antes do dd/mm/aa (na v1, "2026/01/05" casava como 26/01/05)."""
    s = str(nome or "").strip()
    if m := re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s):
        ano, mes, dia = int(m[1]), int(m[2]), int(m[3])
    elif m := re.search(r"(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})", s):
        ano, mes, dia = _ano(m[3]), int(m[2]), int(m[1])
    else:
        return None
    return f"{ano:04d}-{mes:02d}-{dia:02d}"


def somar_series(series: list[Any], chave: Any) -> list[dict[str, Any]]:
    """Soma várias séries [{name, value}] pela chave (mês ou dia), em ordem cronológica."""
    total: dict[str, float] = defaultdict(float)
    for serie in series:
        for ponto in serie or []:
            p = ponto if isinstance(ponto, dict) else getattr(ponto, "__dict__", {})
            k = chave(p.get("name"))
            if k is not None:
                total[k] += float(p.get("value") or 0)
    return [{"name": k, "value": round(v, 2)} for k, v in sorted(total.items())]


# --------------------------------------------------------------------------------------------------------------------
# Leitura das rotas da v1
# --------------------------------------------------------------------------------------------------------------------


def _campo(resposta: dict[str, Any], nome: str) -> Any:
    if resposta.get(nome) is not None:
        return resposta[nome]
    return (resposta.get("stats") or {}).get(nome)


def _num(v: Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


async def _rota(
    ctx: DashboardContext,
    copia: ModuleType,
    nome: str,
    de: date | None,
    ate: date | None,
    **filtros: Any,
) -> dict[str, Any]:
    fn = copia.HANDLERS[nome]
    params = generico_v1._parametros(fn)
    todos = dict.fromkeys(params)
    todos.update({k: v for k, v in filtros.items() if k in params})
    resposta = await generico_v1.chamar_v1(ctx, copia, fn, from_date=de, to_date=ate, **todos)
    return resposta.model_dump()


def filtros_da_pagina(
    ctx: DashboardContext, tem_uf: bool
) -> tuple[list[str], list[str], list[str]]:
    """(UFs, comarcas, situações) da URL. UF só na NG; todas as UFs = nenhuma (uma chamada só, como a v1)."""
    ufs = sorted(
        {str(u).strip().upper() for u in ctx.filters.get(FILTRO_UF) or [] if str(u).strip()}
    )
    invalidas = [u for u in ufs if u not in UFS_NG]
    if invalidas:
        raise DashboardInputError(f"UF inválida: {', '.join(invalidas)}. Use AM, PA ou PB.")
    if not tem_uf or set(ufs) == set(UFS_NG):
        ufs = []
    comarcas = [str(c).strip() for c in ctx.filters.get(FILTRO_COMARCA) or [] if str(c).strip()]
    situacoes = [
        str(s).strip().upper() for s in ctx.filters.get(FILTRO_SITUACAO) or [] if str(s).strip()
    ]
    invalidas = [s for s in situacoes if s not in SITUACOES]
    if invalidas:
        raise DashboardInputError(
            f"Situação inválida: {', '.join(invalidas)}. Use ATIVO, ARQUIVADO ou SUSPENSO/SOBRESTADO."
        )
    return ufs, comarcas, situacoes


async def _legado(
    ctx: DashboardContext, leg: Legado, ufs: list[str]
) -> dict[str, list[dict[str, Any]]] | None:
    """As respostas das rotas legadas da unidade: uma por UF escolhida (ou uma só, sem UF), como a v1."""
    fonte = ctx.extra_sources.get(leg.banco)
    if fonte is None:
        return None
    sub = replace(ctx, source=fonte, source_db=leg.banco)
    ini, fim = ctx.period.start, ctx.period.end
    alvos: list[str | None] = list(ufs) or [None]
    respostas: dict[str, list[dict[str, Any]]] = defaultdict(list)

    async def chamar(chave: str, alvo: tuple[ModuleType, str], de: Any, ate: Any) -> None:
        copia, nome = alvo
        for uf in alvos:
            filtros: dict[str, Any] = {}
            if uf is not None and nome in leg.uf:
                param = leg.uf[nome]
                filtros[param] = [uf] if param == "uf_protocolo" else uf
            respostas[chave].append(await _rota(sub, copia, nome, de, ate, **filtros))

    await chamar("comercial", leg.comercial, ini, fim)
    await chamar("comercial_historico", leg.comercial, None, None)
    await chamar("protocolo", leg.protocolo, ini, fim)
    await chamar("protocolo_historico", leg.protocolo, None, None)
    await chamar("org_doc", leg.org_doc, None, None)
    await chamar("pendencias", leg.pendencias, None, None)
    await chamar("peticionamento", leg.peticionamento, None, None)
    return respostas


def _soma(respostas: list[dict[str, Any]], campo: str) -> float:
    return sum(_num(_campo(r, campo)) for r in respostas)


def _series(respostas: list[dict[str, Any]], campo: str) -> list[Any]:
    return [_campo(r, campo) or [] for r in respostas]


def _filtrar_lexpre_por_ufs(rows: list[dict[str, Any]], ufs: list[str]) -> list[dict[str, Any]]:
    """= _filtrar_lexpre_por_ufs da v1: UF do cliente; sem UF = todas."""
    if not ufs:
        return rows
    alvo = {u.upper() for u in ufs}
    return [r for r in rows if str(r.get("UF") or "").strip().upper() in alvo]


async def resumo_lexpre(ctx: DashboardContext, ufs: list[str]) -> dict[str, Any] | None:
    """= _build_comercial_lexpre_resumo_estrategico_geral da v1 (sem a área de atuação), com o escritório da unidade
    no LexPre (app.unit_source_refs). None = unidade sem o LexPre ligado."""
    fonte = ctx.extra_sources.get("lexpre")
    ref = ctx.extra_refs.get("lexpre")
    if fonte is None or ref is None:
        return None
    escritorio_id = int(ref)
    de, ate = ctx.period.start, ctx.period.end

    rows = com_lexpre.filter_comercial_lexpre_por_escritorio(
        await fonte.fetch("comercial_lexpre_NG"), escritorio_id=escritorio_id
    )
    rows = _filtrar_lexpre_por_ufs(rows, ufs)
    mapa = com_lexpre.build_mapa_rubricas_reunidas(
        await fonte.fetch("demanda_rubrica_reunida_lexpre_NG")
    )

    log_setor = await fonte.fetch("log_setor_demanda_lexpre_NG")
    org_doc = _filtrar_lexpre_por_ufs(
        org_doc_lexpre.filter_org_doc_lexpre_por_escritorio(log_setor, escritorio_id=escritorio_id),
        ufs,
    )
    peticionamento = _filtrar_lexpre_por_ufs(
        peticionamento_lexpre.filter_peticionamento_lexpre_por_escritorio(
            log_setor, escritorio_id=escritorio_id
        ),
        ufs,
    )
    protocolo_setor = _filtrar_lexpre_por_ufs(
        protocolo_setor_lexpre.filter_protocolo_lexpre_por_escritorio(
            log_setor, escritorio_id=escritorio_id
        ),
        ufs,
    )
    pendencia = _filtrar_lexpre_por_ufs(
        pendencia_setor_lexpre.filter_pendencia_lexpre_por_escritorio(
            log_setor, escritorio_id=escritorio_id
        ),
        ufs,
    )
    visitas = pendencia_setor_lexpre._construir_visitas(
        pendencia, pendencia_setor_lexpre.SETOR_PENDENCIAS_IDS
    )
    represados = (
        org_doc_lexpre.get_represados(org_doc)
        + peticionamento_lexpre.get_represados(peticionamento)
        + protocolo_setor_lexpre.get_represados(protocolo_setor)
        + pendencia_setor_lexpre.get_pendencias_nao_resolvidas(visitas)
    )
    return {
        "contratos": com_lexpre.get_clientes_todos(rows, de, ate),
        "contratos_anterior": com_lexpre.get_clientes_todos_periodo_anterior(rows, de, ate),
        "acoes": com_lexpre.get_acoes_fechadas(rows, de, ate, mapa),
        "acoes_anterior": com_lexpre.get_acoes_fechadas_periodo_anterior(rows, de, ate, mapa),
        "contratos_por_mes": com_lexpre.group_clientes_todos_por_mes(rows),
        "acoes_por_mes": com_lexpre.group_acoes_fechadas_por_mes(rows, mapa),
        "contratos_por_dia": com_lexpre.group_clientes_todos_por_dia(rows),
        "acoes_por_dia": com_lexpre.group_acoes_fechadas_por_dia(rows, mapa),
        # Protocolados = demandas protocoladas, sem o mapa das rubricas reunidas (v1: inflava a contagem).
        "protocolados": prot_lexpre.get_protocolados(rows, de, ate),
        "protocolados_anterior": prot_lexpre.get_protocolados_periodo_anterior(rows, de, ate),
        "valor_causa": prot_lexpre.get_valor_causa_protocolado(rows, de, ate),
        "valor_causa_anterior": prot_lexpre.get_valor_causa_protocolado_periodo_anterior(
            rows, de, ate
        ),
        "represados": represados,
        "protocolados_por_mes": prot_lexpre.group_protocolados_por_mes(rows),
        "protocolados_por_dia": prot_lexpre.group_protocolados_por_dia(rows),
        "valor_causa_por_mes": prot_lexpre.group_valor_causa_protocolado_por_mes(rows),
        "valor_causa_por_dia": prot_lexpre.group_valor_causa_protocolado_por_dia(rows),
    }


def somar_comercial_protocolo(
    legado: dict[str, list[dict[str, Any]]] | None,
    campos: dict[str, str],
    lexpre: dict[str, Any] | None,
) -> dict[str, Any]:
    """As seções 01 e 02 da v1: legado + LexPre somados (contas da página da v1, Estrategico.tsx)."""
    leg = legado or defaultdict(list)
    lx = lexpre or {}

    def soma(chave_resposta: str, chave: str) -> float:
        return _soma(leg[chave_resposta], campos[chave]) + _num(lx.get(chave))

    def series(chave_resposta: str, chave: str, por: Any) -> list[dict[str, Any]]:
        return somar_series(
            [*_series(leg[chave_resposta], campos[chave]), lx.get(chave) or []], por
        )

    protocolados = soma("protocolo", "protocolados")
    valor_causa = soma("protocolo", "valor_causa")
    protocolados_ant = soma("protocolo", "protocolados_anterior")
    valor_causa_ant = soma("protocolo", "valor_causa_anterior")
    # Ticket médio: com uma resposta do legado e sem protocolados do LexPre, o campo pronto da rota (como a v1);
    # senão, valor de causa ÷ protocolados.
    if len(leg["protocolo"]) == 1 and not _num(lx.get("protocolados")):
        pronto = _campo(leg["protocolo"][0], campos["ticket_medio"])
        ticket = _num(pronto) if pronto is not None else None
    else:
        ticket = None
    if ticket is None:
        ticket = valor_causa / protocolados if protocolados > 0 else 0.0

    represados = (
        _soma(leg["org_doc"], campos["represados_org_doc"])
        + _soma(leg["pendencias"], campos["represados_pendencias"])
        + _soma(leg["protocolo_historico"], campos["represados_protocolo"])
        + _soma(leg["peticionamento"], campos["represados_peticionamento"])
        + _num(lx.get("represados"))
    )
    return {
        "comercial": {
            "contratos": soma("comercial", "contratos"),
            "contratos_anterior": soma("comercial", "contratos_anterior"),
            "acoes": soma("comercial", "acoes"),
            "acoes_anterior": soma("comercial", "acoes_anterior"),
            "contratos_por_mes": series("comercial_historico", "contratos_por_mes", chave_mes),
            "acoes_por_mes": series("comercial_historico", "acoes_por_mes", chave_mes),
            "contratos_por_dia": series("comercial_historico", "contratos_por_dia", chave_dia),
            "acoes_por_dia": series("comercial_historico", "acoes_por_dia", chave_dia),
        },
        "protocolo": {
            "represados": represados,
            "protocolados": protocolados,
            "protocolados_anterior": protocolados_ant,
            "valor_causa": round(valor_causa, 2),
            "valor_causa_anterior": round(valor_causa_ant, 2),
            "ticket_medio": round(ticket, 2),
            "ticket_medio_anterior": round(valor_causa_ant / protocolados_ant, 2)
            if protocolados_ant > 0
            else 0.0,
            "protocolados_por_mes": series(
                "protocolo_historico", "protocolados_por_mes", chave_mes
            ),
            "valor_causa_por_mes": series("protocolo_historico", "valor_causa_por_mes", chave_mes),
            "protocolados_por_dia": series(
                "protocolo_historico", "protocolados_por_dia", chave_dia
            ),
            "valor_causa_por_dia": series("protocolo_historico", "valor_causa_por_dia", chave_dia),
        },
    }


CAMPOS_JURIDICO = (
    "estrategico_geral_fase_inicial_total_processos",
    "estrategico_geral_fase_inicial_valor_causa_total",
    "estrategico_geral_fase_recursal_total_processos",
    "estrategico_geral_fase_recursal_valor_causa_total",
    "estrategico_geral_fase_recursal_valor_sentenca_total",
    "estrategico_geral_fase_execucao_total_processos",
    "estrategico_geral_fase_execucao_valor_causa_total",
    "estrategico_geral_fase_execucao_valor_execucao_total",
    "estrategico_geral_fase_inicial_por_subfase",
    "estrategico_geral_fase_recursal_por_subfase",
    "estrategico_geral_fase_execucao_por_subfase",
    "estrategico_geral_juridico_por_comarca",
)


def _sem_prefixo(nome: str) -> str:
    return nome.removeprefix("estrategico_geral_")


def _sem_nulos(valor: Any) -> Any:
    if isinstance(valor, list):
        return [_sem_nulos(v) for v in valor]
    if isinstance(valor, dict):
        return {k: v for k, v in valor.items() if v is not None}
    return valor


async def juridico(
    ctx: DashboardContext,
    escritorio: str,
    ufs: list[str],
    comarcas: list[str],
    situacoes: list[str],
    com_periodo: bool,
) -> dict[str, Any]:
    """/estrategico_geral da v1 com o escritório da unidade (seção 03 com o período; 04 sem)."""
    de, ate = (ctx.period.start, ctx.period.end) if com_periodo else (None, None)
    resposta = await _rota(
        ctx,
        v1_juridico,
        "estrategico_geral",
        de,
        ate,
        escritorio=[escritorio],
        comarca=comarcas or None,
        uf=ufs or None,
        situacao=situacoes or None,
    )
    return {_sem_prefixo(c): _sem_nulos(_campo(resposta, c)) for c in CAMPOS_JURIDICO}


async def build(ctx: DashboardContext) -> dict[str, Any]:
    r = ROTAS.get(ctx.unit_ref)
    if r is None:
        raise NotReady("Estratégico existe na NG, no LA e no RJ")
    ufs, comarcas, situacoes = filtros_da_pagina(ctx, r.tem_uf)
    legado = await _legado(ctx, r.legado, ufs)
    lexpre = await resumo_lexpre(ctx, ufs)
    corpo = somar_comercial_protocolo(legado, r.legado.campos, lexpre)
    fixo = await juridico(ctx, r.escritorio_juridico, ufs, comarcas, situacoes, False)
    return {
        "unidade": ctx.unit_ref,
        "tem_uf": r.tem_uf,
        "fontes": {"legado": legado is not None, "lexpre": lexpre is not None},
        **corpo,
        "juridico_periodo": await juridico(
            ctx, r.escritorio_juridico, ufs, comarcas, situacoes, True
        ),
        "juridico_fixo": fixo,
    }


def _queries(*rotas: tuple[ModuleType, str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(q for copia, nome in rotas for q in copia.QUERIES_POR_DASHBOARD[nome])
    )


MODULE = DashboardModule(
    key="estrategico",
    source_db="lexflow",
    source_label="LexFlow + Comercial e Protocolo (legado e LexPre)",
    build=build,
    filters={FILTRO_UF: str, FILTRO_COMARCA: str, FILTRO_SITUACAO: str},
    queries=tuple(v1_juridico.QUERIES_POR_DASHBOARD["estrategico_geral"]),
    extra_queries={
        "ng": _queries(
            *(
                getattr(ROTAS[u].legado, s)
                for u in ("NG", "RJ")
                for s in ("comercial", "protocolo", "org_doc", "pendencias", "peticionamento")
            )
        ),
        "laadv": _queries(
            *(
                getattr(ROTAS["LA"].legado, s)
                for s in ("comercial", "protocolo", "org_doc", "pendencias", "peticionamento")
            )
        ),
        "lexpre": QUERIES_LEXPRE,
    },
)
