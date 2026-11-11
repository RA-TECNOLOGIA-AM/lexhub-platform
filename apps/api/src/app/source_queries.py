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
    # v1: queries.py:791, "setor_func_lexpre_NG" (copiada em 11/11/2026). Pendências (LexPre).
    "setor_func_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            sf.id AS "SETOR_FUNC_ID",
            sf.funcionario_id AS "FUNCIONARIO_ID",
            sf.setor_id AS "SETOR_ID"
        FROM public.setor_func sf
        """,
        # Vínculos funcionário-setor (banco lexpre) — quem está formalmente alocado em qual
        # setor agora. Usado em Pendências (04/09/2026) para validar se quem executou um
        # cancelamento (log_setor_demanda.actor_id) realmente pertence ao setor Pendências —
        # ver comentário em "log_setor_demanda_lexpre_NG" e
        # pendencia_setor_lexpre.build_funcionarios_do_setor.
        "description": "Vínculos funcionário-setor (banco lexpre) — quem está alocado em qual setor.",
        "params": []
    },
    # v1: queries.py:613, "comercial_lexpre_NG" (copiada em 11/11/2026). Comercial e Comissão Comercial (LexPre).
    "comercial_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            a.id AS "ID_ACTION",
            c.nome AS "CLIENTE",
            c.uf AS "UF",
            f.nome AS "ATENDENTE",
            a.status_id AS "STATUS_ID",
            s.descricao AS "STATUS",
            a.escritorio_id AS "ESCRITORIO_ID",
            e.nome AS "ESCRITORIO",
            a.motivo_id AS "MOTIVO_ID",
            me.descricao AS "MOTIVO_ENCERRAMENTO",
            a.data_assinatura AS "DATA_ASSINATURA",
            a.data_entrada AS "DATA_ENTRADA",
            a.canal_aquisicao AS "CANAL_AQUISICAO",
            a.tipo_trafego AS "TIPO_TRAFEGO",
            a.prospeccao AS "PROSPECCAO",
            a.nome_campanha AS "NOME_CAMPANHA",
            a.nome_conjunto AS "NOME_CONJUNTO",
            a.criativo AS "CRIATIVO",
            a.posicionamento AS "POSICIONAMENTO",
            a.ad_id AS "AD_ID",
            d.id AS "ID_DEMANDA",
            d.rubrica_id AS "ID_RUBRICA",
            r.nome AS "RUBRICA",
            r.reunida AS "RUBRICA_REUNIDA",
            r.operacao_id AS "OPERACAO_ID",
            op.nome AS "OPERACAO_NOME",
            aa.id AS "AREA_ATUACAO_ID",
            aa.description AS "AREA_ATUACAO_NOME",
            r.valor_rubrica AS "VALOR_AM",
            d.status AS "STATUS_DEMANDA_ID",
            sd.descricao AS "STATUS_DEMANDA",
            d.valor_causa AS "VALOR_CAUSA",
            d.dano_moral AS "DANO_MORAL",
            d.numero_processo AS "NUMERO_PROCESSO",
            d.data_protocolo AS "DATA_PROTOCOLO",
            d.setor_id AS "SETOR_ID",
            st.nome_setor AS "SETOR_NOME"
        FROM public.atendimento a
        LEFT JOIN public.customer c
            ON a.customer_id = c.id
        LEFT JOIN public.funcionario f
            ON a.funcionario_id = f.id
        LEFT JOIN public.status s
            ON a.status_id = s.id
        LEFT JOIN public.escritorio e
            ON a.escritorio_id = e.id
        LEFT JOIN public.motivo_encerramento me
            ON a.motivo_id = me.id
        LEFT JOIN public.demandas d
            ON d.atendimento_id = a.id
        LEFT JOIN public.rubricas r
            ON d.rubrica_id = r.id
        LEFT JOIN public.operacao op
            ON r.operacao_id = op.id
        LEFT JOIN public.area_atuacao aa
            ON op.area_atuacao_id = aa.id
        LEFT JOIN public.status sd
            ON d.status = sd.id
        LEFT JOIN public.setores st
            ON d.setor_id = st.id
        """,
        # Sem filtro de escritório na query — traz todos os escritórios (NGAM/LAAM/LARJ).
        # O recorte NG (escritorio_id = 1) é aplicado no backend (dashboard_routes.py).
        # VALOR_AM (rubricas.valor_rubrica) é o valor de comissão fixo por rubrica —
        # equivalente ao VALOR_AM do banco `ng`, adicionado em 04/09/2026. Consumido por
        # app.analyses.NG.comissao_lexpre.get_comissao_base. Nem toda rubrica tem valor
        # cadastrado ainda (NULL vira R$0 na soma, via `_converter_valor`).
        #
        # AREA_ATUACAO_ID/NOME (17/09/2026): a "área de atuação" de verdade do dashboard
        # antigo NÃO é `rubricas.operacao_id`/`public.operacao` (que no lexpre é mais um
        # código de escritório/operação — NGAM/NGPB/NGPA/CONSUMIDOR/ADMINISTRATIVO) — é
        # `public.operacao.area_atuacao_id`, que aponta pra `public.area_atuacao`
        # (CONSUMIDOR, CIVIL, TRABALHISTA, PENAL, ADMINISTRATIVO, AMBIENTAL,
        # PREVIDENCIÁRIO). Hoje toda rubrica cadastrada usa uma operação de
        # area_atuacao_id=1 (CONSUMIDOR) — outras operações (ex.: "NGAM ADM", associada a
        # area_atuacao_id=5/ADMINISTRATIVO) ainda vão ser criadas. OPERACAO_ID/NOME
        # continuam expostos (compatibilidade com o resto do módulo), mas o filtro/catálogo
        # de "área de atuação" deve usar AREA_ATUACAO_ID/NOME — ver
        # comercial_lexpre.list_areas_atuacao_comerciais/filter_comercial_lexpre_por_area_atuacao.
        "description": "Dados comerciais a partir do banco lexpre (atendimento + demandas), base da nova página Comercial (LexPre).",
        "params": []
    },
    # v1: queries.py:809, "demanda_rubrica_reunida_lexpre_NG" (copiada em 11/11/2026). Comercial e Comissão Comercial (LexPre).
    "demanda_rubrica_reunida_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            drr.demanda_id AS "DEMANDA_ID",
            drr.rubrica_associada_id AS "RUBRICA_ASSOCIADA_ID",
            ra.nome AS "RUBRICA_ASSOCIADA_NOME",
            ra.valor_rubrica AS "RUBRICA_ASSOCIADA_VALOR_AM"
        FROM public.demanda_rubrica_reunida drr
        LEFT JOIN public.rubricas ra
            ON drr.rubrica_associada_id = ra.id
        """,
        # Mapa demanda -> rubricas associadas REALMENTE configuradas para aquela demanda
        # específica de rubrica "reunida" (pacote), usado para expandir 1 demanda em 1 ação
        # por componente, no cálculo de "ações fechadas" da página Comercial (LexPre).
        #
        # Corrigido em 04/09/2026: antes essa expansão usava `public.rubricas_reunidas`
        # (mapa GENÉRICO rubrica_id do pacote -> TODAS as associadas já cadastradas para
        # aquele tipo de pacote, ex.: 24 associadas para RUBRICAS_BRADESCO), inflando a
        # contagem de toda demanda daquele pacote pelas 24, mesmo quando só 3-5 delas
        # realmente se aplicavam ao caso do cliente. `demanda_rubrica_reunida` é a tabela
        # correta: guarda, por demanda, só os componentes que o time realmente configurou
        # para AQUELE caso. RUBRICA_ASSOCIADA_VALOR_AM é o VALOR_AM (rubricas.valor_rubrica)
        # da PRÓPRIA associada, não do pacote — o pacote normalmente não tem valor cadastrado
        # (ex.: RUBRICAS_BRADESCO), quem carrega a comissão são os componentes (ver
        # comercial_lexpre.build_mapa_valor_rubrica_associada).
        "description": "Componentes reais de cada demanda de rubrica 'reunida' (pacote), por demanda específica (banco lexpre).",
        "params": []
    },
    # v1: queries.py:839, "audit_log_demandas_canceladas_lexpre_NG" (copiada em 11/11/2026). Comercial e Comissão Comercial (LexPre).
    "audit_log_demandas_canceladas_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            al.entidade_id AS "ID_DEMANDA",
            al.created_at AS "DATA_CANCELAMENTO",
            al.escritorio_id AS "ESCRITORIO_ID"
        FROM public.audit_log al
        WHERE al.entidade = 'demanda'
          AND al.acao = 'demanda.cancelada'
        """,
        # Trilha de auditoria (public.audit_log) do momento exato em que cada demanda
        # foi cancelada — usada em app.analyses.NG.comissao_lexpre para descontar, da
        # comissão do Comercial, o VALOR_AM de demandas cuja comissão já tinha sido
        # paga em um período ANTERIOR (DATA_ASSINATURA antes do período atual) mas que
        # foram canceladas DENTRO do período atual (ex.: atendente comissiona por um
        # RMC fechado no fim de agosto, cliente cancela em setembro — o valor precisa
        # ser descontado da comissão de setembro, não retroagir sobre agosto, que já
        # foi pago). entidade_id é o id de public.demandas (entidade = 'demanda').
        "description": "Eventos de cancelamento de demanda (banco lexpre), usados para desconto de comissão por cancelamento tardio.",
        "params": []
    },
}
