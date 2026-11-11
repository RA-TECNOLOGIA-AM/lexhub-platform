"""Queries dos bancos de origem, copiadas da v1 (api_dashboards/src/app/queries.py) SEM mudar o texto.

Mesmo formato da v1: nome -> {"database": "lexpre" | "lexflow" | "ng" | "laadv", "query": "..."}.
O dev de dados cola aqui só as que os dashboards da V2 usam (ex.: "log_setor_demanda_lexpre_NG").
"""

QUERIES: dict[str, dict] = {
    # v1: queries.py, "log_setor_demanda_lexpre_NG" (copiada em 11/11/2026). Protocolo e Pendências (LexPre).
    "log_setor_demanda_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            l.id AS "LOG_ID",
            l.data AS "DATA",
            l.movimentacao_id AS "MOVIMENTACAO_ID",
            l.tipo AS "TIPO",
            l.demanda_id AS "ID_DEMANDA",
            l.setor_id AS "SETOR_ID",
            st.nome_setor AS "SETOR_NOME",
            l.escritorio_id AS "ESCRITORIO_ID",
            l.atendimento_id AS "ID_ACTION",
            f.nome AS "FUNCIONARIO",
            l.actor_id AS "ACTOR_ID",
            l.motivo AS "MOTIVO",
            l.origem AS "ORIGEM",
            d.rubrica_id AS "ID_RUBRICA",
            r.nome AS "MATERIA",
            r.reunida AS "RUBRICA_REUNIDA",
            r.operacao_id AS "OPERACAO_ID",
            op.nome AS "OPERACAO_NOME",
            aa.id AS "AREA_ATUACAO_ID",
            aa.description AS "AREA_ATUACAO_NOME",
            d.status AS "STATUS_DEMANDA_ID",
            sd.descricao AS "STATUS_DEMANDA",
            d.valor_causa AS "VALOR_CAUSA",
            d.dano_moral AS "DANO_MORAL",
            d.pet_auto AS "PET_AUTO",
            d.motivo_cancelamento_id AS "MOTIVO_CANCELAMENTO_ID",
            d.setor_id AS "SETOR_ATUAL_ID",
            st_atual.nome_setor AS "SETOR_ATUAL_NOME",
            d.numero_processo AS "NUMERO_PROCESSO",
            d.data_protocolo AS "DATA_PROTOCOLO",
            c.nome AS "CLIENTE_NOME",
            c.uf AS "UF"
        FROM public.log_setor_demanda l
        LEFT JOIN public.demandas d
            ON d.id = l.demanda_id
        LEFT JOIN public.rubricas r
            ON d.rubrica_id = r.id
        LEFT JOIN public.operacao op
            ON r.operacao_id = op.id
        LEFT JOIN public.area_atuacao aa
            ON op.area_atuacao_id = aa.id
        LEFT JOIN public.status sd
            ON d.status = sd.id
        LEFT JOIN public.setores st
            ON l.setor_id = st.id
        LEFT JOIN public.setores st_atual
            ON d.setor_id = st_atual.id
        LEFT JOIN public.setor_func sf
            ON l.responsavel_id = sf.id
        LEFT JOIN public.funcionario f
            ON sf.funcionario_id = f.id
        LEFT JOIN public.atendimento at
            ON at.id = d.atendimento_id
        LEFT JOIN public.customer c
            ON c.id = at.customer_id
        """,
        # Uma linha por evento de entrada/saída de demanda em setor (log_setor_demanda) —
        # cada movimentação de setor gera duas linhas (saída do setor antigo + entrada no
        # novo) com o mesmo movimentacao_id. Sem filtro de escritório/setor na query — é o
        # log CRU e COMPLETO (todos os setores), reaproveitado por qualquer dashboard de
        # setor baseado nesse fluxo (Organização de Documentos, Peticionamento, ...); cada
        # módulo de análise filtra o setor de interesse e aplica o recorte de escritório
        # (escritorio_id = 1 para NG) no backend. FUNCIONARIO é o responsável pelo setor no
        # momento do evento (log_setor_demanda.responsavel_id -> setor_func -> funcionario),
        # não quem disparou a movimentação. ACTOR_ID (log_setor_demanda.actor_id, FK direta
        # pra public.funcionario) é quem de fato executou o evento — usado em Pendências
        # (04/09/2026: só considerar um cancelamento como "cancelamento da Pendência" se
        # ACTOR_ID pertencer ao setor Pendências, via `setor_func_lexpre_NG` — ver
        # pendencia_setor_lexpre.build_funcionarios_do_setor/_is_cancelada). Confirmado por
        # amostragem: 100% das saídas do setor Pendências têm ACTOR_ID de alguém do próprio
        # setor, e 0% das entradas (entrada é sempre disparada por quem ENVIOU a demanda,
        # de outro setor) — por isso ACTOR_ID não pode ser usado sozinho sem esse cruzamento.
        # SETOR_ATUAL_NOME é o nome do setor onde a demanda está AGORA (demandas.setor_id,
        # valor vivo — não o setor do evento de log). CLIENTE_NOME e UF vêm de demandas ->
        # atendimento -> customer (nome e UF do cliente contratante) — UF adicionado em
        # 17/09/2026 para o filtro de UF nos dashboards por setor (LexPre), mesmo campo já
        # exposto por "comercial_lexpre_NG" (c.uf) para o dashboard Comercial.
        # AREA_ATUACAO_ID/NOME (17/09/2026): mesma correção de "comercial_lexpre_NG" — a
        # "área de atuação" de verdade é `public.operacao.area_atuacao_id` ->
        # `public.area_atuacao` (CONSUMIDOR/CIVIL/TRABALHISTA/PENAL/ADMINISTRATIVO/
        # AMBIENTAL/PREVIDENCIÁRIO), não `rubricas.operacao_id`/`public.operacao` (que no
        # lexpre é mais um código de escritório/operação). OPERACAO_ID/NOME continuam
        # expostos; o filtro/catálogo de área de atuação usa AREA_ATUACAO_ID/NOME.
        "description": "Log de entradas/saídas de demandas por setor (banco lexpre), base das páginas de dashboard por setor (LexPre).",
        "params": [],
    },
}
