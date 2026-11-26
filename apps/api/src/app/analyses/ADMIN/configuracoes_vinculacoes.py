"""Auditoria de configuração das vinculações (setor + atividade) do LexFlow.

Uma "vinculação" é uma linha de `setor_atividade`. A regra de negócio de cada
vinculação (campos obrigatórios, exigências de cumprido/não cumprido, próxima
atividade desencadeada, gatilhos de fase/subfase/situação) fica em
`configuracao_atividade` — o LexFlow só lê a configuração ATIVA.

A interpretação do fluxo de encerramento espelha o próprio LexFlow
(`resolve-fluxo-encerramento.ts` + `use-andamento-agendamento-modal.ts`), para que
o painel mostre o que de fato acontece ao encerrar um agendamento:

- CUMPRIDO e NÃO CUMPRIDO têm 3 opções exclusivas no modal "Configurar Atividade":
  "Apenas encerrar", "Encaminhar" e "Encaminhar com motivo".
  * Apenas encerrar  → `fluxo_encerramento_*_apenas_encerrar` (tem precedência).
  * Com motivo       → flag `fluxo_encerramento_*_encaminhamento_com_motivo` OU algum
                       item com `motivo` nos JSONs; destinos vêm de
                       `encaminhamentos_automaticos_*_json` (ou dos itens com motivo
                       de `encaminhamentos_*_json`).
  * Encaminhar       → CUMPRIDO: `fluxo_encerramento_cumprido_encaminhar_agendamento`;
                       NÃO CUMPRIDO: `fluxo_encerramento_nao_cumprido_controladoria`
                       (o nome da coluna é legado — no modal é a opção "Encaminhar").
                       Destinos em `encaminhamentos_*_json`, com fallback para a
                       coluna legada de destino único.
  O flag global `encaminhamento_automatico_ativo` NÃO é lido pelo LexFlow no
  encerramento — por isso é ignorado aqui.
- Gatilho de encerramento ("Trigger de Encerramento" no LexFlow, tickets 762/871):
  aplicado no CUMPRIDO e, desde o ticket 871, também no NÃO CUMPRIDO. Os slots de
  `triggers_conclusao_por_encaminhamento_json` têm `fluxo` (`cumprido` |
  `nao_cumprido`; slot legado sem o campo = cumprido) e mandam (um por
  destino+motivo). Se o fluxo do encerramento não tem nenhum slot ATIVO, o LexFlow
  chama a RPC sem override e ela aplica as colunas flat `trigger_conclusao_*` — ou
  seja, uma vinculação configurada antes do ticket 871 passa a mover o processo
  para a fase/subfase do cumprido também ao encerrar como NÃO CUMPRIDO.

A query busca todos os escritórios assinantes (necessário para resolver
encaminhamentos entre vinculações), mas a saída é restrita aos escritórios marcados
como ativos em `escritorio_assinante` — um escritório novo entra sozinho.

Campos de `configuracao_atividade` que esta auditoria ainda não interpreta (ex.:
uma coluna nova criada no LexFlow) são capturados automaticamente de
`configuracao_completa` e devolvidos em OUTRAS_CONFIGURACOES; os que nem o LexFlow
rotula ainda vêm com CONHECIDO=False, para o painel avisar que há campo novo.
"""
import json
from typing import Any, Dict, List, Optional, Tuple

# Colunas de configuracao_atividade que a auditoria já interpreta (fluxos, regras,
# gatilhos, campos obrigatórios) ou que são internas — não entram em "outras".
_CAMPOS_INTERPRETADOS = {
    "id", "id_setor_atividade", "id_subatividade", "ativo", "criado_em", "atualizado_em",
    "permite_pendencia", "disponivel_agendamento_manual", "prazo_padrao_qtd_dias", "prazo_padrao_dias_uteis",
    "regra_cumprido_exige_anexo", "regra_cumprido_exige_parecer", "regra_cumprido_sem_exigencia",
    "regra_nao_cumprido_exige_motivo", "regra_nao_cumprido_exige_anexo",
    "regra_nao_cumprido_exige_motivo_anexo", "regra_nao_cumprido_nenhuma_exigencia",
    "fluxo_encerramento_cumprido_apenas_encerrar", "fluxo_encerramento_cumprido_encaminhar_agendamento",
    "fluxo_encerramento_cumprido_encaminhamento_com_motivo",
    "fluxo_encerramento_cumprido_id_setor_atividade_encaminhamento", "qtd_dias_prazo_cumprido",
    "encaminhamentos_cumprido_json", "encaminhamentos_automaticos_cumprido_json",
    "fluxo_encerramento_nao_cumprido_apenas_encerrar", "fluxo_encerramento_nao_cumprido_controladoria",
    "fluxo_encerramento_nao_cumprido_encaminhamento_com_motivo",
    "fluxo_encerramento_nao_cumprido_id_setor_atividade", "qtd_dias_prazo_nao_cumprido",
    "encaminhamentos_nao_cumprido_json", "encaminhamentos_automaticos_nao_cumprido_json",
    "encaminhamento_automatico_ativo",  # não é lido pelo LexFlow no encerramento
    "trigger_criacao_ativo", "trigger_criacao_fase_id", "trigger_criacao_status_processual_id",
    "trigger_criacao_situacao_id",
    "trigger_conclusao_ativo", "trigger_conclusao_fase_id", "trigger_conclusao_status_processual_id",
    "triggers_conclusao_por_encaminhamento_json",
    "id_conf_campos_obrigatorios",
    "webhook_criacao_secret", "webhook_criacao_headers_json", "webhook_criacao_tem_secret",
}

