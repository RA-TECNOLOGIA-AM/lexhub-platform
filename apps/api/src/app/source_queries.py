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
    # v1: queries.py:1326, "execucao_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "execucao_LA": {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_escritorio_assinante as "ID_ESCRITORIO",
            ea.razao_social as "ESCRITORIO",
            CASE
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END as "DATA_EXECUCAO",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END as "DATA_DISTRIBUICAO",
            p.numero_processo as "NUMERO_PROCESSO",
            p.id_fase AS "ID_FASE",
            f.description as "FASE",
            p.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            sp.description as "SUBFASE",
            m.description as "MATERIA",
            p.id_area_atuacao as "ID_AREA_ATUACAO",
            aa.description as "AREA_ATUACAO",
            p.uf as "UF",
            c.nome as "COMARCA",
            v.grau as "VARA",
            cp.nome as "COMPETENCIA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END as "ULTIMA_MOVIMENTACAO",
            p.valor_causa as "VALOR_CAUSA",
            p.valor_dano_material as "DANO_MATERIAL",
            p.valor_dano_moral as "DANO_MORAL",
            p.valor_causa_ve as "VALOR_EXECUCAO",
            p.dano_material_ve as "DANO_MATERIAL_EXECUCAO",
            p.dano_moral_ve as "DANO_MORAL_EXECUCAO",
            p.valor_honorarios_contratuais as "VALOR_HONORARIOS",
            p.valor_ted as "VALOR_TED",
            p.valor_ted_2 as "VALOR_TED_2",
            p.valor_ted_3 as "VALOR_TED_3",
            CASE
                WHEN p.transito_julgado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                THEN p.transito_julgado
            END as "DATA_TRANSITO_JULGADO",
            CASE
                WHEN p.encerramento IS NOT NULL
                    AND EXTRACT(YEAR FROM p.encerramento) BETWEEN 1900 AND 2100
                THEN p.encerramento
            END as "DATA_ENCERRAMENTO",
            GREATEST(
                CASE
                    WHEN p.transito_julgado IS NOT NULL
                        AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                    THEN p.transito_julgado
                END,
                CASE
                    WHEN p.encerramento IS NOT NULL
                        AND EXTRACT(YEAR FROM p.encerramento) BETWEEN 1900 AND 2100
                    THEN p.encerramento
                END
            ) as "DATA_SAIDA",
            CASE
                WHEN p.data_compensacao_alvara IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_compensacao_alvara) BETWEEN 1900 AND 2100
                THEN p.data_compensacao_alvara
            END as "DATA_COMPENSACAO_ALVARA",
            CASE
                WHEN p.data_compensacao_alvara_incontroverso IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_compensacao_alvara_incontroverso) BETWEEN 1900 AND 2100
                THEN p.data_compensacao_alvara_incontroverso
            END as "DATA_COMPENSACAO_ALVARA_INCONTROVERSO",
            p.valor_incontroverso as "VALOR_INCONTROVERSO",
            p.valor_remanescente as "VALOR_REMANESCENTE",
            CASE
                WHEN p.data_expedicao_alvara IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara
            END as "DATA_EXPEDICAO_ALVARA",
            CASE
                WHEN p.data_expedicao_alvara_incontroverso IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara_incontroverso) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara_incontroverso
            END as "DATA_EXPEDICAO_ALVARA_INCONTROVERSO",
            p.valor_multas as "VALOR_MULTAS",
            p.valor_sucumbencia_porcentagem as "SUCUMBENCIA_PORCENTAGEM",
            p.valor_sucumbencia as "VALOR_SUCUMBENCIA",
            p.valor_alvara as "VALOR_ALVARA",
            p.valor_alvara_incontroverso as "VALOR_ALVARA_INCONTROVERSO",
            EXISTS (
                SELECT 1
                FROM public.processo_etiqueta pe
                JOIN public.etiquetas et ON et.id = pe.id_etiqueta
                WHERE pe.id_processo = p.id
                    AND et.nome ILIKE 'acordo'
            ) as "TEM_ETIQUETA_ACORDO"

        from public.processo p
        left join public.materia m on p.id_materia = m.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id
        left join public.area_atuacao aa on p.id_area_atuacao = aa.id
        left join public.fase f on p.id_fase = f.id
        left join public.status_processual sp on p.id_status_processual = sp.id
        left join public.comarca c on p.id_comarca = c.id
        left join public.vara v on p.id_vara = v.id
        left join public.competencias cp on p.id_competencia = cp.id
        left join public.situacao sit on sit.id = p.id_situacao

        where p.id_situacao in (1, 2)
        """,
        "description": (
            "Dados do setor de Execução do Escritorio Luis Albert AM. "
            "id_situacao IN (1, 2) = ATIVO + ARQUIVADO — processos já compensados "
            "(pagos) saem da fase Financeiro e ficam arquivados (arquivado por "
            "procedência, motivo Valor Compensado); precisam continuar aparecendo "
            "no histórico de saídas (quantidade e valor) da Execução. "
            "DATA_COMPENSACAO_ALVARA é a data usada para definir a saída da "
            "Execução (quantidade e valor)."
        ),
        "params": []
    },
    # v1: queries.py:1452, "execucao_RJ" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "execucao_RJ": {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_escritorio_assinante as "ID_ESCRITORIO",
            ea.razao_social as "ESCRITORIO",
            CASE
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END as "DATA_EXECUCAO",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END as "DATA_DISTRIBUICAO",
            p.numero_processo as "NUMERO_PROCESSO",
            p.id_fase AS "ID_FASE",
            f.description as "FASE",
            p.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            sp.description as "SUBFASE",
            m.description as "MATERIA",
            p.id_area_atuacao as "ID_AREA_ATUACAO",
            aa.description as "AREA_ATUACAO",
            p.uf as "UF",
            c.nome as "COMARCA",
            v.grau as "VARA",
            cp.nome as "COMPETENCIA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END as "ULTIMA_MOVIMENTACAO",
            p.valor_causa as "VALOR_CAUSA",
            p.valor_dano_material as "DANO_MATERIAL",
            p.valor_dano_moral as "DANO_MORAL",
            p.valor_causa_ve as "VALOR_EXECUCAO",
            p.dano_material_ve as "DANO_MATERIAL_EXECUCAO",
            p.dano_moral_ve as "DANO_MORAL_EXECUCAO",
            p.valor_honorarios_contratuais as "VALOR_HONORARIOS",
            p.valor_ted as "VALOR_TED",
            p.valor_ted_2 as "VALOR_TED_2",
            p.valor_ted_3 as "VALOR_TED_3",
            CASE
                WHEN p.transito_julgado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                THEN p.transito_julgado
            END as "DATA_TRANSITO_JULGADO",
            CASE
                WHEN p.encerramento IS NOT NULL
                    AND EXTRACT(YEAR FROM p.encerramento) BETWEEN 1900 AND 2100
                THEN p.encerramento
            END as "DATA_ENCERRAMENTO",
            GREATEST(
                CASE
                    WHEN p.transito_julgado IS NOT NULL
                        AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                    THEN p.transito_julgado
                END,
                CASE
                    WHEN p.encerramento IS NOT NULL
                        AND EXTRACT(YEAR FROM p.encerramento) BETWEEN 1900 AND 2100
                    THEN p.encerramento
                END
            ) as "DATA_SAIDA",
            CASE
                WHEN p.data_compensacao_alvara IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_compensacao_alvara) BETWEEN 1900 AND 2100
                THEN p.data_compensacao_alvara
            END as "DATA_COMPENSACAO_ALVARA",
            CASE
                WHEN p.data_compensacao_alvara_incontroverso IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_compensacao_alvara_incontroverso) BETWEEN 1900 AND 2100
                THEN p.data_compensacao_alvara_incontroverso
            END as "DATA_COMPENSACAO_ALVARA_INCONTROVERSO",
            p.valor_incontroverso as "VALOR_INCONTROVERSO",
            p.valor_remanescente as "VALOR_REMANESCENTE",
            CASE
                WHEN p.data_expedicao_alvara IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara
            END as "DATA_EXPEDICAO_ALVARA",
            CASE
                WHEN p.data_expedicao_alvara_incontroverso IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara_incontroverso) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara_incontroverso
            END as "DATA_EXPEDICAO_ALVARA_INCONTROVERSO",
            p.valor_multas as "VALOR_MULTAS",
            p.valor_sucumbencia_porcentagem as "SUCUMBENCIA_PORCENTAGEM",
            p.valor_sucumbencia as "VALOR_SUCUMBENCIA",
            p.valor_alvara as "VALOR_ALVARA",
            p.valor_alvara_incontroverso as "VALOR_ALVARA_INCONTROVERSO",
            -- RJ não tem uma etiqueta base "ACORDO" isolada por nome (diferente do
            -- NG/LA, que usam EXISTS em processo_etiqueta/etiquetas com nome ILIKE
            -- 'acordo') — usa 4 etiquetas via id_etiquetas_lista, igual à query
            -- execucao_acordos_RJ: 73 e 74 = ACORDO - PRÉ SENTENÇA (cadastro
            -- duplicado, mesmo nome, ids diferentes), 75 = ACORDO - EXTRAJUDICIAL,
            -- 76 = ACORDO - JUDICIAL.
            (
                COALESCE(p.id_etiquetas_lista::jsonb @> '[73]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[74]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[75]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[76]'::jsonb, false)
            ) as "TEM_ETIQUETA_ACORDO"

        from public.processo p
        left join public.materia m on p.id_materia = m.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id
        left join public.area_atuacao aa on p.id_area_atuacao = aa.id
        left join public.fase f on p.id_fase = f.id
        left join public.status_processual sp on p.id_status_processual = sp.id
        left join public.comarca c on p.id_comarca = c.id
        left join public.vara v on p.id_vara = v.id
        left join public.competencias cp on p.id_competencia = cp.id
        left join public.situacao sit on sit.id = p.id_situacao

        where p.id_situacao in (1, 2)
        """,
        "description": (
            "Dados do setor de Execução (Condenação) do Escritorio Luis Albert RJ "
            "(LARJ, ID_ESCRITORIO=27). Mesmo formato de execucao_LA, mas com "
            "TEM_ETIQUETA_ACORDO calculado pelos ids de etiqueta 73/74/75/76 "
            "(id_etiquetas_lista), já que RJ não tem etiqueta base 'Acordo' por "
            "nome. id_situacao IN (1, 2) = ATIVO + ARQUIVADO, mesmo motivo de "
            "execucao_LA."
        ),
        "params": []
    },
    # v1: queries.py:1582, "execucao_acordos_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "execucao_acordos_NG": {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_escritorio_assinante as "ID_ESCRITORIO",
            p.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.razao_social as "ESCRITORIO",
            CASE
                WHEN p.acordo_fechado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_fechado) BETWEEN 1900 AND 2100
                THEN p.acordo_fechado
            END as "DATA_ACORDO_FECHADO",
            CASE
                WHEN p.acordo_homologado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_homologado) BETWEEN 1900 AND 2100
                THEN p.acordo_homologado
            END as "DATA_ACORDO_HOMOLOGADO",
            CASE
                WHEN p.pagamento_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.pagamento_acordo) BETWEEN 1900 AND 2100
                THEN p.pagamento_acordo
            END as "DATA_PAGAMENTO_ACORDO",
            CASE
                WHEN p.data_expedicao_alvara_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara_acordo) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara_acordo
            END as "DATA_EXPEDICAO_ALVARA_ACORDO",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END as "DATA_DISTRIBUICAO",
            CASE
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END as "DATA_EXECUCAO",
            p.numero_processo as "NUMERO_PROCESSO",
            p.id_fase AS "ID_FASE",
            f.description as "FASE",
            sp.description as "SUBFASE",
            m.description as "MATERIA",
            p.id_area_atuacao as "ID_AREA_ATUACAO",
            aa.description as "AREA_ATUACAO",
            p.uf as "UF",
            c.nome as "COMARCA",
            v.grau as "VARA",
            cp.nome as "COMPETENCIA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END as "ULTIMA_MOVIMENTACAO",
            p.valor_alcada_final as "VALOR_ALCADA_FINAL",
            p.valor_ted as "VALOR_TED",
            p.valor_ted_2 as "VALOR_TED_2",
            p.valor_ted_3 as "VALOR_TED_3",
            p.valor_proposta_recebida as "VALOR_PROPOSTA_RECEBIDA",
            p.valor_contraproposta as "VALOR_CONTRAPROPOSTA",
            p.valor_alvara as "VALOR_ALVARA",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[48]'::jsonb, false) as "TEM_ETIQUETA_ACORDO",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[50]'::jsonb, false) as "TEM_ETIQUETA_JUDICIAL",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[51]'::jsonb, false) as "TEM_ETIQUETA_EXTRAJUDICIAL",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[55]'::jsonb, false) as "TEM_ETIQUETA_PRE_SENTENCA",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[56]'::jsonb, false) as "TEM_ETIQUETA_POS_SENTENCA"

        from public.processo p
        left join public.materia m on p.id_materia = m.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id
        left join public.area_atuacao aa on p.id_area_atuacao = aa.id
        left join public.fase f on p.id_fase = f.id
        left join public.status_processual sp on p.id_status_processual = sp.id
        left join public.comarca c on p.id_comarca = c.id
        left join public.vara v on p.id_vara = v.id
        left join public.competencias cp on p.id_competencia = cp.id
        left join public.situacao sit on sit.id = p.id_situacao

        where p.id_situacao in (1, 2)
        """,
        "description": (
            "Dados de Execução de Acordos do Escritorio Nicolas Gomes (NG). "
            "id_situacao IN (1, 2) = ATIVO + ARQUIVADO — processos com etiqueta "
            "Acordo/acordo_fechado que já foram arquivados (ex.: arquivado por "
            "procedência) precisam continuar aparecendo no histórico de entradas/saídas."
        ),
        "params": []
    },
    # v1: queries.py:1671, "execucao_acordos_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "execucao_acordos_LA": {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_escritorio_assinante as "ID_ESCRITORIO",
            p.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.razao_social as "ESCRITORIO",
            CASE
                WHEN p.acordo_fechado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_fechado) BETWEEN 1900 AND 2100
                THEN p.acordo_fechado
            END as "DATA_ACORDO_FECHADO",
            CASE
                WHEN p.acordo_homologado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_homologado) BETWEEN 1900 AND 2100
                THEN p.acordo_homologado
            END as "DATA_ACORDO_HOMOLOGADO",
            CASE
                WHEN p.pagamento_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.pagamento_acordo) BETWEEN 1900 AND 2100
                THEN p.pagamento_acordo
            END as "DATA_PAGAMENTO_ACORDO",
            CASE
                WHEN p.data_expedicao_alvara_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara_acordo) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara_acordo
            END as "DATA_EXPEDICAO_ALVARA_ACORDO",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END as "DATA_DISTRIBUICAO",
            CASE
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END as "DATA_EXECUCAO",
            p.numero_processo as "NUMERO_PROCESSO",
            p.id_fase AS "ID_FASE",
            f.description as "FASE",
            sp.description as "SUBFASE",
            m.description as "MATERIA",
            p.id_area_atuacao as "ID_AREA_ATUACAO",
            aa.description as "AREA_ATUACAO",
            p.uf as "UF",
            c.nome as "COMARCA",
            v.grau as "VARA",
            cp.nome as "COMPETENCIA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END as "ULTIMA_MOVIMENTACAO",
            p.valor_alcada_final as "VALOR_ALCADA_FINAL",
            p.valor_ted as "VALOR_TED",
            p.valor_ted_2 as "VALOR_TED_2",
            p.valor_ted_3 as "VALOR_TED_3",
            p.valor_proposta_recebida as "VALOR_PROPOSTA_RECEBIDA",
            p.valor_contraproposta as "VALOR_CONTRAPROPOSTA",
            p.valor_alvara as "VALOR_ALVARA",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[49]'::jsonb, false) as "TEM_ETIQUETA_ACORDO",
            -- LA não tem etiquetas JUDICIAL/EXTRAJUDICIAL isoladas (ids 52/53 cadastrados mas nunca usados) nem
            -- PRÉ/PÓS-SENTENÇA isoladas (diferente do NG, ids 55/56) — em vez disso usa 4 etiquetas combinadas:
            -- 68=ACORDO PRÉ-SENTENÇA - JUDICIAL, 69=ACORDO PRÉ-SENTENÇA - EXTRAJUDICIAL,
            -- 70=ACORDO PÓS-SENTENÇA - JUDICIAL, 71=ACORDO PÓS-SENTENÇA - EXTRAJUDICIAL.
            -- Cada uma das 4 booleans abaixo é derivada combinando o par correspondente.
            COALESCE(p.id_etiquetas_lista::jsonb @> '[68]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[70]'::jsonb, false) as "TEM_ETIQUETA_JUDICIAL",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[69]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[71]'::jsonb, false) as "TEM_ETIQUETA_EXTRAJUDICIAL",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[68]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[69]'::jsonb, false) as "TEM_ETIQUETA_PRE_SENTENCA",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[70]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[71]'::jsonb, false) as "TEM_ETIQUETA_POS_SENTENCA"

        from public.processo p
        left join public.materia m on p.id_materia = m.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id
        left join public.area_atuacao aa on p.id_area_atuacao = aa.id
        left join public.fase f on p.id_fase = f.id
        left join public.status_processual sp on p.id_status_processual = sp.id
        left join public.comarca c on p.id_comarca = c.id
        left join public.vara v on p.id_vara = v.id
        left join public.competencias cp on p.id_competencia = cp.id
        left join public.situacao sit on sit.id = p.id_situacao

        where p.id_situacao in (1, 2)
        """,
        "description": (
            "Dados de Execução de Acordos do Escritorio Luis Albert AM (LA). "
            "id_situacao IN (1, 2) = ATIVO + ARQUIVADO — processos com etiqueta "
            "Acordo/acordo_fechado que já foram arquivados (ex.: arquivado por "
            "procedência) precisam continuar aparecendo no histórico de entradas/saídas."
        ),
        "params": []
    },
    # v1: queries.py:1769, "execucao_acordos_RJ" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "execucao_acordos_RJ": {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_escritorio_assinante as "ID_ESCRITORIO",
            p.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.razao_social as "ESCRITORIO",
            CASE
                WHEN p.acordo_fechado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_fechado) BETWEEN 1900 AND 2100
                THEN p.acordo_fechado
            END as "DATA_ACORDO_FECHADO",
            CASE
                WHEN p.acordo_homologado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordo_homologado) BETWEEN 1900 AND 2100
                THEN p.acordo_homologado
            END as "DATA_ACORDO_HOMOLOGADO",
            CASE
                WHEN p.pagamento_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.pagamento_acordo) BETWEEN 1900 AND 2100
                THEN p.pagamento_acordo
            END as "DATA_PAGAMENTO_ACORDO",
            CASE
                WHEN p.data_expedicao_alvara_acordo IS NOT NULL
                    AND EXTRACT(YEAR FROM p.data_expedicao_alvara_acordo) BETWEEN 1900 AND 2100
                THEN p.data_expedicao_alvara_acordo
            END as "DATA_EXPEDICAO_ALVARA_ACORDO",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END as "DATA_DISTRIBUICAO",
            CASE
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END as "DATA_EXECUCAO",
            p.numero_processo as "NUMERO_PROCESSO",
            p.id_fase AS "ID_FASE",
            f.description as "FASE",
            sp.description as "SUBFASE",
            m.description as "MATERIA",
            p.id_area_atuacao as "ID_AREA_ATUACAO",
            aa.description as "AREA_ATUACAO",
            p.uf as "UF",
            c.nome as "COMARCA",
            v.grau as "VARA",
            cp.nome as "COMPETENCIA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END as "ULTIMA_MOVIMENTACAO",
            p.valor_alcada_final as "VALOR_ALCADA_FINAL",
            p.valor_ted as "VALOR_TED",
            p.valor_ted_2 as "VALOR_TED_2",
            p.valor_ted_3 as "VALOR_TED_3",
            p.valor_proposta_recebida as "VALOR_PROPOSTA_RECEBIDA",
            p.valor_contraproposta as "VALOR_CONTRAPROPOSTA",
            p.valor_alvara as "VALOR_ALVARA",
            -- RJ não tem uma etiqueta base "ACORDO" isolada (diferente do NG=48/LA=49) — usa só 4
            -- etiquetas, cada uma mapeando para exatamente 1 flag (sem combinação, diferente do LA):
            -- 73 e 74 = ACORDO - PRÉ SENTENÇA (cadastro duplicado, mesmo nome, ids diferentes),
            -- 75 = ACORDO - EXTRAJUDICIAL, 76 = ACORDO - JUDICIAL. Não existe etiqueta de
            -- PÓS-SENTENÇA para RJ ainda — TEM_ETIQUETA_POS_SENTENCA fica hardcoded false.
            -- TEM_ETIQUETA_ACORDO usa qualquer uma das 4 como melhor sinal disponível de
            -- "processo é de Acordo", já que não há tag base dedicada.
            (
                COALESCE(p.id_etiquetas_lista::jsonb @> '[73]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[74]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[75]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[76]'::jsonb, false)
            ) as "TEM_ETIQUETA_ACORDO",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[76]'::jsonb, false) as "TEM_ETIQUETA_JUDICIAL",
            COALESCE(p.id_etiquetas_lista::jsonb @> '[75]'::jsonb, false) as "TEM_ETIQUETA_EXTRAJUDICIAL",
            (
                COALESCE(p.id_etiquetas_lista::jsonb @> '[73]'::jsonb, false)
                OR COALESCE(p.id_etiquetas_lista::jsonb @> '[74]'::jsonb, false)
            ) as "TEM_ETIQUETA_PRE_SENTENCA",
            false as "TEM_ETIQUETA_POS_SENTENCA"

        from public.processo p
        left join public.materia m on p.id_materia = m.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id
        left join public.area_atuacao aa on p.id_area_atuacao = aa.id
        left join public.fase f on p.id_fase = f.id
        left join public.status_processual sp on p.id_status_processual = sp.id
        left join public.comarca c on p.id_comarca = c.id
        left join public.vara v on p.id_vara = v.id
        left join public.competencias cp on p.id_competencia = cp.id
        left join public.situacao sit on sit.id = p.id_situacao

        where p.id_situacao in (1, 2)
        """,
        "description": (
            "Dados de Execução de Acordos do Escritorio Luis Albert RJ (LARJ). "
            "id_situacao IN (1, 2) = ATIVO + ARQUIVADO — processos com etiqueta "
            "Acordo/acordo_fechado que já foram arquivados (ex.: arquivado por "
            "procedência) precisam continuar aparecendo no histórico de entradas/saídas."
        ),
        "params": []
    },
    # v1: queries.py:3123, "agendamentos_setor_execucao_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_NG": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.numero_processo                               AS "NUMERO_PROCESSO",
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO'                                      AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO",
            ps.valor_causa_vs                               AS "VALOR_CAUSA_SENTENCA",
            ps.valor_causa_va                               AS "VALOR_CAUSA_ACORDO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'EXECUÇÃO - %'
        """,
        "description": (
            "Agendamentos do setor EXECUÇÃO (NG) via vw_dashboard_agendamentos_detalhados, "
            "com motivo_encaminhamento (join direto em agendamento) para identificar o motivo "
            "de atividades encerradas como 'Encerrado Não Cumprido'. VALOR_CAUSA_SENTENCA/"
            "VALOR_CAUSA_ACORDO (processo.valor_causa_vs/va) para a Confecção CS."
        ),
        "params": []
    },
    # v1: queries.py:3033, "agendamentos_setor_execucao_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_LA": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.numero_processo                               AS "NUMERO_PROCESSO",
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO'                                      AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO",
            ps.valor_causa_vs                               AS "VALOR_CAUSA_SENTENCA",
            ps.valor_causa_va                               AS "VALOR_CAUSA_ACORDO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'EXECUÇÃO - %'
        """,
        "description": (
            "Agendamentos do setor EXECUÇÃO (LA) via vw_dashboard_agendamentos_detalhados, "
            "com motivo_encaminhamento (join direto em agendamento) para identificar o motivo "
            "de atividades encerradas como 'Encerrado Não Cumprido'. VALOR_CAUSA_SENTENCA/"
            "VALOR_CAUSA_ACORDO (processo.valor_causa_vs/va) para a Confecção CS."
        ),
        "params": []
    },
    # v1: queries.py:3077, "agendamentos_setor_execucao_LA_RJ" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_LA_RJ": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.numero_processo                               AS "NUMERO_PROCESSO",
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO'                                      AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO",
            ps.valor_causa_vs                               AS "VALOR_CAUSA_SENTENCA",
            ps.valor_causa_va                               AS "VALOR_CAUSA_ACORDO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'EXECUÇÃO - %'
        """,
        "description": (
            "Agendamentos do setor EXECUÇÃO (Escritorio Luis Albert RJ - LARJ) via "
            "vw_dashboard_agendamentos_detalhados, com motivo_encaminhamento (join direto "
            "em agendamento) para identificar o motivo de atividades encerradas como "
            "'Encerrado Não Cumprido'. Usado pela seção Atividades do dashboard "
            "Execução Condenação RJ. VALOR_CAUSA_SENTENCA/VALOR_CAUSA_ACORDO "
            "(processo.valor_causa_vs/va) para a Confecção CS."
        ),
        "params": []
    },
    # v1: queries.py:1873, "agendamentos_fechamento_acordos_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_fechamento_acordos_NG": {
        "database": "lexflow",
        "query": """
        select
            v.processo_id,
            v.numero_processo as "NUMERO_PROCESSO",
            v.setor_atividade_nome as "SETOR_ATIVIDADE",
            v.agendamento_status as "STATUS",
            v.data_hora_conclusao as "DATA_HORA_CONCLUSAO",
            ps.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO"

        from public.vw_dashboard_agendamentos_detalhados v
        left join public.processo ps on ps.id = CAST(v.processo_id AS INTEGER)
        left join public.situacao sit on sit.id = ps.id_situacao

        where v.id_escritorio_assinante = 20
            and (
                v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA ENVIADA%'
                or v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA RECEBIDA%'
            )
        """,
        "description": (
            "Agendamentos de PROPOSTA ENVIADA/PROPOSTA RECEBIDA do setor ACORDOS (NG). "
            "Quando o status é 'Encerrado Cumprido', DATA_HORA_CONCLUSAO marca o início "
            "da negociação de acordo do processo (vinculação cumprida)."
        ),
        "params": []
    },
    # v1: queries.py:1934, "agendamentos_fechamento_acordos_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_fechamento_acordos_LA": {
        "database": "lexflow",
        "query": """
        select
            v.processo_id,
            v.numero_processo as "NUMERO_PROCESSO",
            v.setor_atividade_nome as "SETOR_ATIVIDADE",
            v.agendamento_status as "STATUS",
            v.data_hora_conclusao as "DATA_HORA_CONCLUSAO",
            ps.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO"

        from public.vw_dashboard_agendamentos_detalhados v
        left join public.processo ps on ps.id = CAST(v.processo_id AS INTEGER)
        left join public.situacao sit on sit.id = ps.id_situacao

        where v.id_escritorio_assinante = 21
            and (
                v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA ENVIADA%'
                or v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA RECEBIDA%'
            )
        """,
        "description": (
            "Agendamentos de PROPOSTA ENVIADA/PROPOSTA RECEBIDA do setor ACORDOS "
            "(Escritorio Luis Albert AM - LA). Quando o status é 'Encerrado Cumprido', "
            "DATA_HORA_CONCLUSAO marca o início da negociação de acordo do processo "
            "(vinculação cumprida). LA ainda não usa esses nomes de setor exatos hoje "
            "(consulta retorna 0 linhas), mas fica pronta para quando o fluxo for adotado."
        ),
        "params": []
    },
    # v1: queries.py:1965, "agendamentos_fechamento_acordos_RJ" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_fechamento_acordos_RJ": {
        "database": "lexflow",
        "query": """
        select
            v.processo_id,
            v.numero_processo as "NUMERO_PROCESSO",
            v.setor_atividade_nome as "SETOR_ATIVIDADE",
            v.agendamento_status as "STATUS",
            v.data_hora_conclusao as "DATA_HORA_CONCLUSAO",
            ps.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO"

        from public.vw_dashboard_agendamentos_detalhados v
        left join public.processo ps on ps.id = CAST(v.processo_id AS INTEGER)
        left join public.situacao sit on sit.id = ps.id_situacao

        where v.id_escritorio_assinante = 27
            and (
                v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA ENVIADA%'
                or v.setor_atividade_nome ilike 'ACORDOS - PROPOSTA RECEBIDA%'
            )
        """,
        "description": (
            "Agendamentos de PROPOSTA ENVIADA/PROPOSTA RECEBIDA do setor ACORDOS "
            "(Escritorio Luis Albert RJ - LARJ). Quando o status é 'Encerrado Cumprido', "
            "DATA_HORA_CONCLUSAO marca o início da negociação de acordo do processo "
            "(vinculação cumprida)."
        ),
        "params": []
    },
    # v1: queries.py:3167, "agendamentos_setor_execucao_acordos_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_acordos_NG": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO DE ACORDOS'                           AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'ACORDOS - %'
        """,
        "description": (
            "Agendamentos do setor ACORDOS (NG) via vw_dashboard_agendamentos_detalhados, "
            "com motivo_encaminhamento (join direto em agendamento) para identificar o motivo "
            "de atividades encerradas como 'Encerrado Não Cumprido'. Usado pela seção "
            "Atividades do dashboard Execução Acordos NG."
        ),
        "params": []
    },
    # v1: queries.py:3208, "agendamentos_setor_execucao_acordos_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_acordos_LA": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO DE ACORDOS'                           AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'ACORDOS - %'
        """,
        "description": (
            "Agendamentos do setor ACORDOS (Escritorio Luis Albert AM - LA) via "
            "vw_dashboard_agendamentos_detalhados, com motivo_encaminhamento (join direto "
            "em agendamento) para identificar o motivo de atividades encerradas como "
            "'Encerrado Não Cumprido'. Usado pela seção Atividades do dashboard "
            "Execução Acordos LA."
        ),
        "params": []
    },
    # v1: queries.py:3249, "agendamentos_setor_execucao_acordos_RJ" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_execucao_acordos_RJ": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'EXECUÇÃO DE ACORDOS'                           AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'ACORDOS - %'
        """,
        "description": (
            "Agendamentos do setor ACORDOS (Escritorio Luis Albert RJ - LARJ) via "
            "vw_dashboard_agendamentos_detalhados, com motivo_encaminhamento (join direto "
            "em agendamento) para identificar o motivo de atividades encerradas como "
            "'Encerrado Não Cumprido'. Usado pela seção Atividades do dashboard "
            "Execução Acordos RJ."
        ),
        "params": []
    },
    # v1: queries.py:2468, "setor_recurso" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "setor_recurso": {
        "database": "lexflow",
        "query": """
        WITH fases_log AS (
            SELECT
                id_processo,

                -- RECURSAL (datas inválidas no log viram NULL — evita falha no asyncpg)
                MAX(
                    CASE
                        WHEN id_fase = 8
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_recursal,
                MAX(
                    CASE
                        WHEN id_fase = 8
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_recursal
            FROM public.log_fase_processual
            GROUP BY id_processo
        ),
        agendamento_recursos_aberto AS (
            SELECT DISTINCT ON (ag.processo_id)
                ag.processo_id,
                sa.id AS id_setor_atividade,
                a.id AS id_atividade,
                a.description AS atividade,
                ag.status AS status_agendamento
            FROM public.agendamento ag
            JOIN public.setor_atividade sa ON sa.id = ag.id_setor_atividade_destino
            JOIN public.setor s ON s.id = sa.id_setor
            JOIN public.atividade a ON a.id = sa.id_atividade
            WHERE sa.id_setor = 16
              AND s.id_escritorio_assinante = 21
              AND sa.ativo = TRUE
              AND ag.status IN ('Recebido', 'Visualizado')
            ORDER BY ag.processo_id, ag.data_hora_criacao DESC NULLS LAST
        )

            SELECT
            p.id,
            p.id_escritorio_assinante                    AS "ID_ESCRITORIO",
            p.id_situacao                                AS "ID_SITUACAO",
            sit.description                              AS "SITUACAO",
            ea.razao_social                              AS "ESCRITORIO",
            p.uf                                         AS "UF",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END                                          AS "DATA_AJUIZAMENTO",
            p.numero_processo                            AS "NUMERO_PROCESSO",
            m.description                                AS "MATERIA",
            pp.razaosocial                               AS "PARTE_ADVERSA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END                                          AS "DATA_ULTIMA_MOVIMENTACAO",
            p.id_fase                                    AS "ID_FASE",
            f.description                                AS "FASE",
            sp.description                               AS "SUBFASE",
            o.descricao                                  AS "OPERACAO",
            p.id_vara                                    AS "VARA",
            p.dano_moral_vs                              AS "DANO_MORAL_SENTENCA",
            p.dano_material_vs                           AS "DANO_MATERIAL_SENTENCA",
            p.valor_causa_vs                             AS "VALOR_CAUSA_SENTENCA",
            p.valor_causa_va                             AS "VALOR_CAUSA_ACORDO",
            p.id_status_grau1                            AS "ID_1G",
            spg.nome                                     AS "STATUS_1G",
            p.juiz_1g                                     AS "JUIZ_1G",
            p.id_status_grau2                            AS "ID_2G",
            ssg.nome                                     AS "STATUS_2G",
            p.id_sentenca_merito_grau1                   AS "ID_SENTENCA_MERITO_1G",
            p.id_acordao_merito_grau2                    AS "ID_ACORDAO_MERITO_2G",
            p.relator_2g                                  AS "RELATOR_2G",
            c.nome                                       AS "COMPETENCIA",
            CASE
                WHEN p.transito_julgado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                THEN p.transito_julgado
            END                                          AS "DATA_TRANSITO_JULGADO",
            CASE
                WHEN p.sentenca IS NOT NULL
                    AND EXTRACT(YEAR FROM p.sentenca) BETWEEN 1900 AND 2100
                THEN p.sentenca
            END                                          AS "DATA_SENTENCA",
            CASE
                WHEN p.acordao_data IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_data) BETWEEN 1900 AND 2100
                THEN p.acordao_data
            END                                          AS "DATA_ACORDAO",

            -- Logs de entrada/saída por fase
            fl.dt_entrada_recursal                       AS "DT_ENTRADA_RECURSAL",
            fl.dt_saida_recursal                         AS "DT_SAIDA_RECURSAL",

            -- Agendamento aberto no setor RECURSOS (escritório LA)
            ara.id_setor_atividade                       AS "ID_SETOR_ATIVIDADE_RECURSOS",
            ara.id_atividade                             AS "ID_ATIVIDADE_RECURSOS",
            ara.atividade                                AS "ATIVIDADE_RECURSOS",
            ara.status_agendamento                       AS "STATUS_AGENDAMENTO_RECURSOS"

        FROM public.processo p
        LEFT JOIN public.escritorio_assinante ea    ON p.id_escritorio_assinante = ea.id
        LEFT JOIN public.materia m                  ON p.id_materia = m.id
        LEFT JOIN public.fase f                     ON p.id_fase = f.id
        LEFT JOIN public.status_processual sp       ON p.id_status_processual = sp.id
        LEFT JOIN public.operacao o                 ON p.id_operacao = o.id
        LEFT JOIN public.status_primeiro_grau spg   ON p.id_status_grau1 = spg.id
        LEFT JOIN public.status_segundo_grau ssg    ON p.id_status_grau2 = ssg.id
        LEFT JOIN public.sentenca_merito_primeiro_grau smpg ON p.id_sentenca_merito_grau1 = smpg.id
        LEFT JOIN public.acordao_merito_segundo_grau ampg   ON p.id_acordao_merito_grau2 = ampg.id
        LEFT JOIN public.adverso_processo ap        ON p.id = ap.id_processo
        LEFT JOIN public.pessoa pp                  ON ap.id_pessoa = pp.id
        LEFT JOIN fases_log fl                      ON p.id = fl.id_processo
        LEFT JOIN public.competencias c             ON p.id_competencia = c.id
        LEFT JOIN agendamento_recursos_aberto ara   ON p.id = ara.processo_id
        LEFT JOIN public.situacao sit               ON sit.id = p.id_situacao

        where p.id_situacao IN (1, 2, 6)
        """,
        "description": (
            "Processos ATIVO + ARQUIVADO + SUSPENSO (padrão sem filtro: só ATIVO, ver app/situacao_processo.py) com agendamento aberto do setor RECURSOS (LA); "
            "filtros de fase, data e atividades em recurso_LA."
        ),
        "params": []
    },
    # v1: queries.py:2810, "setor_recurso_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "setor_recurso_NG": {
        "database": "lexflow",
        "query": """
        WITH fases_log AS (
            SELECT
                id_processo,

                -- RECURSAL (datas inválidas no log viram NULL — evita falha no asyncpg)
                MAX(
                    CASE
                        WHEN id_fase = 8
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_recursal,
                MAX(
                    CASE
                        WHEN id_fase = 8
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_recursal
            FROM public.log_fase_processual
            GROUP BY id_processo
        ),
        agendamento_recursos_aberto AS (
            SELECT DISTINCT ON (ag.processo_id)
                ag.processo_id,
                sa.id AS id_setor_atividade,
                a.id AS id_atividade,
                a.description AS atividade,
                ag.status AS status_agendamento
            FROM public.agendamento ag
            JOIN public.setor_atividade sa ON sa.id = ag.id_setor_atividade_destino
            JOIN public.setor s ON s.id = sa.id_setor
            JOIN public.atividade a ON a.id = sa.id_atividade
            WHERE sa.id_setor = 149
              AND s.id_escritorio_assinante = 20
              AND sa.ativo = TRUE
              AND ag.status IN ('Recebido', 'Visualizado')
            ORDER BY ag.processo_id, ag.data_hora_criacao DESC NULLS LAST
        )

            SELECT
            p.id,
            p.id_escritorio_assinante                    AS "ID_ESCRITORIO",
            p.id_situacao                                AS "ID_SITUACAO",
            sit.description                              AS "SITUACAO",
            ea.razao_social                              AS "ESCRITORIO",
            p.uf                                         AS "UF",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END                                          AS "DATA_AJUIZAMENTO",
            p.numero_processo                            AS "NUMERO_PROCESSO",
            m.description                                AS "MATERIA",
            pp.razaosocial                               AS "PARTE_ADVERSA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END                                          AS "DATA_ULTIMA_MOVIMENTACAO",
            p.id_fase                                    AS "ID_FASE",
            f.description                                AS "FASE",
            sp.description                               AS "SUBFASE",
            o.descricao                                  AS "OPERACAO",
            p.id_vara                                    AS "VARA",
            p.dano_moral_vs                              AS "DANO_MORAL_SENTENCA",
            p.dano_material_vs                           AS "DANO_MATERIAL_SENTENCA",
            p.valor_causa_vs                             AS "VALOR_CAUSA_SENTENCA",
            p.valor_causa_va                             AS "VALOR_CAUSA_ACORDO",
            p.id_status_grau1                            AS "ID_1G",
            spg.nome                                     AS "STATUS_1G",
            p.juiz_1g                                     AS "JUIZ_1G",
            p.id_status_grau2                            AS "ID_2G",
            ssg.nome                                     AS "STATUS_2G",
            p.id_sentenca_merito_grau1                   AS "ID_SENTENCA_MERITO_1G",
            p.id_acordao_merito_grau2                    AS "ID_ACORDAO_MERITO_2G",
            p.relator_2g                                  AS "RELATOR_2G",
            c.nome                                       AS "COMPETENCIA",
            CASE
                WHEN p.transito_julgado IS NOT NULL
                    AND EXTRACT(YEAR FROM p.transito_julgado) BETWEEN 1900 AND 2100
                THEN p.transito_julgado
            END                                          AS "DATA_TRANSITO_JULGADO",
            CASE
                WHEN p.sentenca IS NOT NULL
                    AND EXTRACT(YEAR FROM p.sentenca) BETWEEN 1900 AND 2100
                THEN p.sentenca
            END                                          AS "DATA_SENTENCA",
            CASE
                WHEN p.acordao_data IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_data) BETWEEN 1900 AND 2100
                THEN p.acordao_data
            END                                          AS "DATA_ACORDAO",
            CASE
                WHEN p.acordao_embargos IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_embargos) BETWEEN 1900 AND 2100
                THEN p.acordao_embargos
            END                                          AS "DATA_ACORDAO_EMBARGOS",

            -- Logs de entrada/saída por fase
            fl.dt_entrada_recursal                       AS "DT_ENTRADA_RECURSAL",
            fl.dt_saida_recursal                         AS "DT_SAIDA_RECURSAL",

            -- Agendamento aberto no setor RECURSOS (escritório NG)
            ara.id_setor_atividade                       AS "ID_SETOR_ATIVIDADE_RECURSOS",
            ara.id_atividade                             AS "ID_ATIVIDADE_RECURSOS",
            ara.atividade                                AS "ATIVIDADE_RECURSOS",
            ara.status_agendamento                       AS "STATUS_AGENDAMENTO_RECURSOS"

        FROM public.processo p
        LEFT JOIN public.escritorio_assinante ea    ON p.id_escritorio_assinante = ea.id
        LEFT JOIN public.materia m                  ON p.id_materia = m.id
        LEFT JOIN public.fase f                     ON p.id_fase = f.id
        LEFT JOIN public.status_processual sp       ON p.id_status_processual = sp.id
        LEFT JOIN public.operacao o                 ON p.id_operacao = o.id
        LEFT JOIN public.status_primeiro_grau spg   ON p.id_status_grau1 = spg.id
        LEFT JOIN public.status_segundo_grau ssg    ON p.id_status_grau2 = ssg.id
        LEFT JOIN public.sentenca_merito_primeiro_grau smpg ON p.id_sentenca_merito_grau1 = smpg.id
        LEFT JOIN public.acordao_merito_segundo_grau ampg   ON p.id_acordao_merito_grau2 = ampg.id
        LEFT JOIN public.adverso_processo ap        ON p.id = ap.id_processo
        LEFT JOIN public.pessoa pp                  ON ap.id_pessoa = pp.id
        LEFT JOIN fases_log fl                      ON p.id = fl.id_processo
        LEFT JOIN public.competencias c             ON p.id_competencia = c.id
        LEFT JOIN agendamento_recursos_aberto ara   ON p.id = ara.processo_id
        LEFT JOIN public.situacao sit               ON sit.id = p.id_situacao

        where p.id_situacao IN (1, 2, 6)
        """,
        "description": (
            "Processos ATIVO + ARQUIVADO + SUSPENSO (padrão sem filtro: só ATIVO, ver app/situacao_processo.py) com agendamento aberto do setor RECURSOS (NG); "
            "filtros de fase, data e atividades em recurso_NG."
        ),
        "params": []
    },
    # v1: queries.py:2750, "agendamentos_setor_recursos_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_recursos_LA": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            SUBSTRING(v.setor_atividade_nome FROM 12)       AS "ATIVIDADE",
            'RECURSOS'                                      AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'RECURSOS - %'
        """,
        "description": "Agendamentos do setor RECURSOS (LA) via vw_dashboard_agendamentos_detalhados.",
        "params": []
    },
    # v1: queries.py:2952, "agendamentos_setor_recursos_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "agendamentos_setor_recursos_NG": {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.agendamento_prazo                             AS "PRAZO",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.data_hora_cancelamento                        AS "DATA_HORA_CANCELAMENTO",
            v.id_usuario_atribuido                          AS "ID_USUARIO_ATRIBUIDO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            v.id_setor_atividade                            AS "ID_SETOR_ATIVIDADE",
            SUBSTRING(v.setor_atividade_nome FROM 12)       AS "ATIVIDADE",
            'RECURSOS'                                      AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            v.numero_processo                               AS "NUMERO_PROCESSO",
            v.motivo                                        AS "MOTIVO",
            ag.motivo_encaminhamento::text                  AS "MOTIVO_ENCAMINHAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        LEFT JOIN public.agendamento ag ON ag.id = v.agendamento_id
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'RECURSOS - %'
        """,
        "description": (
            "Agendamentos do setor RECURSOS (NG) via vw_dashboard_agendamentos_detalhados, "
            "com motivo_encaminhamento (join direto em agendamento) para identificar "
            "encaminhamentos como 'RECURSO CANCELADO' (AVR - RETORNO / RETORNO - CR)."
        ),
        "params": []
    },
    # v1: queries.py:3011, "atividades_setor_recursos_LA" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "atividades_setor_recursos_LA": {
        "database": "lexflow",
        "query": """
        SELECT
            a.id AS id_atividade,
            a.description AS "ATIVIDADE"
        FROM public.setor_atividade sa
        JOIN public.atividade a ON a.id = sa.id_atividade
        WHERE sa.id_setor = 16
          AND sa.ativo = TRUE
        ORDER BY a.description
        """,
        "description": (
            "Catálogo dinâmico de atividades ativas do setor RECURSOS (LA); "
            "usado como whitelist e como opções do filtro de atividade. Substitui "
            "a lista estática antiga (_ATIVIDADES_RECURSOS_LA), que ficou desatualizada "
            "e fazia tarefas de atividades novas sumirem silenciosamente dos KPIs "
            "(ex.: ELABORAR CONTRARRAZÕES APELAÇÃO / ELABORAR CONTRARRAZOES INOMINADO)."
        ),
        "params": []
    },
    # v1: queries.py:2992, "atividades_setor_recursos_NG" (copiada em 11/11/2026). Execução, Acordos e Recursal (LexFlow).
    "atividades_setor_recursos_NG": {
        "database": "lexflow",
        "query": """
        SELECT
            a.id AS id_atividade,
            a.description AS "ATIVIDADE"
        FROM public.setor_atividade sa
        JOIN public.atividade a ON a.id = sa.id_atividade
        WHERE sa.id_setor = 149
          AND sa.ativo = TRUE
        ORDER BY a.description
        """,
        "description": (
            "Catálogo dinâmico de atividades ativas do setor RECURSOS (NG); "
            "usado como whitelist e como opções do filtro de atividade."
        ),
        "params": []
    },
    # v1: queries.py:1047, "setor_protocolo" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "setor_protocolo": {
        "database": "ng",
        "query": """
        SELECT
            pro.id,
            pro."NOME",
            pro."ENTRADA",
            pro."ID_PROCESSO",
            atendente.nome AS "ATENDENTE",
            pro."MATERIA",
            pro."PARTE_ADVERSA",
            pro."VALOR_DA_CAUSA",
            pro."SISTEMA",
            pro."UF",
            pro."STATUS",
            pro."SAIDA",
            pro."ID_ACTION",
            pro."ID_FUNCIONARIO",
            responsavel.nome AS "FUNCIONARIO",
            t.nome_campanha AS "CAMPANHA",
            pro."REAJUIZAMENTO",
            COALESCE(pro."DANO_MORAL", pet."DANO_MORAL") AS "DANO_MORAL",
            COALESCE(pro."DANO_MATERIAL", pet."DANO_MATERIAL") AS "DANO_MATERIAL",
            pro."DATA_CONTRATACAO",
            r.area_atuacao_id AS "AREA_ATUACAO_ID"
        FROM protocolo.protocolo pro
        LEFT JOIN "public".actions a ON pro."ID_ACTION" = a.id
        LEFT JOIN "public".trackeamento t ON a.id_tracking = t.id
        LEFT JOIN "Setores".funcionarios atendente ON a.atendente_comercial = atendente.id
        LEFT JOIN "Setores".funcionarios responsavel ON pro."ID_FUNCIONARIO" = responsavel.id
        LEFT JOIN juridico.processos jp ON pro."ID_PROCESSO" = jp.id
        LEFT JOIN juridico.rubricas r ON jp."ID_RUBRICA" = r.id
        LEFT JOIN peticionamento."Peticionamento" pet ON pro."ID_PROCESSO" = pet."ID_PROCESSO"
        """,
        "description": "Protocolo do banco NG",
        "params": []
    },
    # v1: queries.py:521, "comercial_geral_NG" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "comercial_geral_NG": {
        "database": "ng",
        "query": """
        WITH acoes_base AS (
            SELECT
                a.id AS "ID_ACTION",
                c.nome AS "CLIENTE",
                f.nome AS "ATENDENTE",
                t.canal_aquisicao AS "CANAL_ATUAL",
                ac.motivo_encerramento,
                tse."NOME" AS "MOTIVO_ENCERRAMENTO_NOME",
                tu.uf AS "UF",
                GREATEST(ac.fechado_em, ac.data_upsell) AS "ASSINATURA",
                f.ativo AS "ATIVO"
            FROM "public".actions a
            INNER JOIN "public".action_status ac
                ON a.id_status = ac.id
            LEFT JOIN "public".customers c
                ON a.customer = c.id
            LEFT JOIN "public".trackeamento t
                ON a.id_tracking = t.id
            LEFT JOIN "public".type_uf tu
                ON a.id_uf = tu.id_uf
            LEFT JOIN "Setores".funcionarios f
                ON a.atendente_comercial = f.id
            LEFT JOIN "public".type_status_encerramento tse
                ON ac.motivo_encerramento = tse.id
            WHERE ac.motivo_encerramento = 11
        ),
        proc_rubricas AS (
            SELECT
                jp."ID_ACTION",
                jp."ID_RUBRICA",
                jp."REAJUIZAMENTO",
                jp.status AS "STATUS",
                tsp.status AS "STATUS_PROCESSO_NOME",
                jr_exp."RUBRICA",
                jr_exp."VALOR_AM",
                jr_exp."AREA_ATUACAO_ID"
            FROM juridico.processos jp
            LEFT JOIN juridico.type_status_processo tsp
                ON jp.status = tsp.id
            LEFT JOIN LATERAL (
                SELECT
                    r2."RUBRICA",
                    r2."valor_AM" AS "VALOR_AM",
                    r2.area_atuacao_id AS "AREA_ATUACAO_ID"
                FROM juridico.processo_rubricas_reunidas prr
                JOIN juridico.rubricas r2
                    ON r2.id = prr.rubrica_id
                WHERE jp."ID_RUBRICA" IN (79, 85)
                  AND prr.processo_id = jp.id

                UNION ALL

                SELECT
                    r1."RUBRICA",
                    r1."valor_AM" AS "VALOR_AM",
                    r1.area_atuacao_id AS "AREA_ATUACAO_ID"
                FROM juridico.rubricas r1
                WHERE jp."ID_RUBRICA" NOT IN (79, 85)
                  AND r1.id = jp."ID_RUBRICA"
            ) jr_exp ON TRUE
        )
        SELECT
            ab."ID_ACTION",
            ab."CLIENTE",
            ab."ATENDENTE",
            ab."CANAL_ATUAL",
            ab.motivo_encerramento,
            ab."MOTIVO_ENCERRAMENTO_NOME",
            ab."UF",
            ab."ASSINATURA",
            ab."ATIVO",
            pr."ID_RUBRICA",
            pr."REAJUIZAMENTO",
            pr."STATUS",
            pr."STATUS_PROCESSO_NOME",
            pr."RUBRICA",
            pr."VALOR_AM",
            pr."AREA_ATUACAO_ID",
            aa.nome_area AS "AREA_ATUACAO_NOME"
        FROM acoes_base ab
        LEFT JOIN proc_rubricas pr
            ON ab."ID_ACTION" = pr."ID_ACTION"
        LEFT JOIN juridico."area_atuação" aa
            ON pr."AREA_ATUACAO_ID" = aa.id
        """,
        "description": "Dados comerciais gerais do banco NG",
        "params": []
    },
    # v1: queries.py:1008, "setor_confeccao" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "setor_confeccao": {
        "database": "ng",
        "query": """
        SELECT
            pp.id,
            pp."NOME",
            pp."ID_PROCESSO",
            pp."ENTRADA",
            pp."ID_ACTION",
            pp."UF",
            pp."STATUS",
            pp."DATA_CONFECCAO",
            pp."MATERIA",
            pp."PARTE_ADVERSA",
            pp."VALOR_DA_CAUSA",
            pp."DANO_MATERIAL",
            pp."DANO_MORAL",
            pp."SISTEMA",
            pp."ID_FUNCIONARIO",
            f.nome AS "FUNCIONARIO",
            pr."ID_PETICAO",
            pp."REAJUIZAMENTO",
            pp."DATA_CONTRATACAO",
            a.atendente_comercial AS "ID_ATENDENTE_COMERCIAL",
            fc.nome AS "ATENDENTE_COMERCIAL",
            pr.pet_auto AS "PET_AUTO",
            pp."DANO_MORAL",
            r.area_atuacao_id AS "AREA_ATUACAO_ID"
        FROM peticionamento."Peticionamento" pp
        JOIN "Setores".funcionarios f ON pp."ID_FUNCIONARIO" = f.id
        JOIN juridico.processos pr ON pp."ID_PROCESSO" = pr.id
        JOIN "public".actions a ON pp."ID_ACTION" = a.id
        LEFT JOIN "Setores".funcionarios fc ON a.atendente_comercial = fc.id
        LEFT JOIN juridico.rubricas r ON pr."ID_RUBRICA" = r.id
        """,
        "description": "Confecção de petições do banco NG",
        "params": []
    },
    # v1: queries.py:976, "setor_org_doc" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "setor_org_doc": {
        "database": "ng",
        "query": """
        SELECT
            od.id,
            od."NOME",
            od."ENTRADA",
            od."UF",
            od."STATUS",
            od."ORIGEM",
            od."ATENDENTE_COMERCIAL",
            od."ID_ACTION",
            od."SAIDA",
            od."ID_PROCESSO",
            od."MATERIA",
            od."DATA_CONTRATACAO",
            od."ID_FUNCIONARIO",
            f.nome AS "FUNCIONARIO",
            p."VALOR_DA_CAUSA",
            od."REAJUIZAMENTO",
            p."DANO_MORAL",
            r.area_atuacao_id AS "AREA_ATUACAO_ID"
        FROM organizacao_doc.organizacao_de_documentos od
        LEFT JOIN "Setores".funcionarios f ON od."ID_FUNCIONARIO" = f.id
        LEFT JOIN peticionamento."Peticionamento" p ON od."ID_PROCESSO" = p."ID_PROCESSO"
        LEFT JOIN juridico.processos jp ON od."ID_PROCESSO" = jp.id
        LEFT JOIN juridico.rubricas r ON jp."ID_RUBRICA" = r.id
        """,
        "description": "Organização de documentos do banco NG",
        "params": []
    },
    # v1: queries.py:946, "setor_pendencias" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "setor_pendencias": {
        "database": "ng",
        "query": """
        SELECT
            pp.id,
            pp."NOME",
            pp."ID_ACTION",
            pp."UF",
            pp."ENTRADA",
            pp."STATUS",
            pp."ATENDENTE",
            pp."SAIDA",
            pp."ORIGEM",
            pp."ID_PROCESSO",
            p."MOTIVO_CANCELAMENTO",
            pp."TIPO_PENDENCIA",
            f.nome AS "FUNCIONARIO",
            pp."ID_FUNCIONARIO",
            pp."DATA_CONTRATACAO",
            pp."REAJUIZAMENTO",
            r.area_atuacao_id AS "AREA_ATUACAO_ID"
        FROM pendencias_de_processos.pendencias_de_processos pp
        LEFT JOIN "Setores".funcionarios f ON pp."ID_FUNCIONARIO" = f.id
        LEFT JOIN juridico.processos p ON pp."ID_PROCESSO" = p.id
        LEFT JOIN juridico.rubricas r ON p."ID_RUBRICA" = r.id
        """,
        "description": "Pendências de processos do banco NG",
        "params": []
    },
    # v1: queries.py:1132, "actions_NG_2" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "actions_NG_2": {
        "database": "ng",
        "query": """
        SELECT
            a."date" AS "ENTRADA",
            a.customer AS "ID_CUSTOMER",
            c.nome AS "CLIENTE",
            tu.uf AS "UF",
            a.id AS "ID_ACTION",
            f.nome AS "ATENDENTE",
            t.nome_campanha AS "CAMPANHA",
            ac.distribuido_em,
            ac.onboarding,
            ac.respondeu_onboarding,
            ac.data_etapa1,
            ac.respondeu_etapa1,
            ac.data_etapa2,
            ac.respondeu_etapa2,
            ac.data_etapa3,
            ac.respondeu_etapa3,
            ac.contrato_criado_em,
            GREATEST(ac.fechado_em, ac.data_upsell) AS "ASSINADO_EM",
            ac.data_encerramento,
            c.tracking_id AS "TRACK_ORIGEM",
            t_origem.canal_aquisicao AS "CANAL_ORIGEM",
            t.id AS "TRACK_ATUAL",
            t.canal_aquisicao AS "CANAL_ATUAL",
            t.tipo_trafego AS "TIPO_TRAFEGO",
            t.prospeccao AS "PROSPECCAO",
            ac.status_id AS "STATUS",
            ac.motivo_encerramento AS "MOTIVO_ENCERRAMENTO"
    
        FROM "public".actions a
        LEFT JOIN "public".action_status ac ON a.id_status = ac.id
        LEFT JOIN "public".type_status ts ON ac.status_id = ts.id
        LEFT JOIN "public".customers c ON a.customer = c.id
        LEFT JOIN "public".trackeamento t ON a.id_tracking = t.id
        LEFT JOIN "public".trackeamento t_origem ON c.tracking_id = t_origem.id
        LEFT JOIN "public".type_uf tu ON a.id_uf = tu.id_uf
        LEFT JOIN "Setores".funcionarios f ON a.atendente_comercial = f.id
        """,
        "description": "Actions do banco NG",
        "params": []
    },
    # v1: queries.py:1085, "rubrica_count_por_processo" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "rubrica_count_por_processo": {
        "database": "ng",
        "query": """
        SELECT
            jp.id AS "ID_PROCESSO",
            COUNT(prr.rubrica_id)::int AS "N_RUBRICAS"
        FROM juridico.processos jp
        JOIN juridico.processo_rubricas_reunidas prr ON prr.processo_id = jp.id
        WHERE jp."ID_RUBRICA" IN (79, 85)
        GROUP BY jp.id
        """,
        "description": "Contagem de sub-rubricas por processo (rubricas reunidas NG)",
        "params": []
    },
    # v1: queries.py:1177, "perfil_clientes_NG" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "perfil_clientes_NG": {
        "database": "ng",
        "query": """
        SELECT
            a."date" AS "ENTRADA",
            a.customer AS "ID_CUSTOMER",
            c.nome AS "CLIENTE",
            c.nascimento AS "DATA_NASCIMENTO",
            c.respondeu_form_socio AS "RESP_TRIAGEM?",
            tec.estado_civil AS "ESTADO_CIVIL",
            tg.genero AS "GENERO",
            c.ocupacao AS "OCUPACAO",
            c.tipo_residencia AS "TIPO_RESIDENCIA",
            c.escolaridade AS "ESCOLARIDADE",
            c.media_mensal AS "MEDIA_MENSAL",
            c.pessoas_dependentes AS "PESSOAS_DEPENDENTES",
            a.id AS "ID_ACTION",
            f.nome AS "ATENDENTE",
            t.nome_campanha AS "CAMPANHA",
            t.plataforma AS "PLATAFORMA",
            t.dispositivo AS "DISPOSITIVO",
            t.canal_aquisicao AS "CANAL_AQUISICAO",
            t.tipo_trafego AS "TIPO_TRAFEGO",
            t.prospeccao AS "PROPECCAO",
            ac.status_id,
            ac.motivo_encerramento,
            tu.uf AS "UF",
            GREATEST(ac.fechado_em, ac.data_upsell) AS "ASSINATURA"
        FROM "public".actions a
        LEFT JOIN "public".action_status ac ON a.id_status = ac.id
        LEFT JOIN "public".type_status ts ON ac.status_id = ts.id
        LEFT JOIN "public".customers c ON a.customer = c.id
        LEFT JOIN "public".trackeamento t ON a.id_tracking = t.id
        LEFT JOIN "public".type_uf tu ON a.id_uf = tu.id_uf
        LEFT JOIN "Setores".funcionarios f ON a.atendente_comercial = f.id
        LEFT JOIN "public".type_estado_civil tec ON c.id_estado_civil = tec.id_estado_civil
        LEFT JOIN "public".type_genero tg ON c.id_genero = tg.id_genero
        WHERE ac.motivo_encerramento = 11
        """,
        "description": "Perfil de clientes do banco NG (motivo encerramento = 11)",
        "params": []
    },
    # v1: queries.py:1100, "facebook_ads" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "facebook_ads": {
        "database": "ng",
        "query": """
        SELECT *
        FROM metrics_ads.facebook_ads
        """,
        "description": "Métricas do Facebook Ads do banco NG",
        "params": []
    },
    # v1: queries.py:1279, "Analise_thiago" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "Analise_thiago": {
        "database": "ng",
        "query": """
        SELECT
            a."date" AS "ENTRADA",
            a.customer AS "ID_CUSTOMER",
            c.nome AS "CLIENTE",
            a.id AS "ID_ACTION",
            f.nome AS "ATENDENTE",
            t.nome_campanha AS "CAMPANHA",
            t.canal_aquisicao,
            t.posicionamento AS "POSICIONAMENTO",
            t.nome_conjunto AS "NOME_CONJUNTO",
            t.criativo AS "CRIATIVO",
            ac.status_id,
            ac.motivo_encerramento,
            tu.uf AS "UF",
            GREATEST(ac.fechado_em, ac.data_upsell) AS "ASSINATURA",
            jp.id AS "ID_PROCESSO",
            jr."RUBRICA",
            jr."valor_AM" AS "VALOR_AM",
            jpa."EMPRESA",
            jp."FASE",
            jp."MOTIVO_CANCELAMENTO",
            jp."REAJUIZAMENTO",
            jp.status AS "STATUS",
            jpp."STATUS" AS "STATUS_PROTOCOLO",
            jpp."VALOR_DA_CAUSA",
            jpp."DANO_MORAL",
            jpp."SAIDA" AS "SAIDA_PROTOCO"
        FROM "public".actions a
        LEFT JOIN "public".action_status ac ON a.id_status = ac.id
        LEFT JOIN "public".type_status ts ON ac.status_id = ts.id
        LEFT JOIN "public".customers c ON a.customer = c.id
        LEFT JOIN "public".trackeamento t ON a.id_tracking = t.id
        LEFT JOIN "public".type_uf tu ON a.id_uf = tu.id_uf
        LEFT JOIN "Setores".funcionarios f ON a.atendente_comercial = f.id
        LEFT JOIN juridico.processos jp ON a.id = jp."ID_ACTION"
        LEFT JOIN juridico.rubricas jr ON jp."ID_RUBRICA" = jr.id
        LEFT JOIN juridico.partes_adversas jpa ON jp."ID_PARTE_ADVERSA" = jpa.id
        LEFT JOIN protocolo.protocolo jpp ON jp.id = jpp."ID_PROCESSO"
        """,
        "description": "Análise Thiago do banco NG",
        "params": []
    },
    # v1: queries.py:485, "trackeamento_NG_2" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "trackeamento_NG_2": {
        "database": "ng",
        "query": """
        SELECT
            t.id AS "ID_TRACK",
            t."date" AS "DATA_TRACKEAMENTO",
            tu.uf AS "UF",
            t.nome_campanha AS "NOME_CAMPANHA",
            t.nome_conjunto AS "NOME_CONJUNTO",
            t.criativo AS "CRIATIVO",
            t.posicionamento AS "POSICIONAMENTO",
            t.canal_aquisicao AS "CANAL_AQUISICAO",
            t.tipo_trafego AS "TIPO_TRAFEGO",
            t.prospeccao AS "PROSPECCAO",
            a.atendente_comercial AS "ATENDENTE",
            GREATEST(ac.fechado_em, ac.data_upsell) AS "ASSINADO_EM",
            ac.motivo_encerramento AS "MOTIVO_ENCERRAMENTO"
        FROM "public".trackeamento t
        LEFT JOIN "public".actions a ON t.id = a.id_tracking
        LEFT JOIN "public".action_status ac ON a.id_status = ac.id
        LEFT JOIN "public".type_uf tu ON a.id_uf = tu.id_uf
        """,
        "description": "Trackeamento do banco NG",
        "params": []
    },
    # v1: queries.py:4049, "nps_NG" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG, nps_NG.
    "nps_NG": {
        "database": "ng",
        "query": """
        SELECT
            r.id                    AS "ID",
            r.cliente               AS "CLIENTE",
            r.telefone              AS "TELEFONE",
            r.data                  AS "DATA",
            r.av_tempo_resposta     AS "AV_TEMPO_RESPOSTA",
            r.av_nivel_info         AS "AV_NIVEL_INFO",
            r.av_prob_ind           AS "AV_PROB_IND",
            r.av_confiança          AS "AV_CONFIANCA",
            r.feedback_positivo     AS "FEEDBACK_POSITIVO",
            r.feedback_melhoria     AS "FEEDBACK_MELHORIA",
            r.etapa_preocupação     AS "ETAPA_PREOCUPACAO",
            r.comentario            AS "COMENTARIO"
        FROM relatorios.nps_escritorio r
        ORDER BY r.data DESC NULLS LAST
        """,
        "description": "Respostas de NPS (Net Promoter Score) do banco NG — tabela relatorios.nps_escritorio.",
        "params": []
    },
}