# Rótulos do próprio LexFlow (setor-atividade-audit-labels.ts → CONFIGURACAO_LABELS).
# Coluna que não está aqui nem em _CAMPOS_INTERPRETADOS = campo novo do LexFlow.
_LABELS_CONFIGURACAO = {
    "herdar_prazo_fatal": "Herdar prazo fatal",
    "permitir_multiplos_motivos_encerramento_cumprido": "Múltiplos motivos (cumprido)",
    "permitir_multiplos_motivos_encerramento_nao_cumprido": "Múltiplos motivos (não cumprido)",
    "trigger_movimentacao_ativo": "Gatilho de movimentação ativo",
    "trigger_movimentacao_qualquer_evento": "Gatilho de movimentação — qualquer evento",
    "trigger_movimentacao_eventos": "Gatilho de movimentação — eventos filtrados",
    "trigger_movimentacao_fase_id": "Gatilho de movimentação — fase (id)",
    "trigger_movimentacao_status_processual_id": "Gatilho de movimentação — subfase (id)",
    "trigger_movimentacao_situacao_id": "Gatilho de movimentação — situação (id)",
    "webhook_criacao_ativo": "Webhook de criação ativo",
    "webhook_criacao_url": "Webhook — URL",
    "webhook_eventos": "Webhook — eventos",
    "escopos_obrigatoriedade": "Escopos cumprimento/não cumprimento",
}

# Campos que pertencem a um grupo com chave liga/desliga mas não compartilham o prefixo.
_DEPENDE_DE = {"webhook_eventos": "webhook_criacao_ativo"}

STATUS_OK = "ok"
STATUS_INCOMPLETA = "incompleta"
STATUS_ERRO = "erro"
STATUS_INATIVA = "inativa"

NIVEL_ERRO = "erro"
NIVEL_INCOMPLETA = "incompleta"

FLUXO_CUMPRIDO = "cumprido"
FLUXO_NAO_CUMPRIDO = "nao_cumprido"
_ROTULO_FLUXO = {FLUXO_CUMPRIDO: "CUMPRIDO", FLUXO_NAO_CUMPRIDO: "NÃO CUMPRIDO"}


def _parse_json_lista(raw: Any) -> List[Any]:
    """Decodifica colunas JSON de encaminhamentos/gatilhos.

    No banco os `encaminhamentos_*_json` (jsonb) estão gravados como *string* JSON
    (duplamente codificados: '"[{...}]"'), e o asyncpg devolve jsonb como texto —
    então pode ser preciso decodificar mais de uma vez, igual ao LexFlow
    (`parseMaybeJsonArray`, até 3 níveis).
    """
    value = raw
    for _ in range(3):
        if not isinstance(value, str):
            break
        texto = value.strip()
        if not texto:
            return []
        try:
            value = json.loads(texto)
        except (json.JSONDecodeError, TypeError):
            return []
    return value if isinstance(value, list) else []


def _int_or_none(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _motivo(item: Any) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    motivo = item.get("motivo")
    if motivo is None:
        return None
    motivo = str(motivo).strip()
    return motivo or None


def _avaliar_destino(
    catalogo: Dict[int, Dict[str, Any]],
    id_destino: Optional[int],
    id_escritorio_origem: Optional[int],
) -> Tuple[str, str]:
    """Retorna (situação do destino, rótulo legível)."""
    info = catalogo.get(id_destino) if id_destino is not None else None
    if not info:
        return "inexistente", f"Vinculação #{id_destino} (não existe mais)"
    rotulo = f"{info['setor']} · {info['atividade']}"
    if id_escritorio_origem is not None and info["id_escritorio"] != id_escritorio_origem:
        return "outro_escritorio", f"{rotulo} (de outro escritório)"
    if not info["ativa"]:
        return "inativa", f"{rotulo} (INATIVA)"
    return "ok", rotulo


def _montar_destino(
    item: Dict[str, Any],
    catalogo: Dict[int, Dict[str, Any]],
    id_escritorio_origem: Optional[int],
    qtd_dias_padrao: Optional[int] = None,
) -> Dict[str, Any]:
    id_destino = _int_or_none(item.get("id_setor_atividade"))
    motivo = _motivo(item)
    qtd_dias = _int_or_none(item.get("qtd_dias"))
    if qtd_dias is None:
        qtd_dias = qtd_dias_padrao
    if id_destino is None:
        # Motivo sem destino = esse motivo apenas encerra (válido no fluxo com motivo).
        situacao, rotulo = "sem_destino", "Apenas encerra"
    else:
        situacao, rotulo = _avaliar_destino(catalogo, id_destino, id_escritorio_origem)
    texto = rotulo
    if motivo:
        texto = f"{motivo} → {rotulo}"
    if id_destino is not None and qtd_dias:
        texto = f"{texto} ({qtd_dias}d)"
    return {
        "ID_VINCULACAO": id_destino,
        "MOTIVO": motivo,
        "QTD_DIAS": qtd_dias,
        "SITUACAO": situacao,
        "TEXTO": texto,
    }


_MODO_LABEL = {
    "encerra": "Apenas encerrar",
    "encaminha": "Encaminhar",
    "encaminha_com_motivo": "Encaminhar com motivo",
    "nao_configurado": "Não configurado",
    "sem_configuracao": "Sem configuração",
}


def _resolver_fluxo(
    *,
    apenas_encerrar: Optional[bool],
    flag_encaminhar: Optional[bool],
    flag_com_motivo: Optional[bool],
    encaminhamentos_json: Any,
    automaticos_json: Any,
    id_destino_legado: Optional[int],
    qtd_dias_legado: Optional[int],
    catalogo: Dict[int, Dict[str, Any]],
    id_escritorio: Optional[int],
) -> Dict[str, Any]:
    """Resolve o fluxo de encerramento (CUMPRIDO ou NÃO CUMPRIDO) como o LexFlow faz."""
    enc = [e for e in _parse_json_lista(encaminhamentos_json) if isinstance(e, dict)]
    autos = [e for e in _parse_json_lista(automaticos_json) if isinstance(e, dict)]

    com_motivo = bool(
        not apenas_encerrar
        and (flag_com_motivo or any(_motivo(e) for e in autos) or any(_motivo(e) for e in enc))
    )

    destinos: List[Dict[str, Any]] = []
    if apenas_encerrar:
        modo = "encerra"
    elif com_motivo:
        modo = "encaminha_com_motivo"
        itens = autos if autos else [e for e in enc if _motivo(e)]
        destinos = [_montar_destino(e, catalogo, id_escritorio) for e in itens]
    elif flag_encaminhar or enc:
        modo = "encaminha"
        itens = [e for e in enc if _int_or_none(e.get("id_setor_atividade")) is not None]
        if not itens and id_destino_legado is not None:
            itens = [{"id_setor_atividade": id_destino_legado, "qtd_dias": qtd_dias_legado}]
        destinos = [_montar_destino(e, catalogo, id_escritorio, qtd_dias_padrao=1) for e in itens]
    else:
        modo = "nao_configurado"

    return {
        "MODO": modo,
        "MODO_LABEL": _MODO_LABEL[modo],
        "DESTINOS": destinos,
    }


def _resumo_fluxo(fluxo: Dict[str, Any]) -> str:
    if fluxo["MODO"] in ("encerra", "nao_configurado", "sem_configuracao"):
        return fluxo["MODO_LABEL"]
    textos = [d["TEXTO"] for d in fluxo["DESTINOS"]]
    return f"{fluxo['MODO_LABEL']}: {'; '.join(textos)}" if textos else f"{fluxo['MODO_LABEL']}: (sem destino)"


def _campos_obrigatorios_ativos(campos_obrigatorios_raw: Any) -> List[str]:
    return sorted(str(item) for item in _parse_json_lista(campos_obrigatorios_raw))


def _montar_gatilhos_conclusao(
    row: Dict[str, Any],
    catalogo: Dict[int, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    slots = []
    for slot in _parse_json_lista(row.get("triggers_conclusao_slots")):
        if not isinstance(slot, dict):
            continue
        id_destino = _int_or_none(slot.get("id_setor_atividade"))
        motivo = _motivo(slot)
        if slot.get("kind") == "apenas_encerrar":
            opcao = "Apenas encerrar"
        elif id_destino is not None:
            _, opcao = _avaliar_destino(catalogo, id_destino, row.get("id_escritorio_assinante"))
        else:
            opcao = "Encaminhamento"
        if motivo:
            opcao = f"{motivo} → {opcao}"
        slots.append(
            {
                "OPCAO": opcao,
                "FLUXO": FLUXO_NAO_CUMPRIDO if slot.get("fluxo") == FLUXO_NAO_CUMPRIDO else FLUXO_CUMPRIDO,
                "TIPO": slot.get("kind") or "encaminhamento",
                "ID_VINCULACAO": id_destino,
                "MOTIVO": motivo,
                "ATIVO": bool(slot.get("ativo")),
                "FASE": slot.get("fase"),
                "SUBFASE": slot.get("subfase"),
                "_fase_id": _int_or_none(slot.get("fase_id")),
                "_fase_id_raw": _int_or_none(slot.get("fase_id_raw")),
                "_status_id": _int_or_none(slot.get("status_processual_id")),
                "_status_id_raw": _int_or_none(slot.get("status_processual_id_raw")),
                "_subfase_fase_id": _int_or_none(slot.get("subfase_fase_id")),
            }
        )
    return slots


def _flat_altera_processo(row: Dict[str, Any]) -> bool:
    """Colunas flat do gatilho de encerramento ligadas e apontando para fase/subfase."""
    return bool(row.get("trigger_conclusao_ativo")) and (
        row.get("trigger_conclusao_fase_id") is not None
        or row.get("trigger_conclusao_status_processual_id") is not None
    )


def _resumo_gatilho_encerramento(
    row: Dict[str, Any],
    gatilhos_conclusao: List[Dict[str, Any]],
    fluxo: str,
) -> Dict[str, Any]:
    """O que o LexFlow faz com a ficha do processo ao encerrar por esse fluxo.

    ORIGEM: "slots" (opções da aba Trigger de Encerramento), "flat" (fallback das
    colunas trigger_conclusao_* — sem slot ativo no fluxo) ou "nenhum".
    """
    ativos = [s for s in gatilhos_conclusao if s["FLUXO"] == fluxo and s["ATIVO"]]
    if ativos:
        combinacoes = {(s["FASE"], s["SUBFASE"]) for s in ativos}
        fase, subfase = next(iter(combinacoes)) if len(combinacoes) == 1 else (None, None)
        return {"ORIGEM": "slots", "ATIVO": True, "FASE": fase, "SUBFASE": subfase, "QTD_SLOTS_ATIVOS": len(ativos)}
    if _flat_altera_processo(row):
        return {
            "ORIGEM": "flat",
            "ATIVO": True,
            "FASE": row.get("fase_conclusao"),
            "SUBFASE": row.get("subfase_conclusao"),
            "QTD_SLOTS_ATIVOS": 0,
        }
    return {
        "ORIGEM": "nenhum",
        "ATIVO": bool(row.get("trigger_conclusao_ativo")),
        "FASE": row.get("fase_conclusao"),
        "SUBFASE": row.get("subfase_conclusao"),
        "QTD_SLOTS_ATIVOS": 0,
    }


def _detectar_problemas(
    row: Dict[str, Any],
    fluxo_cumprido: Dict[str, Any],
    fluxo_nao_cumprido: Dict[str, Any],
    gatilhos_conclusao: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Lista de problemas de uma vinculação ATIVA.

    - erro: a configuração aponta para algo errado (destino inexistente/inativo/de
      outro escritório, subfase de outra fase, fase/subfase apagada).
    - incompleta: falta preencher algo que o LexFlow precisa para agir.
    """
    problemas: List[Dict[str, str]] = []

    def add(nivel: str, mensagem: str, tipo: Optional[str] = None) -> None:
        # TIPO é estável (sem o trecho variável) para agrupar no painel.
        problemas.append({"NIVEL": nivel, "TIPO": tipo or mensagem, "MENSAGEM": mensagem})

    if row.get("id_configuracao") is None:
        add(NIVEL_INCOMPLETA, "Vinculação sem configuração de atividade cadastrada")
        return problemas
    if row.get("configuracao_ativa") is False:
        add(NIVEL_INCOMPLETA, "Só existe configuração INATIVA — o LexFlow trata como sem configuração")
        return problemas

    if row.get("id_conf_campos_obrigatorios") is None:
        add(NIVEL_INCOMPLETA, "Nenhum conjunto de campos obrigatórios vinculado")

    if not any(
        row.get(c) for c in ("regra_cumprido_exige_anexo", "regra_cumprido_exige_parecer", "regra_cumprido_sem_exigencia")
    ):
        add(NIVEL_INCOMPLETA, "Regra de CUMPRIDO não definida (anexo/parecer/sem exigência)")
    if not any(
        row.get(c)
        for c in (
            "regra_nao_cumprido_exige_motivo",
            "regra_nao_cumprido_exige_anexo",
            "regra_nao_cumprido_exige_motivo_anexo",
            "regra_nao_cumprido_nenhuma_exigencia",
        )
    ):
        add(NIVEL_INCOMPLETA, "Regra de NÃO CUMPRIDO não definida (motivo/anexo/sem exigência)")

    for rotulo, fluxo in (("CUMPRIDO", fluxo_cumprido), ("NÃO CUMPRIDO", fluxo_nao_cumprido)):
        modo = fluxo["MODO"]
        if modo == "nao_configurado":
            add(NIVEL_INCOMPLETA, f"Fluxo de {rotulo} não definido (apenas encerrar / encaminhar / com motivo)", f"Fluxo de {rotulo} não definido")
            continue
        if modo == "encaminha" and not fluxo["DESTINOS"]:
            add(NIVEL_INCOMPLETA, f"{rotulo}: opção \"Encaminhar\" marcada, mas sem vinculação de destino", "\"Encaminhar\" marcado sem destino")
        if modo == "encaminha_com_motivo" and not fluxo["DESTINOS"]:
            add(NIVEL_INCOMPLETA, f"{rotulo}: opção \"Encaminhar com motivo\" marcada, mas sem nenhum motivo cadastrado", "\"Com motivo\" marcado sem motivos")
        for destino in fluxo["DESTINOS"]:
            situacao = destino["SITUACAO"]
            if situacao == "inexistente":
                add(NIVEL_ERRO, f"{rotulo} encaminha para vinculação que não existe mais (#{destino['ID_VINCULACAO']})", "Encaminha para vinculação inexistente")
            elif situacao == "inativa":
                add(NIVEL_ERRO, f"{rotulo} encaminha para vinculação INATIVA: {destino['TEXTO']}", "Encaminha para vinculação inativa")
            elif situacao == "outro_escritorio":
                add(NIVEL_ERRO, f"{rotulo} encaminha para vinculação de OUTRO escritório: {destino['TEXTO']}", "Encaminha para vinculação de outro escritório")

    # Gatilho de criação (agendamento): fase, subfase e/ou situação.
    if row.get("trigger_criacao_ativo"):
        if (
            row.get("trigger_criacao_fase_id") is None
            and row.get("trigger_criacao_status_processual_id") is None
            and row.get("trigger_criacao_situacao_id") is None
        ):
            add(NIVEL_INCOMPLETA, "Gatilho de agendamento ativo, mas sem fase/subfase/situação definida")
    if row.get("trigger_criacao_fase_id") is not None and row.get("fase_agendamento") is None:
        add(NIVEL_ERRO, "Fase do agendamento aponta para fase que não existe mais")
    if row.get("trigger_criacao_status_processual_id") is not None and row.get("subfase_agendamento") is None:
        add(NIVEL_ERRO, "Subfase do agendamento aponta para subfase que não existe mais")
    if (
        row.get("trigger_criacao_fase_id") is not None
        and row.get("subfase_agendamento_fase_id") is not None
        and row["subfase_agendamento_fase_id"] != row["trigger_criacao_fase_id"]
    ):
        add(NIVEL_ERRO, "Subfase do agendamento não pertence à fase de agendamento configurada")

    # Gatilho de encerramento: slots por fluxo+encaminhamento mandam; flat é fallback.
    destinos_por_fluxo = {
        FLUXO_CUMPRIDO: (fluxo_cumprido, {(d["ID_VINCULACAO"], (d["MOTIVO"] or "").lower()) for d in fluxo_cumprido["DESTINOS"]}),
        FLUXO_NAO_CUMPRIDO: (fluxo_nao_cumprido, {(d["ID_VINCULACAO"], (d["MOTIVO"] or "").lower()) for d in fluxo_nao_cumprido["DESTINOS"]}),
    }
    for slot in gatilhos_conclusao:
        if not slot["ATIVO"]:
            continue
        rotulo = _ROTULO_FLUXO[slot["FLUXO"]]
        opcao = f"{rotulo}: {slot['OPCAO']}"
        if slot["_fase_id"] is None and slot["_status_id"] is None:
            add(NIVEL_INCOMPLETA, f"Gatilho de encerramento ativo sem fase/subfase (opção {opcao})", "Gatilho de conclusão ativo sem fase/subfase")
        if slot["_fase_id_raw"] is not None and slot["_fase_id"] is None:
            add(NIVEL_ERRO, f"Gatilho de encerramento aponta para fase que não existe mais (opção {opcao})", "Fase da conclusão aponta para fase que não existe mais")
        if slot["_status_id_raw"] is not None and slot["_status_id"] is None:
            add(NIVEL_ERRO, f"Gatilho de encerramento aponta para subfase que não existe mais (opção {opcao})", "Subfase da conclusão aponta para subfase que não existe mais")
        if (
            slot["_fase_id"] is not None
            and slot["_subfase_fase_id"] is not None
            and slot["_subfase_fase_id"] != slot["_fase_id"]
        ):
            add(NIVEL_ERRO, f"Subfase do encerramento não pertence à fase configurada (opção {opcao})", "Subfase da conclusão não pertence à fase de conclusão configurada")
        fluxo_slot, destinos_slot = destinos_por_fluxo[slot["FLUXO"]]
        if (
            slot["TIPO"] == "encaminhamento"
            and fluxo_slot["MODO"] in ("encaminha", "encaminha_com_motivo")
            and (slot["ID_VINCULACAO"], (slot["MOTIVO"] or "").lower()) not in destinos_slot
        ):
            add(
                NIVEL_INCOMPLETA,
                f"Gatilho de encerramento configurado para um encaminhamento que não existe mais no fluxo de {rotulo} ({slot['OPCAO']})",
                "Gatilho de conclusão órfão (encaminhamento removido)",
            )

    # Algum fluxo sem slot ativo cai nas colunas flat — valida o flat nesse caso.
    usa_flat = any(
        not any(s["ATIVO"] for s in gatilhos_conclusao if s["FLUXO"] == f)
        for f in (FLUXO_CUMPRIDO, FLUXO_NAO_CUMPRIDO)
    )
    if usa_flat:
        if not gatilhos_conclusao and row.get("trigger_conclusao_ativo") and (
            row.get("trigger_conclusao_fase_id") is None and row.get("trigger_conclusao_status_processual_id") is None
        ):
            add(NIVEL_INCOMPLETA, "Gatilho de conclusão ativo, mas sem fase/subfase definida", "Gatilho de conclusão ativo sem fase/subfase")
        if row.get("trigger_conclusao_fase_id") is not None and row.get("fase_conclusao") is None:
            add(NIVEL_ERRO, "Fase da conclusão aponta para fase que não existe mais")
        if row.get("trigger_conclusao_status_processual_id") is not None and row.get("subfase_conclusao") is None:
            add(NIVEL_ERRO, "Subfase da conclusão aponta para subfase que não existe mais")
        if (
            row.get("trigger_conclusao_fase_id") is not None
            and row.get("subfase_conclusao_fase_id") is not None
            and row["subfase_conclusao_fase_id"] != row["trigger_conclusao_fase_id"]
        ):
            add(NIVEL_ERRO, "Subfase da conclusão não pertence à fase de conclusão configurada")

    # Ticket 871: NÃO CUMPRIDO sem opção ativa própria herda o gatilho flat (que
    # espelha o CUMPRIDO) — o processo vai para a fase/subfase do cumprido.
    tem_slot_nc_ativo = any(s["ATIVO"] for s in gatilhos_conclusao if s["FLUXO"] == FLUXO_NAO_CUMPRIDO)
    if not tem_slot_nc_ativo and _flat_altera_processo(row):
        alvo = " / ".join(x for x in (row.get("fase_conclusao"), row.get("subfase_conclusao")) if x) or "fase/subfase do gatilho"
        add(
            NIVEL_ERRO,
            "Ao encerrar como NÃO CUMPRIDO o processo vai para a fase/subfase do gatilho de encerramento "
            f"({alvo}) — não há opção ativa de Não Cumprido na aba Trigger de Encerramento",
            "Não cumprido herda o gatilho de encerramento do cumprido",
        )

    return problemas


def _valor_preenchido(valor: Any) -> bool:
    if valor is None or valor is False:
        return False
    if isinstance(valor, str) and not valor.strip():
        return False
    if isinstance(valor, (list, dict)) and not valor:
        return False
    return True


def _formatar_valor(valor: Any) -> str:
    if valor is True:
        return "Sim"
    if isinstance(valor, list):
        return ", ".join(_formatar_valor(v) for v in valor)
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)


def _outras_configuracoes(configuracao_completa: Any) -> List[Dict[str, Any]]:
    """Campos preenchidos da configuração que a auditoria não interpreta."""
    config = configuracao_completa
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(config, dict):
        return []
    # Grupos desligados: `<prefixo>_ativo = false` esconde os demais `<prefixo>_*`
    # (ex.: trigger_movimentacao_*, webhook_criacao_*) — vale para grupos novos também.
    prefixos_desligados = [
        campo[: -len("ativo")] for campo, valor in config.items() if campo.endswith("_ativo") and not valor
    ]

    def _grupo_desligado(campo: str) -> bool:
        if campo in _DEPENDE_DE:
            return not config.get(_DEPENDE_DE[campo])
        return any(campo.startswith(p) and campo != f"{p}ativo" for p in prefixos_desligados)

    outras = []
    for campo in sorted(config):
        if campo in _CAMPOS_INTERPRETADOS or _grupo_desligado(campo):
            continue
        valor = config[campo]
        if isinstance(valor, str) and valor.strip()[:1] in ("[", "{", '"'):
            # jsonb gravado como string — mostra o conteúdo, não o texto escapado
            parsed = _parse_json_lista(valor)
            if parsed or valor.strip() in ("[]", '"[]"'):
                valor = parsed
        if not _valor_preenchido(valor):
            continue
        conhecido = campo in _LABELS_CONFIGURACAO
        outras.append(
            {
                "CAMPO": campo,
                "LABEL": _LABELS_CONFIGURACAO.get(campo) or campo.replace("_", " ").capitalize(),
                "VALOR": _formatar_valor(valor),
                "CONHECIDO": conhecido,
            }
        )
    return outras


def _status(vinculacao_ativa: bool, problemas: List[Dict[str, str]]) -> str:
    if not vinculacao_ativa:
        return STATUS_INATIVA
    if any(p["NIVEL"] == NIVEL_ERRO for p in problemas):
        return STATUS_ERRO
    if problemas:
        return STATUS_INCOMPLETA
    return STATUS_OK


_ORDEM_STATUS = {STATUS_ERRO: 0, STATUS_INCOMPLETA: 1, STATUS_OK: 2, STATUS_INATIVA: 3}


def montar_configuracoes_vinculacoes(rows_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Recebe as linhas cruas da query `configuracoes_vinculacoes` e monta o relatório.

    Uma linha de entrada = uma vinculação (setor_atividade), já com o LEFT JOIN da
    configuração ativa (quando existir) e dos catálogos de fase/subfase/situação.
    """
    rows = [dict(r) for r in rows_raw]

    catalogo: Dict[int, Dict[str, Any]] = {
        int(r["id_vinculacao"]): {
            "setor": r.get("setor"),
            "atividade": r.get("atividade"),
            "ativa": bool(r.get("vinculacao_ativa")),
            "id_escritorio": r.get("id_escritorio_assinante"),
        }
        for r in rows
    }

    resultado: List[Dict[str, Any]] = []
    for row in rows:
        id_escritorio = row.get("id_escritorio_assinante")
        if id_escritorio is None or not row.get("escritorio_ativo"):
            continue

        vinculacao_ativa = bool(row.get("vinculacao_ativa"))
        tem_configuracao = row.get("id_configuracao") is not None
        campos_obrigatorios = _campos_obrigatorios_ativos(row.get("campos_obrigatorios"))

        if tem_configuracao and row.get("configuracao_ativa") is not False:
            fluxo_cumprido = _resolver_fluxo(
                apenas_encerrar=row.get("fluxo_encerramento_cumprido_apenas_encerrar"),
                flag_encaminhar=row.get("fluxo_encerramento_cumprido_encaminhar_agendamento"),
                flag_com_motivo=row.get("fluxo_encerramento_cumprido_encaminhamento_com_motivo"),
                encaminhamentos_json=row.get("encaminhamentos_cumprido_json"),
                automaticos_json=row.get("encaminhamentos_automaticos_cumprido_json"),
                id_destino_legado=_int_or_none(row.get("fluxo_encerramento_cumprido_id_setor_atividade_encaminhamento")),
                qtd_dias_legado=row.get("qtd_dias_prazo_cumprido"),
                catalogo=catalogo,
                id_escritorio=id_escritorio,
            )
            fluxo_nao_cumprido = _resolver_fluxo(
                apenas_encerrar=row.get("fluxo_encerramento_nao_cumprido_apenas_encerrar"),
                flag_encaminhar=row.get("fluxo_encerramento_nao_cumprido_controladoria"),
                flag_com_motivo=row.get("fluxo_encerramento_nao_cumprido_encaminhamento_com_motivo"),
                encaminhamentos_json=row.get("encaminhamentos_nao_cumprido_json"),
                automaticos_json=row.get("encaminhamentos_automaticos_nao_cumprido_json"),
                id_destino_legado=_int_or_none(row.get("fluxo_encerramento_nao_cumprido_id_setor_atividade")),
                qtd_dias_legado=row.get("qtd_dias_prazo_nao_cumprido"),
                catalogo=catalogo,
                id_escritorio=id_escritorio,
            )
        else:
            fluxo_cumprido = {"MODO": "sem_configuracao", "MODO_LABEL": _MODO_LABEL["sem_configuracao"], "DESTINOS": []}
            fluxo_nao_cumprido = dict(fluxo_cumprido)

        gatilhos_conclusao = _montar_gatilhos_conclusao(row, catalogo)
        problemas = (
            _detectar_problemas(row, fluxo_cumprido, fluxo_nao_cumprido, gatilhos_conclusao)
            if vinculacao_ativa
            else []
        )

        # Fase/subfase do encerramento por fluxo: com slots, mostra a combinação comum
        # aos slots ativos (ou nada, quando varia por encaminhamento — o detalhe lista todos).
        gatilho_cumprido = _resumo_gatilho_encerramento(row, gatilhos_conclusao, FLUXO_CUMPRIDO)
        gatilho_nao_cumprido = _resumo_gatilho_encerramento(row, gatilhos_conclusao, FLUXO_NAO_CUMPRIDO)

        resultado.append(
            {
                "ID_VINCULACAO": row["id_vinculacao"],
                "ID_ESCRITORIO_ASSINANTE": id_escritorio,
                "ESCRITORIO": row.get("escritorio") or row.get("escritorio_razao_social"),
                "ESCRITORIO_ATIVO": row.get("escritorio_ativo"),
                "VINCULACAO_ATIVA": vinculacao_ativa,
                "SETOR": row.get("setor"),
                "ATIVIDADE": row.get("atividade"),
                "VINCULACAO": f"{row.get('setor')} · {row.get('atividade')}",
                "STATUS": _status(vinculacao_ativa, problemas),
                "TEM_CONFIGURACAO": tem_configuracao,
                "CONFIGURACAO_ATIVA": bool(row.get("configuracao_ativa")) if tem_configuracao else None,
                "FASE_AGENDAMENTO": row.get("fase_agendamento"),
                "SUBFASE_AGENDAMENTO": row.get("subfase_agendamento"),
                "SITUACAO_AGENDAMENTO": row.get("situacao_agendamento"),
                "GATILHO_AGENDAMENTO_ATIVO": row.get("trigger_criacao_ativo"),
                "FASE_CONCLUSAO": gatilho_cumprido["FASE"],
                "SUBFASE_CONCLUSAO": gatilho_cumprido["SUBFASE"],
                "GATILHO_CONCLUSAO_ATIVO": gatilho_cumprido["ATIVO"],
                "GATILHO_ENCERRAMENTO_CUMPRIDO": gatilho_cumprido,
                "GATILHO_ENCERRAMENTO_NAO_CUMPRIDO": gatilho_nao_cumprido,
                "GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO": [
                    {k: v for k, v in s.items() if not k.startswith("_")} for s in gatilhos_conclusao
                ],
                "CAMPOS_OBRIGATORIOS": campos_obrigatorios,
                "QTD_CAMPOS_OBRIGATORIOS": len(campos_obrigatorios),
                "REGRA_CUMPRIDO_EXIGE_ANEXO": row.get("regra_cumprido_exige_anexo"),
                "REGRA_CUMPRIDO_EXIGE_PARECER": row.get("regra_cumprido_exige_parecer"),
                "REGRA_CUMPRIDO_SEM_EXIGENCIA": row.get("regra_cumprido_sem_exigencia"),
                "REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO": row.get("regra_nao_cumprido_exige_motivo"),
                "REGRA_NAO_CUMPRIDO_EXIGE_ANEXO": row.get("regra_nao_cumprido_exige_anexo"),
                "REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO_ANEXO": row.get("regra_nao_cumprido_exige_motivo_anexo"),
                "REGRA_NAO_CUMPRIDO_NENHUMA_EXIGENCIA": row.get("regra_nao_cumprido_nenhuma_exigencia"),
                "PERMITE_PENDENCIA": row.get("permite_pendencia"),
                "PRAZO_PADRAO_QTD_DIAS": row.get("prazo_padrao_qtd_dias"),
                "PRAZO_PADRAO_DIAS_UTEIS": row.get("prazo_padrao_dias_uteis"),
                "DISPONIVEL_AGENDAMENTO_MANUAL": row.get("disponivel_agendamento_manual"),
                "FLUXO_CUMPRIDO": fluxo_cumprido,
                "FLUXO_NAO_CUMPRIDO": fluxo_nao_cumprido,
                "PROXIMA_ATIVIDADE_CUMPRIDO": _resumo_fluxo(fluxo_cumprido),
                "PROXIMA_ATIVIDADE_NAO_CUMPRIDO": _resumo_fluxo(fluxo_nao_cumprido),
                "QTD_PROBLEMAS": len(problemas),
                "QTD_ERROS": sum(1 for p in problemas if p["NIVEL"] == NIVEL_ERRO),
                "PROBLEMAS": [p["MENSAGEM"] for p in problemas],
                "PROBLEMAS_DETALHE": problemas,
                "OUTRAS_CONFIGURACOES": _outras_configuracoes(row.get("configuracao_completa")),
                "CONFIGURACAO_CRIADO_EM": row.get("configuracao_criado_em"),
                "CONFIGURACAO_ATUALIZADO_EM": row.get("configuracao_atualizado_em"),
            }
        )

    resultado.sort(
        key=lambda r: (
            _ORDEM_STATUS[r["STATUS"]],
            -r["QTD_PROBLEMAS"],
            r["ID_ESCRITORIO_ASSINANTE"] or 0,
            r["SETOR"] or "",
            r["ATIVIDADE"] or "",
        )
    )
    return resultado
