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
        "params": [],
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
        "params": [],
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
        "params": [],
    },
    # v1: queries.py:1220, "perfil_clientes_lexpre" (copiada em 25/11/2026). Marketing (LexPre).
    "perfil_clientes_lexpre": {
        "database": "lexpre",
        "query": """
        select
            c.escritorio_id,
            e.razao_social as "ESCRITORIO",
            a.data_entrada as "ENTRADA",
            a.id as "ATENDIMENTO",
            c.nome as "CLIENTE",
            c.nascimento as "NASCIMENTO",
            c.estado_civil as "ESTADO_CIVIL",
            c.genero as "GENERO",
            c.bairro as "BAIRRO",
            c.uf as "UF",
            f.nome as "FUNCIONARIO",
            a.nome_campanha as "CAMPANHA",
            a.plataforma as "PLATAFORMA",
            a.canal_aquisicao as "CANAL_AQUISICAO",
            a.tipo_trafego as "TIPO_TRAFEGO",
            a.prospeccao as "PROSPECCAO",
            a.motivo_id,
            a.status_id,
            a.data_assinatura as "DATA_ASSINATURA",
            -- Campos extraídos do JSONB ps.respostas
                ps.respostas ->> 'RESIDENCIA' as "PS_RESIDENCIA",
                ps.respostas ->> 'ocupação' as "PS_OCUPACAO",
                ps.respostas ->> 'ESCOLARIDADE' as "PS_ESCOLARIDADE",
                ps.respostas ->> 'primeiro_nome' as "PS_PRIMEIRO_NOME",
                ps.respostas ->> 'UNICO PROVEDOR?' as "PS_UNICO_PROVEDOR",
                ps.respostas ->> 'MEDIA GANHO MENSAL' as "PS_MEDIA_GANHO_MENSAL",
                ps.respostas ->> 'carteira assinada?' as "PS_CARTEIRA_ASSINADA",
                ps.respostas ->> 'total de dependentes' as "PS_TOTAL_DEPENDENTES"

            from public.atendimento a
            left join public.customer c on a.customer_id = c.id
            left join public.escritorio e on a.escritorio_id = e.id
            left join public.funcionario f on a.funcionario_id = f.id
            left join public.pesquisa_socioeconomica ps on a.id = ps.atendimento_id

            where a.status_id = 6
              and a.data_assinatura is not null
        """,
        # Assinado = status_id 6 + data_assinatura (29/09/2026), mesma regra de
        # comercial_lexpre._is_assinado. Antes era motivo_id = 4, que só é preenchido
        # quando o atendimento é encerrado depois — deixava ~92% dos assinados de fora.
        "description": "Perfil de clientes lexPre (assinados: status_id = 6)",
        "params": [],
    },
    # v1: queries.py:839, "audit_log_demandas_canceladas_lexpre_NG" (copiada em 11/11/2026). Comercial e Comissão Comercial (LexPre).
    "audit_log_demandas_canceladas_lexpre_NG": {
        "database": "lexpre",
        "query": """
        SELECT
            al.entidade_id AS "ID_DEMANDA",
            al.created_at AS "DATA_CANCELAMENTO",
            al.escritorio_id AS "ESCRITORIO_ID",
            me.descricao AS "MOTIVO_CANCELAMENTO"
        FROM public.audit_log al
        LEFT JOIN public.demandas d
            ON d.id = al.entidade_id
        LEFT JOIN public.motivo_encerramento me
            ON me.id = d.motivo_cancelamento_id
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
        # MOTIVO_CANCELAMENTO é a descrição do catálogo (motivo_encerramento) apontado por
        # demandas.motivo_cancelamento_id — o motivo gravado na demanda cancelada.
        "description": "Eventos de cancelamento de demanda (banco lexpre), usados para desconto de comissão por cancelamento tardio.",
        "params": [],
    },
    # v1: queries.py:1326, "execucao_LA" (copiada em 17/11/2026). Execução, Acordos e Recursal (LexFlow).
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
            p.valor_causa_vs as "VALOR_SENTENCA",
            p.valor_causa_va as "VALOR_ACORDAO",
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
            p.datas_execucao_extras as "DATAS_EXECUCAO_EXTRAS",
            p.valores_financeiros_extras as "VALORES_FINANCEIROS_EXTRAS",
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
    # v1: queries.py:1456, "execucao_RJ" (copiada em 17/11/2026). Execução, Acordos e Recursal (LexFlow).
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
            p.valor_causa_vs as "VALOR_SENTENCA",
            p.valor_causa_va as "VALOR_ACORDAO",
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
            p.datas_execucao_extras as "DATAS_EXECUCAO_EXTRAS",
            p.valores_financeiros_extras as "VALORES_FINANCEIROS_EXTRAS",
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
    },
    # v1: queries.py:235, "setor_protocolo_LA" (copiada em 16/11/2026). comercial-lexpre (meta anual e meta por atendente: protocolado no legado LA).
    "setor_protocolo_LA": {
        "database": "laadv",
        "query": """
        SELECT
            pro.id,
            pro."NOME",
            pro."ENTRADA",
            pro."PROCESSO_ID",
            atendente.nome AS "ATENDENTE",
            pro."MATERIA",
            pro."PARTE_ADVERSA",
            pro."VALOR_CAUSA",
            pro."SISTEMA",
            pro."UF",
            pro."STATUS",
            pro."SAIDA",
            pro."ACTION_ID",
            pro."FUNCIONARIO_ID",
            responsavel.nome AS "FUNCIONARIO",
            pro."REAJUIZAMENTO",
            COALESCE(pro."DANO_MORAL", pet."DANO_MORAL") AS "DANO_MORAL",
            COALESCE(pro."DANO_MATERIAL", pet."DANO_MATERIAL") AS "DANO_MATERIAL",
            pro."DATA_CONTRATACAO",
            r.area_atuacao_id AS "AREA_ATUACAO_ID",
            aa.nome_area AS "AREA_ATUACAO"

        FROM protocolo.protocolo pro
        LEFT JOIN "public".actions a ON pro."ACTION_ID" = a.id_action
        LEFT JOIN "Setores".funcionarios atendente ON a.atendente_comercial = atendente.id
        LEFT JOIN "Setores".funcionarios responsavel ON pro."FUNCIONARIO_ID" = responsavel.id
        LEFT JOIN juridico.processos jp ON pro."PROCESSO_ID" = jp.id
        LEFT JOIN juridico.rubricas r ON jp.rubrica_id = r.id
        LEFT JOIN juridico.area_atuacao aa ON r.area_atuacao_id = aa.id
        LEFT JOIN peticionamento.peticionamento pet ON pro."PROCESSO_ID" = pet."PROCESSO_ID"
        """,
        "description": "Protocolo do banco LAADV",
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
    },
    # v1: queries.py:1100, "facebook_ads" (copiada em 12/11/2026). protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG.
    "facebook_ads": {
        "database": "ng",
        "query": """
        SELECT *
        FROM metrics_ads.facebook_ads
        """,
        "description": "Métricas do Facebook Ads do banco NG",
        "params": [],
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
        "params": [],
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
        "params": [],
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
        "params": [],
    },
    # v1: queries.py:20, "comercial_geral_LA" (copiada em 16/11/2026). protocolo_LA.
    "comercial_geral_LA": {
        "database": "laadv",
        "query": """
        SELECT
            a.id_action AS "ID_ACTION",
            a."date" AS "ENTRADA",
            c.id AS "ID_CUSTOMER",
            c.nome AS "CLIENTE",
            c.telefone1 AS "WHATSAPP",
            f.nome AS "ATENDENTE",
            GREATEST(s.fechado_em, s.data_upsell) AS "ASSINADO_EM",
            ts.status AS "STATUS",
            s.status_id,
            s.motivo_encerramento,
            tse.nome AS "MOTIVO_ENCERRAMENTO_NOME",
            tu.uf AS "UF",
            t.nome_campanha AS "CAMPANHA",
            t.canal_aquisicao AS "CANAL_AQUISICAO",
            p.id AS "ID_PROCESSO",
            p.rubrica_id AS "ID_RUBRICA",
            p.reajuizamento AS "REAJUIZAMENTO",
            rub."RUBRICA",
            rub."AREA_ATUACAO",
            rub."VALOR",
            rub."AREA_ATUACAO_ID",
            jpa."EMPRESA",
            tsp.status AS "STATUS_PROCESSO",
            f.ativo AS "ATIVO"
        FROM "public".actions a
        LEFT JOIN "public".customers c ON a.customer_id = c.id
        LEFT JOIN "Setores".funcionarios f ON a.atendente_comercial = f.id
        LEFT JOIN "public".actions_status s ON a.action_status_id = s.id
        LEFT JOIN "public".type_uf_end tu ON a.uf_id = tu.id_uf_end
        LEFT JOIN "public".type_status ts ON s.status_id = ts.id
        LEFT JOIN "public".type_status_encerramento tse ON s.motivo_encerramento = tse.id
        LEFT JOIN "public".trackeamento t ON a.trackeamento_id = t.id
        LEFT JOIN juridico.processos p ON a.id_action = p.action_id
        LEFT JOIN juridico.partes_adversas jpa ON p.parte_adversa_id = jpa.id
        LEFT JOIN juridico.type_status_processo tsp ON p.status = tsp.id
        JOIN LATERAL (
            -- Se for rubrica reunida (184 ou 209), busca as rubricas reais
            SELECT r2."RUBRICA", aa2.nome_area AS "AREA_ATUACAO", r2.valor AS "VALOR", r2.area_atuacao_id AS "AREA_ATUACAO_ID"
            FROM juridico.processo_rubricas_reunidas prr
            JOIN juridico.rubricas r2
                ON r2.id = prr.rubrica_id
            LEFT JOIN juridico.area_atuacao aa2
                ON r2.area_atuacao_id = aa2.id
            WHERE p.rubrica_id IN (184, 209)
              AND prr.processo_id = p.id
            UNION ALL
            -- Se não for reunida, busca a rubrica direta + área
            SELECT r1."RUBRICA", aa1.nome_area AS "AREA_ATUACAO", r1.valor AS "VALOR", r1.area_atuacao_id AS "AREA_ATUACAO_ID"
            FROM juridico.rubricas r1
            LEFT JOIN juridico.area_atuacao aa1
                ON r1.area_atuacao_id = aa1.id
            WHERE p.rubrica_id NOT IN (184, 209)
              AND r1.id = p.rubrica_id
        ) rub ON TRUE
        ORDER BY a.id_action DESC
        """,
        "description": "Dados comerciais gerais do banco LAADV",
        "params": [],
    },
    # v1: queries.py:177, "setor_confeccao_LA" (copiada em 16/11/2026). protocolo_LA, peticionamento_LA.
    "setor_confeccao_LA": {
        "database": "laadv",
        "query": """
        WITH cte_log_fase AS (
            SELECT
                processo_id,
                
                -- PETICIONAMENTO
                MAX(CASE WHEN subfase_id = 5 AND acao = 1 THEN data END) AS dt_entrada_pet,
                MAX(CASE WHEN subfase_id = 5 AND acao = 2 THEN data END) AS dt_saida_pet,
                
                -- PROTOCOLO
                MAX(CASE WHEN subfase_id = 6 AND acao = 1 THEN data END) AS dt_entrada_protocolo,
                MAX(CASE WHEN subfase_id = 6 AND acao = 2 THEN data END) AS dt_saida_protocolo
                
                FROM juridico.log_fase
                GROUP BY processo_id
        )
        SELECT
            pp.id,
            pp."NOME",
            pp."PROCESSO_ID",
            atendente.nome AS "ATENDENTE",
            pp."ENTRADA",
            pp."ACTION_ID",
            pp."UF",
            pp."STATUS",
            pp."SAIDA",
            pp."MATERIA",
            pp."PARTE_ADVERSA",
            pp."VALOR_CAUSA",
            pp."SISTEMA",
            pp."FUNCIONARIO_ID",
            responsavel.nome AS "FUNCIONARIO",
            pp."PET_AUTO",
            pp."REAJUIZAMENTO",
            pp."DANO_MORAL",
            pp."DANO_MATERIAL",
            lf.dt_entrada_pet AS "DATA_ENTRADA_PET",
            lf.dt_saida_pet AS "DATA_SAIDA_PET",
            lf.dt_entrada_protocolo AS "DATA_ENTRADA_PROTOCOLO",
            lf.dt_saida_protocolo AS "DATA_SAIDA_PROTOCOLO",
            r.area_atuacao_id AS "AREA_ATUACAO_ID",
            aa.nome_area AS "AREA_ATUACAO"

        FROM peticionamento.peticionamento pp
        LEFT JOIN "public".actions a ON pp."ACTION_ID" = a.id_action
        LEFT JOIN "Setores".funcionarios atendente ON a.atendente_comercial = atendente.id
        LEFT JOIN "Setores".funcionarios responsavel ON pp."FUNCIONARIO_ID" = responsavel.id
        LEFT JOIN cte_log_fase lf ON pp."PROCESSO_ID" = lf.processo_id
        LEFT JOIN juridico.processos jp ON pp."PROCESSO_ID" = jp.id
        LEFT JOIN juridico.rubricas r ON jp.rubrica_id = r.id
        LEFT JOIN juridico.area_atuacao aa ON r.area_atuacao_id = aa.id
        """,
        "description": "Confecção de petições do banco LAADV",
        "params": [],
    },
    # v1: queries.py:142, "setor_org_documentos_LA" (copiada em 16/11/2026). protocolo_LA, peticionamento_LA, org_doc_LA.
    "setor_org_documentos_LA": {
        "database": "laadv",
        "query": """
        SELECT
            od.id,
            od."NOME",
            od."ENTRADA",
            od."UF",
            od."STATUS",
            od."SETOR_ORIGEM",
            od."ATENDENTE_COMERCIAL",
            od."ACTION_ID",
            od."SAIDA",
            od."PROCESSO_ID",
            od."MATERIA",
            od."DATA_CONTRATACAO",
            od."FUNCIONARIO_ID",
            f.nome AS "FUNCIONARIO",
            p."VALOR_CAUSA",
            p."REAJUIZAMENTO",
            p."DANO_MORAL",
            p."PET_AUTO",
            r.area_atuacao_id AS "AREA_ATUACAO_ID",
            aa.nome_area AS "AREA_ATUACAO"
        FROM organizacao_doc.organizacao_documentos od
        LEFT JOIN "Setores".funcionarios f ON od."FUNCIONARIO_ID" = f.id
        LEFT JOIN peticionamento.peticionamento p ON od."PROCESSO_ID" = p."PROCESSO_ID"
        LEFT JOIN juridico.processos jp ON od."PROCESSO_ID" = jp.id
        LEFT JOIN juridico.rubricas r ON jp.rubrica_id = r.id
        LEFT JOIN juridico.area_atuacao aa ON r.area_atuacao_id = aa.id
        """,
        "description": "Organização de documentos do banco LAADV",
        "params": [],
    },
    # v1: queries.py:110, "setor_pendencia_LA" (copiada em 16/11/2026). protocolo_LA, peticionamento_LA, org_doc_LA, pendencia_LA.
    "setor_pendencia_LA": {
        "database": "laadv",
        "query": """
        SELECT
            pp.id,
            pp."NOME",
            pp."ACTION_ID",
            pp."UF",
            pp."ENTRADA",
            pp."STATUS",
            pp."ATENDENTE",
            pp."SAIDA",
            pp."SETOR_ORIGEM",
            pp."PROCESSO_ID",
            p.motivo_cancelamento AS "MOTIVO_CANCELAMENTO",
            pp."TIPO_PENDENCIA",
            f.nome AS "FUNCIONARIO",
            pp."FUNCIONARIO_ID",
            pp."DATA_CONTRATACAO",
            pp."REAJUIZAMENTOS" AS "REAJUIZAMENTO",
        r.area_atuacao_id AS "AREA_ATUACAO_ID",
        aa.nome_area AS "AREA_ATUACAO"
        FROM pendencias_de_processos.pendencias_de_processos pp
        LEFT JOIN "Setores".funcionarios f ON pp."FUNCIONARIO_ID" = f.id
        LEFT JOIN juridico.processos p ON pp."PROCESSO_ID" = p.id
        LEFT JOIN juridico.rubricas r ON p.rubrica_id = r.id
        LEFT JOIN juridico.area_atuacao aa ON r.area_atuacao_id = aa.id
        """,
        "description": "Pendências de processos do banco LAADV",
        "params": [],
    },
    # v1: queries.py:1910, "valor_causa_ajuizado_lexflow_NG" (copiada em 17/11/2026). financeiro-estrategico.
    "valor_causa_ajuizado_lexflow_NG": {
        "database": "lexflow",
        "query": """
        select
            (p.distribuicao at time zone 'UTC')::date as "DATA_AJUIZAMENTO",
            m.description as "MATERIA",
            count(*) as "QUANTIDADE",
            coalesce(sum(
                case when m.description = 'ANP'
                     then coalesce(nullif(p.valor_dano_moral, 0), p.valor_causa)
                     else p.valor_causa
                end
            ), 0) as "VALOR_CAUSA"

        from public.processo p
        left join public.materia m on m.id = p.id_materia

        where p.id_escritorio_assinante = 20
            and coalesce(upper(trim(p.uf)), '') <> 'RJ'

        group by 1, 2
        """,
        "description": (
            "Valor de causa ajuizado do NG (escritório 20, sem RJ) agregado por dia de "
            "distribuição e matéria — fonte única do Valor Protocolado/Ajuizado do Financeiro "
            "Estratégico NG. Matéria ANP usa dano moral (fallback valor da causa quando "
            "vazio/0), mesma regra do banco ng e do LexPre. A data é a data UTC de "
            "`distribuicao` (gravada ora 00:00 UTC, ora 00:00 Manaus); sem distribuição "
            "vem com DATA_AJUIZAMENTO nula."
        ),
        "params": []
    },
}


# v1: queries.py:4641 — Financeiro Estratégico LA: mesma consulta do NG, escritório 21 (LAADV AM).
QUERIES["valor_causa_ajuizado_lexflow_LA"] = {
    **QUERIES["valor_causa_ajuizado_lexflow_NG"],
    "query": QUERIES["valor_causa_ajuizado_lexflow_NG"]["query"].replace(
        "p.id_escritorio_assinante = 20", "p.id_escritorio_assinante = 21"
    ),
    "description": (
        "Valor de causa ajuizado do LAAM (escritório 21, sem RJ) por dia de distribuição e "
        "matéria — Valor Protocolado/Ajuizado do Financeiro Estratégico LA. Mesmas regras da "
        "valor_causa_ajuizado_lexflow_NG (ANP = dano moral)."
    ),
}
assert "id_escritorio_assinante = 21" in QUERIES["valor_causa_ajuizado_lexflow_LA"]["query"]


# v1: queries.py:4123, "julgados" (copiada em 17/11/2026). julgados_acordaos_NG, julgados_acordaos_LA, julgados_acordaos_RJ.
QUERIES["julgados"] = {
    "database": "lexflow",
    "query": """
        -- Mérito vigente ANTES dos embargos (o LexFlow atualiza o mérito na mesma edição em que
        -- lança o resultado do embargo): último valor no processo_audit antes do lançamento do
        -- resultado atual; sem histórico, o mérito atual. Só processos com resultado lançado.
        WITH
        pre_emb1 AS (
            SELECT p.id,
                COALESCE(
                    (SELECT NULLIF(a.valor_novo, '')::int FROM public.processo_audit a
                      WHERE a.id_processo = p.id AND a.campo = 'id_sentenca_merito_grau1' AND a.alterado_em < emb.t
                      ORDER BY a.alterado_em DESC LIMIT 1),
                    (SELECT NULLIF(a.valor_anterior, '')::int FROM public.processo_audit a
                      WHERE a.id_processo = p.id AND a.campo = 'id_sentenca_merito_grau1' AND a.alterado_em >= emb.t
                      ORDER BY a.alterado_em ASC LIMIT 1),
                    p.id_sentenca_merito_grau1
                ) AS id_pre
            FROM public.processo p
            CROSS JOIN LATERAL (
                SELECT MAX(a.alterado_em) AS t FROM public.processo_audit a
                 WHERE a.id_processo = p.id AND a.campo = 'id_sentenca_embargos_grau1'
                   AND a.valor_novo = p.id_sentenca_embargos_grau1::text
            ) emb
            WHERE p.id_sentenca_embargos_grau1 IS NOT NULL
        ),
        pre_emb2 AS (
            SELECT p.id,
                COALESCE(
                    (SELECT NULLIF(a.valor_novo, '')::int FROM public.processo_audit a
                      WHERE a.id_processo = p.id AND a.campo = 'id_acordao_merito_grau2' AND a.alterado_em < emb.t
                      ORDER BY a.alterado_em DESC LIMIT 1),
                    (SELECT NULLIF(a.valor_anterior, '')::int FROM public.processo_audit a
                      WHERE a.id_processo = p.id AND a.campo = 'id_acordao_merito_grau2' AND a.alterado_em >= emb.t
                      ORDER BY a.alterado_em ASC LIMIT 1),
                    p.id_acordao_merito_grau2
                ) AS id_pre
            FROM public.processo p
            CROSS JOIN LATERAL (
                SELECT MAX(a.alterado_em) AS t FROM public.processo_audit a
                 WHERE a.id_processo = p.id AND a.campo = 'id_acordao_embargos_grau2'
                   AND a.valor_novo = p.id_acordao_embargos_grau2::text
            ) emb
            WHERE p.id_acordao_embargos_grau2 IS NOT NULL
        )
        SELECT
            p.id                                         AS "ID",
            p.id_escritorio_assinante                    AS "ID_ESCRITORIO",
            ea.razao_social                               AS "ESCRITORIO",
            p.numero_processo                             AS "NUMERO_PROCESSO",
            p.id_situacao                                 AS "ID_SITUACAO",
            sit.description                               AS "SITUACAO",
            m.description                                 AS "MATERIA",
            c.nome                                         AS "COMARCA",
            p.uf                                           AS "UF",
            p.id_fase                                      AS "ID_FASE",
            f.description                                  AS "FASE",
            sp.description                                 AS "SUBFASE",
            p.id_status_processual                         AS "ID_SUBFASE",
            p.id_status_grau1                              AS "ID_1G",
            spg.nome                                       AS "STATUS_1G",
            msg1.description                               AS "MOTIVO_STATUS_1G",
            p.juiz_1g                                      AS "JUIZ_1G",
            p.id_status_grau2                              AS "ID_2G",
            ssg.nome                                       AS "STATUS_2G",
            p.id_sentenca_merito_grau1                     AS "ID_SENTENCA_MERITO_1G",
            p.id_acordao_merito_grau2                      AS "ID_ACORDAO_MERITO_2G",
            smpg.nome                                      AS "MERITO_SENTENCA_1G",
            ampg.nome                                      AS "MERITO_ACORDAO_2G",
            sepg.nome                                       AS "STATUS_SENTENCA_EMBARGOS",
            aesg.nome                                       AS "STATUS_ACORDAO_EMBARGOS",
            pre_emb1.id_pre                                 AS "ID_SENTENCA_MERITO_1G_PRE_EMBARGOS",
            pre_emb2.id_pre                                 AS "ID_ACORDAO_MERITO_2G_PRE_EMBARGOS",
            msg2.description                               AS "MOTIVO_STATUS_2G",
            p.relator_2g                                   AS "RELATOR_2G",
            ct.nome                                        AS "CAMARA_TURMA",
            comp.nome                                      AS "COMPETENCIA",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END                                             AS "DATA_AJUIZAMENTO",
            CASE
                WHEN p.sentenca IS NOT NULL
                    AND EXTRACT(YEAR FROM p.sentenca) BETWEEN 1900 AND 2100
                THEN p.sentenca
            END                                             AS "DATA_SENTENCA",
            CASE
                WHEN p.acordao_data IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_data) BETWEEN 1900 AND 2100
                THEN p.acordao_data
            END                                             AS "DATA_ACORDAO",
            CASE
                WHEN p.sentenca_embargos IS NOT NULL
                    AND EXTRACT(YEAR FROM p.sentenca_embargos) BETWEEN 1900 AND 2100
                THEN p.sentenca_embargos
            END                                             AS "SENTENCA_EMBARGOS",
            CASE
                WHEN p.acordao_embargos IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_embargos) BETWEEN 1900 AND 2100
                THEN p.acordao_embargos
            END                                             AS "ACORDAO_EMBARGOS",
            p.valor_causa                                   AS "VALOR_CAUSA_SENTENCA",
            p.valor_causa                                   AS "VALOR_CAUSA_ACORDO",
            -- "Novo Valor da Causa do Valor Acordão" (comentário da coluna): valor fixado no acórdão,
            -- diferente do valor de causa inicial. Só exportado no relatório de Acórdãos.
            p.valor_causa_va                                AS "VALOR_ACORDAO",
            -- Valor fixado na sentença (sem comentário no banco; >0 quase só em mérito com proveito
            -- econômico). Diferente do valor de causa inicial. Só exportado no relatório de Sentenças.
            p.valor_causa_vs                                AS "VALOR_SENTENCA"
        FROM public.processo p
        LEFT JOIN public.materia m ON p.id_materia = m.id
        LEFT JOIN public.fase f ON p.id_fase = f.id
        LEFT JOIN public.status_processual sp ON p.id_status_processual = sp.id
        LEFT JOIN public.status_primeiro_grau spg ON p.id_status_grau1 = spg.id
        LEFT JOIN public.motivo_status_grau msg1 ON p.id_motivo_status_grau1 = msg1.id
        LEFT JOIN public.status_segundo_grau ssg ON p.id_status_grau2 = ssg.id
        LEFT JOIN public.sentenca_merito_primeiro_grau smpg ON p.id_sentenca_merito_grau1 = smpg.id
        LEFT JOIN public.acordao_merito_segundo_grau ampg   ON p.id_acordao_merito_grau2 = ampg.id
        LEFT JOIN public.sentenca_embargos_primeiro_grau sepg ON p.id_sentenca_embargos_grau1 = sepg.id
        LEFT JOIN public.acordao_embargos_segundo_grau aesg   ON p.id_acordao_embargos_grau2 = aesg.id
        LEFT JOIN public.motivo_status_grau msg2 ON p.id_motivo_status_grau2 = msg2.id
        LEFT JOIN public.camara_turma ct ON p.id_camara_turma = ct.id
        LEFT JOIN public.comarca c ON p.id_comarca = c.id
        LEFT JOIN public.competencias comp ON p.id_competencia = comp.id
        LEFT JOIN public.escritorio_assinante ea ON p.id_escritorio_assinante = ea.id
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        LEFT JOIN pre_emb1 ON pre_emb1.id = p.id
        LEFT JOIN pre_emb2 ON pre_emb2.id = p.id
        """,
    "description": (
        "Dashboard Julgados — processos de todos os escritórios, com dados de 1º e 2º grau. "
        "O recorte por escritório é aplicado nas análises (ex.: analyses/NG/julgados_sentenca.py)."
    ),
    "params": []
}


# v1: queries.py:511, "tickets" (copiada em 18/11/2026). Tickets (Log_tickets_discord, banco NG).
QUERIES["tickets"] = {
    "database": "ng",
    "query": """
        SELECT *
        FROM "public"."Log_tickets_discord"
        """,
    "description": "Log de tickets do Discord do banco NG",
    "params": [],
}


# v1: queries.py:3041, "setor_recurso_RJ" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ.
QUERIES["setor_recurso_RJ"] = {
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
            WHERE sa.id_setor = 198
              AND s.id_escritorio_assinante = 27
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

            -- Agendamento aberto no setor RECURSOS (escritório RJ, id 27)
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
            "Processos ATIVO + ARQUIVADO + SUSPENSO (padrão sem filtro: só ATIVO, ver app/situacao_processo.py) com agendamento aberto do setor RECURSOS (RJ); "
            "filtros de fase, data e atividades em recurso_RJ."
        ),
        "params": []
    }


# v1: queries.py:3183, "agendamentos_setor_recursos_RJ" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ.
QUERIES["agendamentos_setor_recursos_RJ"] = {
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
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'RECURSOS - %'
        """,
        "description": (
            "Agendamentos do setor RECURSOS (RJ, escritório 27) via vw_dashboard_agendamentos_detalhados, "
            "com motivo_encaminhamento (join direto em agendamento) para identificar "
            "encaminhamentos como 'RECURSO CANCELADO' (AVR - RETORNO / RETORNO - CR)."
        ),
        "params": []
    }


# v1: queries.py:3223, "atividades_setor_recursos_RJ" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ.
QUERIES["atividades_setor_recursos_RJ"] = {
        "database": "lexflow",
        "query": """
        SELECT
            a.id AS id_atividade,
            a.description AS "ATIVIDADE"
        FROM public.setor_atividade sa
        JOIN public.atividade a ON a.id = sa.id_atividade
        WHERE sa.id_setor = 198
          AND sa.ativo = TRUE
        ORDER BY a.description
        """,
        "description": (
            "Catálogo dinâmico de atividades ativas do setor RECURSOS (RJ); "
            "usado como whitelist e como opções do filtro de atividade."
        ),
        "params": []
    }


# v1: queries.py:2188, "controle_processo_todas_situacoes" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ.
QUERIES["controle_processo_todas_situacoes"] = {
        "database": "lexflow",
        "query": """
        WITH fases_log AS (
            SELECT
                id_processo,

                -- INICIAL (datas inválidas no log viram NULL — evita falha no asyncpg)
                MAX(
                    CASE
                        WHEN id_fase = 25
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_inicial,
                MAX(
                    CASE
                        WHEN id_fase = 25
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_inicial,

                -- RECURSAL
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
                ) AS dt_saida_recursal,

                -- EXECUÇÃO
                MAX(
                    CASE
                        WHEN id_fase = 12
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_execucao,
                MAX(
                    CASE
                        WHEN id_fase = 12
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_execucao,

                -- Histórico de subfase em log_fase_processual (id_status_processual por linha)
                -- INICIAL INDEFERIDA: public.status_processual 189 (somente na fase inicial = 25)
                BOOL_OR(
                    id_fase = 25
                    AND id_status_processual = 189
                ) AS log_teve_subfase_inicial_indeferida,
                -- RECURSO NÃO PROVIDO: public.status_processual 190 (somente na fase recursal = 8)
                BOOL_OR(
                    id_fase = 8
                    AND id_status_processual = 190
                ) AS log_teve_subfase_recursal_nao_provido

            FROM public.log_fase_processual
            GROUP BY id_processo
            )

            SELECT
            p.id,
            p.id_escritorio_assinante                    AS "ID_ESCRITORIO",
            ea.razao_social                              AS "ESCRITORIO",
            p.uf                                         AS "UF",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END                                          AS "DATA_AJUIZAMENTO",
            p.numero_processo                            AS "NUMERO_PROCESSO",
            m.description                                AS "MATERIA",
            aa.description                               AS "AREA_ATUACAO",
            pp.razaosocial                               AS "PARTE_ADVERSA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END                                          AS "DATA_ULTIMA_MOVIMENTACAO",
            p.id_fase                                    AS "ID_FASE",
            f.description                                AS "FASE",
            sp.description                               AS "SUBFASE",
            c.nome                                        AS "COMARCA",
            p.valor_causa                                AS "VALOR_DE_CAUSA",
            o.descricao                                  AS "OPERACAO",
            p.dano_moral_vs                              AS "DANO_MORAL_SENTENCA",
            p.dano_material_vs                           AS "DANO_MATERIAL_SENTENCA",
            p.valor_causa_vs                             AS "VALOR_CAUSA_SENTENCA",
            p.valor_causa_va                             AS "VALOR_CAUSA_ACORDO",
            p.dano_moral_ve                              AS "DANO_MORAL_EXECUCAO",
            p.dano_material_ve                           AS "DANO_MATERIAL_EXECUCAO",
            p.valor_causa_ve                             AS "VALOR_CAUSA_EXECUCAO",
            p.valor_alcada_final                         AS "VALOR_ALCADA_FINAL",
            p.id_status_grau1                            AS "ID_1G",
            spg.nome                                     AS "STATUS_1G",
            p.id_status_grau2                            AS "ID_2G",
            ssg.nome                                     AS "STATUS_2G",
            p.id_sentenca_merito_grau1                   AS "ID_SENTENCA_MERITO_1G",
            p.id_acordao_merito_grau2                    AS "ID_ACORDAO_MERITO_2G",
            p.id_situacao                                AS "ID_SITUACAO",
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
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END                                          AS "DATA_EXECUCAO",
            CASE
                WHEN p.acordao_data IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_data) BETWEEN 1900 AND 2100
                THEN p.acordao_data
            END                                          AS "DATA_ACORDAO",

            -- Logs de entrada/saída por fase
            fl.dt_entrada_inicial                        AS "DT_ENTRADA_INICIAL",
            fl.dt_saida_inicial                          AS "DT_SAIDA_INICIAL",
            fl.dt_entrada_recursal                       AS "DT_ENTRADA_RECURSAL",
            fl.dt_saida_recursal                         AS "DT_SAIDA_RECURSAL",
            fl.dt_entrada_execucao                       AS "DT_ENTRADA_EXECUCAO",
            fl.dt_saida_execucao                         AS "DT_SAIDA_EXECUCAO",

            COALESCE(fl.log_teve_subfase_inicial_indeferida, FALSE)    AS "LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA",
            COALESCE(fl.log_teve_subfase_recursal_nao_provido, FALSE)  AS "LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO",

            EXISTS (
                SELECT 1
                FROM public.processo_etiqueta pe
                JOIN public.etiquetas et ON et.id = pe.id_etiqueta
                WHERE pe.id_processo = p.id
                    AND et.nome ILIKE 'acordo'
            ) AS "TEM_ETIQUETA_ACORDO"

    FROM public.processo p
    LEFT JOIN public.escritorio_assinante ea    ON p.id_escritorio_assinante = ea.id
    LEFT JOIN public.materia m                  ON p.id_materia = m.id
    LEFT JOIN public.area_atuacao aa           ON p.id_area_atuacao = aa.id
    LEFT JOIN public.fase f                     ON p.id_fase = f.id
    LEFT JOIN public.status_processual sp       ON p.id_status_processual = sp.id
    LEFT JOIN public.operacao o                 ON p.id_operacao = o.id
    LEFT JOIN public.status_primeiro_grau spg   ON p.id_status_grau1 = spg.id
    LEFT JOIN public.status_segundo_grau ssg    ON p.id_status_grau2 = ssg.id
    LEFT JOIN public.sentenca_merito_primeiro_grau smpg ON p.id_sentenca_merito_grau1 = smpg.id
    LEFT JOIN public.acordao_merito_segundo_grau ampg   ON p.id_acordao_merito_grau2 = ampg.id
    LEFT JOIN public.adverso_processo ap        ON p.id = ap.id_processo
    LEFT JOIN public.pessoa pp                  ON ap.id_pessoa = pp.id
    LEFT JOIN public.comarca c                  ON p.id_comarca = c.id
    LEFT JOIN fases_log fl                      ON p.id = fl.id_processo

    where p.id_situacao IN (1, 2, 6)
        """,
        "description": (
            "Igual a `controle_processo`, mas inclui também ARQUIVADO (situação 2) — usado "
            "só pelo painel 'Extintos · 2º Grau' do Recursal, que não deve ficar restrito a "
            "ativo/suspenso como o Controle de Processos."
        ),
        "params": []
    }


# v1: queries.py:2003, "controle_processo" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA.
QUERIES["controle_processo"] = {
        "database": "lexflow",
        "query": """
        WITH fases_log AS (
            SELECT
                id_processo,

                -- INICIAL (datas inválidas no log viram NULL — evita falha no asyncpg)
                MAX(
                    CASE
                        WHEN id_fase = 25
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_inicial,
                MAX(
                    CASE
                        WHEN id_fase = 25
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_inicial,

                -- RECURSAL
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
                ) AS dt_saida_recursal,

                -- EXECUÇÃO
                MAX(
                    CASE
                        WHEN id_fase = 12
                            AND tipo_movimentacao = 'entrada'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_entrada_execucao,
                MAX(
                    CASE
                        WHEN id_fase = 12
                            AND tipo_movimentacao = 'saida'
                            AND data IS NOT NULL
                            AND EXTRACT(YEAR FROM data) BETWEEN 1900 AND 2100
                        THEN data
                    END
                ) AS dt_saida_execucao,

                -- Histórico de subfase em log_fase_processual (id_status_processual por linha)
                -- INICIAL INDEFERIDA: public.status_processual 189 (somente na fase inicial = 25)
                BOOL_OR(
                    id_fase = 25
                    AND id_status_processual = 189
                ) AS log_teve_subfase_inicial_indeferida,
                -- RECURSO NÃO PROVIDO: public.status_processual 190 (somente na fase recursal = 8)
                BOOL_OR(
                    id_fase = 8
                    AND id_status_processual = 190
                ) AS log_teve_subfase_recursal_nao_provido

            FROM public.log_fase_processual
            GROUP BY id_processo
            )

            SELECT
            p.id,
            p.id_escritorio_assinante                    AS "ID_ESCRITORIO",
            ea.razao_social                              AS "ESCRITORIO",
            p.uf                                         AS "UF",
            CASE
                WHEN p.distribuicao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.distribuicao) BETWEEN 1900 AND 2100
                THEN p.distribuicao
            END                                          AS "DATA_AJUIZAMENTO",
            p.numero_processo                            AS "NUMERO_PROCESSO",
            m.description                                AS "MATERIA",
            aa.description                               AS "AREA_ATUACAO",
            pp.razaosocial                               AS "PARTE_ADVERSA",
            CASE
                WHEN p.ultima_movimentacao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.ultima_movimentacao) BETWEEN 1900 AND 2100
                THEN p.ultima_movimentacao
            END                                          AS "DATA_ULTIMA_MOVIMENTACAO",
            p.id_fase                                    AS "ID_FASE",
            f.description                                AS "FASE",
            sp.description                               AS "SUBFASE",
            c.nome                                        AS "COMARCA",
            p.valor_causa                                AS "VALOR_DE_CAUSA",
            o.descricao                                  AS "OPERACAO",
            p.dano_moral_vs                              AS "DANO_MORAL_SENTENCA",
            p.dano_material_vs                           AS "DANO_MATERIAL_SENTENCA",
            p.valor_causa_vs                             AS "VALOR_CAUSA_SENTENCA",
            p.valor_causa_va                             AS "VALOR_CAUSA_ACORDO",
            p.dano_moral_ve                              AS "DANO_MORAL_EXECUCAO",
            p.dano_material_ve                           AS "DANO_MATERIAL_EXECUCAO",
            p.valor_causa_ve                             AS "VALOR_CAUSA_EXECUCAO",
            p.valor_alcada_final                         AS "VALOR_ALCADA_FINAL",
            p.id_status_grau1                            AS "ID_1G",
            spg.nome                                     AS "STATUS_1G",
            p.id_status_grau2                            AS "ID_2G",
            ssg.nome                                     AS "STATUS_2G",
            p.id_sentenca_merito_grau1                   AS "ID_SENTENCA_MERITO_1G",
            p.id_acordao_merito_grau2                    AS "ID_ACORDAO_MERITO_2G",
            p.id_situacao                                AS "ID_SITUACAO",
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
                WHEN p.execucao IS NOT NULL
                    AND EXTRACT(YEAR FROM p.execucao) BETWEEN 1900 AND 2100
                THEN p.execucao
            END                                          AS "DATA_EXECUCAO",
            CASE
                WHEN p.acordao_data IS NOT NULL
                    AND EXTRACT(YEAR FROM p.acordao_data) BETWEEN 1900 AND 2100
                THEN p.acordao_data
            END                                          AS "DATA_ACORDAO",

            -- Logs de entrada/saída por fase
            fl.dt_entrada_inicial                        AS "DT_ENTRADA_INICIAL",
            fl.dt_saida_inicial                          AS "DT_SAIDA_INICIAL",
            fl.dt_entrada_recursal                       AS "DT_ENTRADA_RECURSAL",
            fl.dt_saida_recursal                         AS "DT_SAIDA_RECURSAL",
            fl.dt_entrada_execucao                       AS "DT_ENTRADA_EXECUCAO",
            fl.dt_saida_execucao                         AS "DT_SAIDA_EXECUCAO",

            COALESCE(fl.log_teve_subfase_inicial_indeferida, FALSE)    AS "LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA",
            COALESCE(fl.log_teve_subfase_recursal_nao_provido, FALSE)  AS "LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO",

            EXISTS (
                SELECT 1
                FROM public.processo_etiqueta pe
                JOIN public.etiquetas et ON et.id = pe.id_etiqueta
                WHERE pe.id_processo = p.id
                    AND et.nome ILIKE 'acordo'
            ) AS "TEM_ETIQUETA_ACORDO"

    FROM public.processo p
    LEFT JOIN public.escritorio_assinante ea    ON p.id_escritorio_assinante = ea.id
    LEFT JOIN public.materia m                  ON p.id_materia = m.id
    LEFT JOIN public.area_atuacao aa           ON p.id_area_atuacao = aa.id
    LEFT JOIN public.fase f                     ON p.id_fase = f.id
    LEFT JOIN public.status_processual sp       ON p.id_status_processual = sp.id
    LEFT JOIN public.operacao o                 ON p.id_operacao = o.id
    LEFT JOIN public.status_primeiro_grau spg   ON p.id_status_grau1 = spg.id
    LEFT JOIN public.status_segundo_grau ssg    ON p.id_status_grau2 = ssg.id
    LEFT JOIN public.sentenca_merito_primeiro_grau smpg ON p.id_sentenca_merito_grau1 = smpg.id
    LEFT JOIN public.acordao_merito_segundo_grau ampg   ON p.id_acordao_merito_grau2 = ampg.id
    LEFT JOIN public.adverso_processo ap        ON p.id = ap.id_processo
    LEFT JOIN public.pessoa pp                  ON ap.id_pessoa = pp.id
    LEFT JOIN public.comarca c                  ON p.id_comarca = c.id
    LEFT JOIN fases_log fl                      ON p.id = fl.id_processo

    where p.id_situacao IN (1, 6)
        """,
        "description": "Controle de processos do escritorio Luis Albert AM — situação ATIVO (1) e SUSPENSO/SOBRESTADO (6)",
        "params": []
    }


# v1: queries.py:2377, "log_subfase_processual" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA.
QUERIES["log_subfase_processual"] = {
        "database": "lexflow",
        "query": """
        SELECT
            lfp.id_processo                        AS "ID_PROCESSO",
            p.id_escritorio_assinante               AS "ID_ESCRITORIO",
            p.id_situacao                           AS "ID_SITUACAO",
            lfp.id_fase                             AS "ID_FASE",
            f.description                           AS "FASE",
            lfp.id_status_processual                AS "ID_SUBFASE",
            sp.description                          AS "SUBFASE",
            lfp.tipo_movimentacao                   AS "TIPO_MOVIMENTACAO",
            lfp.data                                AS "DATA"
        FROM public.log_fase_processual lfp
        JOIN public.processo p                  ON p.id = lfp.id_processo
        LEFT JOIN public.fase f                 ON lfp.id_fase = f.id
        LEFT JOIN public.status_processual sp   ON lfp.id_status_processual = sp.id
        WHERE p.id_escritorio_assinante IN (20, 21)
          AND p.id_situacao IN (1, 6)
          AND lfp.id_status_processual IS NOT NULL
        ORDER BY lfp.id_processo, lfp.data
        """,
        "description": (
            "Histórico de movimentação de fase/subfase (log_fase_processual) dos escritórios "
            "NG (20) e LA (21) — usado para estimar o tempo médio de permanência por subfase "
            "no dashboard Controle de Processos. Situação ATIVO (1) e SUSPENSO/SOBRESTADO (6)."
        ),
        "params": []
    }


# v1: queries.py:4049, "publicacoes_NG" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["publicacoes_NG"] = {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_processo as "ID_PROCESSO",
            pro.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.nome_fantasia as "ESCRITORIO",
            p.data_disponibilizacao as "DATA_DISPONIBILIZACAO",
            p.nomeclasse as "CLASSE",
            p.nomeorgao as "ORGAO",
            c.nome as "COMARCA",
            p.numero_processo,
            m.description as "MATERIA",
            p.siglatribunal as "TRIBUNAL",
            p."tipoComunicacao" as "COMUNICACAO",
            p."tipoDocumento" as "DOCUMENTO",
            p.dias as "DIAS",
            p.status as "STATUS",
            ur.nome as "RESPONSAVEL",
            ul.nome as "LEITOR",
            p.data_leitura_publicacao as "DATA_LEITURA",
            p.data_conclusao as "DATA_CONCLUSAO"

        from public.publicacoes p
        left join public.processo pro on p.id_processo = pro.id
        left join public.situacao sit on sit.id = pro.id_situacao
        left join public.materia m on pro.id_materia = m.id
        left join public.comarca c on pro.id_comarca = c.id
        left join public.usuario ul on p.id_usuario_leitor = ul.id
        left join public.usuario ur on p.id_usuario_responsavel = ur.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id

        where p.id_escritorio_assinante = 20
        """,
        "description": "Publicações do LexFlow do escritorio NG",
        "params": []
    }


# v1: queries.py:4089, "agendamentos_todos_setores_NG" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["agendamentos_todos_setores_NG"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM 1 FOR POSITION(' - ' IN v.setor_atividade_nome) - 1)
                ELSE v.setor_atividade_nome
            END                                             AS "SETOR",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 20
          AND v.processo_id IS NOT NULL
        """,
        "description": "Todos os agendamentos (qualquer setor) do escritório NG, para vincular a publicações via processo_id.",
        "params": []
    }


# v1: queries.py:355, "publicacoes_LA" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["publicacoes_LA"] = {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_processo as "ID_PROCESSO",
            pro.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.nome_fantasia as "ESCRITORIO",
            p.data_disponibilizacao as "DATA_DISPONIBILIZACAO",
            --p.meiocompleto,
            p.nomeclasse as "CLASSE",
            p.nomeorgao as "ORGAO",
            c.nome as "COMARCA",
            p.numero_processo,
            m.description as "MATERIA",
            p.siglatribunal as "TRIBUNAL",
            p."tipoComunicacao" as "COMUNICACAO",
            p."tipoDocumento" as "DOCUMENTO",
            p.dias as "DIAS",
            p.status as "STATUS",
            --p.id_usuario_responsavel,
            ur.nome as "RESPONSAVEL",
            --p.id_usuario_leitor,
            ul.nome as "LEITOR",
            p.data_leitura_publicacao as "DATA_LEITURA",
            p.data_conclusao as "DATA_CONCLUSAO"

        from public.publicacoes p
        left join public.processo pro on p.id_processo = pro.id
        left join public.situacao sit on sit.id = pro.id_situacao
        left join public.materia m on pro.id_materia = m.id
        left join public.comarca c on pro.id_comarca = c.id
        left join public.usuario ul on p.id_usuario_leitor = ul.id
        left join public.usuario ur on p.id_usuario_responsavel = ur.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id

        where p.id_escritorio_assinante = 21
        """,
        "description": "Publicações do LexFlow do escritorio LAADV AM",
        "params": []
    }


# v1: queries.py:3987, "agendamentos_todos_setores_LA" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["agendamentos_todos_setores_LA"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM 1 FOR POSITION(' - ' IN v.setor_atividade_nome) - 1)
                ELSE v.setor_atividade_nome
            END                                             AS "SETOR",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND v.processo_id IS NOT NULL
        """,
        "description": "Todos os agendamentos (qualquer setor) do escritório LAADV AM, para vincular a publicações via processo_id.",
        "params": []
    }


# v1: queries.py:398, "publicacoes_LA_RJ" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["publicacoes_LA_RJ"] = {
        "database": "lexflow",
        "query": """
        select
            p.id,
            p.id_processo as "ID_PROCESSO",
            pro.id_situacao as "ID_SITUACAO",
            sit.description as "SITUACAO",
            ea.nome_fantasia as "ESCRITORIO",
            p.data_disponibilizacao as "DATA_DISPONIBILIZACAO",
            --p.meiocompleto,
            p.nomeclasse as "CLASSE",
            p.nomeorgao as "ORGAO",
            c.nome as "COMARCA",
            p.numero_processo,
            m.description as "MATERIA",
            p.siglatribunal as "TRIBUNAL",
            p."tipoComunicacao" as "COMUNICACAO",
            p."tipoDocumento" as "DOCUMENTO",
            p.dias as "DIAS",
            p.status as "STATUS",
            --p.id_usuario_responsavel,
            ur.nome as "RESPONSAVEL",
            --p.id_usuario_leitor,
            ul.nome as "LEITOR",
            p.data_leitura_publicacao as "DATA_LEITURA",
            p.data_conclusao as "DATA_CONCLUSAO"

        from public.publicacoes p
        left join public.processo pro on p.id_processo = pro.id
        left join public.situacao sit on sit.id = pro.id_situacao
        left join public.materia m on pro.id_materia = m.id
        left join public.comarca c on pro.id_comarca = c.id
        left join public.usuario ul on p.id_usuario_leitor = ul.id
        left join public.usuario ur on p.id_usuario_responsavel = ur.id
        left join public.escritorio_assinante ea on p.id_escritorio_assinante = ea.id

        where p.id_escritorio_assinante = 27
        """,
        "description": "Publicações do LexFlow do escritorio LAADV RJ",
        "params": []
    }


# v1: queries.py:4018, "agendamentos_todos_setores_LA_RJ" (copiada em 18/11/2026). execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
QUERIES["agendamentos_todos_setores_LA_RJ"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            CASE
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM 1 FOR POSITION(' - ' IN v.setor_atividade_nome) - 1)
                ELSE v.setor_atividade_nome
            END                                             AS "SETOR",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 27
          AND v.processo_id IS NOT NULL
        """,
        "description": "Todos os agendamentos (qualquer setor) do escritório LAADV RJ, para vincular a publicações via processo_id.",
        "params": []
    }


# v1: queries.py:4431, "tcc_sobrevivencia_processual" (copiada em 18/11/2026). Sobrevivência Processual (TCC).
QUERIES["tcc_sobrevivencia_processual"] = {
    "database": "lexflow",
    # Cópia da coorte do TCC (`TCC - Luiz/coorte_sobrevivencia_2_estagios.sql`), só com
    # as colunas que o dashboard usa. Mudou a definição da coorte lá? Replicar aqui.
    "query": """
    with base as (
      select
        p.id,
        p.numero_processo,
        p.id_escritorio_assinante,   -- 20=NG, 21=LA (AM), 27=RJ
        -- Marco zero (t=0) da sobrevivencia e a DISTRIBUICAO do processo (data real
        -- de inicio da tramitacao judicial), nao a contratacao (relacao com o
        -- escritorio, que pode ser bem antes ou depois da distribuicao - mediana
        -- da diferenca = 0 dias, mas com cauda grande pros dois lados). Trocado
        -- em 03/11/2026: distribuicao tambem cobre mais processos (88k vs 70k
        -- com contratacao preenchida, no universo sem segredo de justica).
        case when (p.distribuicao at time zone 'America/Manaus')::date
               between '1971-01-01' and current_date + 730
             then (p.distribuicao at time zone 'America/Manaus')::date end as distribuicao_d,
        case when (p.sentenca at time zone 'America/Manaus')::date
               between '1971-01-01' and current_date + 730
             then (p.sentenca at time zone 'America/Manaus')::date end as sentenca_d,
        case when p.acordao_data between '1971-01-01' and current_date + 730
             then p.acordao_data end as acordao_d,
        case when (p.acordo_fechado at time zone 'America/Manaus')::date
               between '1971-01-01' and current_date + 730
             then (p.acordo_fechado at time zone 'America/Manaus')::date end as acordo_d,
        case when (p.ultima_movimentacao at time zone 'America/Manaus')::date
               between '1971-01-01' and current_date + 730
             then (p.ultima_movimentacao at time zone 'America/Manaus')::date end as ultima_mov_d,
        case when p.data_compensacao_alvara between '1971-01-01' and current_date + 730
             then p.data_compensacao_alvara end as compensacao_alvara_d,
        case when p.data_compensacao_alvara_incontroverso between '1971-01-01' and current_date + 730
             then p.data_compensacao_alvara_incontroverso end as compensacao_incontroverso_d,
        case when (p.pagamento_acordo at time zone 'America/Manaus')::date
               between '1971-01-01' and current_date + 730
             then (p.pagamento_acordo at time zone 'America/Manaus')::date end as pagamento_acordo_d,
        p.id_sentenca_merito_grau1,
        p.id_acordao_merito_grau2,
        p.id_tipo_acao, ta.description as tipo_acao,
        p.id_materia, m.description as materia,
        p.valor_causa,
        p.id_comarca,
        co.nome as comarca,
        p.uf,
        p.juiz_1g,       -- texto livre e a fonte real nos dashboards do projeto, nao a FK juiz_primeiro_grau
        p.relator_2g,    -- idem juiz_1g: texto livre, so preenchido quando ha acordao (2G)
        c.nome as competencia,
        f.description as fase,
        sp.description as subfase    -- public.status_processual - e isso que o resto do sistema chama de "subfase"
      from processo p
      left join tipo_acao ta on ta.id = p.id_tipo_acao
      left join materia m on m.id = p.id_materia
      left join comarca co on co.id = p.id_comarca
      left join competencias c on c.id = p.id_competencia
      left join fase f on f.id = p.id_fase
      left join status_processual sp on sp.id = p.id_status_processual
      where p.distribuicao is not null
        and coalesce(p.segredo_justica, false) = false
        -- 09/11/2026: so NG (20) e LA/AM (21), igual a coorte do TCC - RJ (27) saiu
        -- do estudo e do dashboard; id 3 e escritorio de teste.
        and p.id_escritorio_assinante in (20, 21)
        -- 06/11/2026 (igual a coorte do TCC): agravo fora da coorte (processo proprio no LexFlow,
        -- nao e acao). Agravo = CNJ com 20 digitos e origem (4 ultimos) 0000/9000/9001/9002.
        and not (
          length(regexp_replace(coalesce(p.numero_processo, ''), '[^0-9]', '', 'g')) = 20
          and right(regexp_replace(coalesce(p.numero_processo, ''), '[^0-9]', '', 'g'), 4)
              in ('0000', '9000', '9001', '9002')
        )
    ),
    base_valida as (
      select * from base
      where distribuicao_d is not null   -- descarta quem tem distribuicao corrompida (sem ancora t=0)
    ),
    merito as (
      select *,
        case when acordao_d is not null then greatest(sentenca_d, acordao_d) else sentenca_d end as fim_merito_d,
        -- id_acordao_merito_grau2 = 8 ("SENTENCA ANULADA"): 2G anulou e devolveu
        -- pro 1G, que profere NOVA sentenca depois (sobrescrita no mesmo campo
        -- `sentenca`) - o desfecho valido e o da sentenca, nao o do acordao.
        -- Replicado de coorte_sobrevivencia_2_estagios.sql (fix de 20/10/2026).
        case when acordao_d is not null and id_acordao_merito_grau2 = 8 then
               (case when sentenca_d is not null then 'SENTENCA_MERITO_1G' end)
             when acordao_d is not null then 'ACORDAO_MERITO_2G'
             when sentenca_d is not null then 'SENTENCA_MERITO_1G'
             else null end as tipo_merito,
        case
          when acordao_d is not null and id_acordao_merito_grau2 = 8 then
            (case when sentenca_d is not null then (id_sentenca_merito_grau1 in (1, 3)) end)
          when acordao_d is not null then (id_acordao_merito_grau2 in (1, 3))
          when sentenca_d is not null then (id_sentenca_merito_grau1 in (1, 3))
          else null
        end as merito_favoravel_com_proveito
      from base_valida
    ),
    estagio1 as (
      select *,
        case
          when acordo_d is not null and (fim_merito_d is null or acordo_d <= fim_merito_d)
            then 'ACORDO'
          when fim_merito_d is not null and merito_favoravel_com_proveito
            then 'MERITO_FAVORAVEL_COM_PROVEITO'
          when fim_merito_d is not null and not merito_favoravel_com_proveito
            then 'MERITO_SEM_PROVEITO_OU_DESFAVORAVEL'
          else 'CENSURADO'
        end as tipo_evento_e1,
        case
          when acordo_d is not null and (fim_merito_d is null or acordo_d <= fim_merito_d)
            then acordo_d
          when fim_merito_d is not null then fim_merito_d
          else ultima_mov_d
        end as data_evento_e1,
        -- Classificacao do acordo para os cards Pre x Pos-Sentenca, INDEPENDENTE do
        -- evento do Estagio 1 (11/11/2026). Antes so valia quando o acordo era o
        -- primeiro desfecho (antes de fim_merito_d): sem acordao, fim_merito_d = a
        -- propria sentenca, entao todo acordo pos-sentenca sem acordao sumia (NG: 323
        -- de 378 nao contados). Regra atual (decisao do usuario): PRE = antes da
        -- primeira decisao de merito (sentenca; ou o acordao quando nao ha sentenca);
        -- POS = qualquer acordo depois dela, inclusive na execucao (apos o acordao).
        -- Fonte: so a data de acordo fechado (etiquetas nao entram).
        case
          when acordo_d is null then null
          when least(sentenca_d, acordao_d) is null or acordo_d <= least(sentenca_d, acordao_d)
            then 'PRE_SENTENCA'
          else 'POS_SENTENCA'
        end as tipo_acordo,
        -- Estagio 1 quebrado em 2 sub-marcos (mesmo t=0 = distribuicao), pra nao
        -- misturar quem so teve sentenca (1G, sem recurso) com quem foi ate
        -- acordao (2G). A MEDIANA/curva conta QUALQUER sentenca/acordao como
        -- evento (procedente ou nao) - so a TAXA (% favoravel) e restrita a
        -- procedente/parcialmente procedente com proveito economico (campos
        -- sentenca_favoravel/acordao_favoravel abaixo, mesmo criterio do
        -- Estagio 1 geral). ACORDO antes do marco em questao conta como
        -- censura (mesma simplificacao ja documentada nas Fases 3-5 do TCC:
        -- sem riscos competitivos nativos) - nao e um "nao-evento", so nao e
        -- ESSE evento.
        case when sentenca_d is not null then 'SENTENCA' else 'CENSURADO' end as tipo_evento_sentenca,
        case when sentenca_d is not null then (id_sentenca_merito_grau1 in (1, 3)) else false end as sentenca_favoravel,
        -- 11/11/2026: improcedencia e extincao, mesma regra dos Julgados
        -- (matriz_julgamento: improcedente = 5 e 6/prescricao-decadencia; extinto = 7)
        case when sentenca_d is not null then (id_sentenca_merito_grau1 in (5, 6)) else false end as sentenca_improcedente,
        case when sentenca_d is not null then (id_sentenca_merito_grau1 = 7) else false end as sentenca_extinta,
        -- acordao_d entra no fallback pq alguns processos tem acordao registrado
        -- mas nao tem a data da sentenca que o precedeu capturada (so o campo
        -- `sentenca` ficou vazio) - sem isso a censura ficava sem data nenhuma.
        coalesce(sentenca_d, acordo_d, acordao_d, ultima_mov_d) as data_evento_sentenca,
        case when tipo_merito = 'ACORDAO_MERITO_2G' then 'ACORDAO_MERITO' else 'CENSURADO' end as tipo_evento_acordao,
        case when tipo_merito = 'ACORDAO_MERITO_2G' then merito_favoravel_com_proveito else false end as acordao_favoravel,
        case when tipo_merito = 'ACORDAO_MERITO_2G' then (id_acordao_merito_grau2 in (5, 6)) else false end as acordao_improcedente,
        case when tipo_merito = 'ACORDAO_MERITO_2G' then (id_acordao_merito_grau2 = 7) else false end as acordao_extinto,
        -- idem, na outra direcao: sentenca_d entra no fallback pra quem so
        -- chegou ao 1G (sem recurso) e nao tem acordo nem ultima_movimentacao
        -- capturados - a propria sentenca vira a censura (ultimo marco certo).
        case
          when tipo_merito = 'ACORDAO_MERITO_2G' then acordao_d
          when acordo_d is not null then acordo_d
          when sentenca_d is not null then sentenca_d
          else ultima_mov_d
        end as data_evento_acordao
      from merito
    ),
    estagio2 as (
      select *,
        case when tipo_evento_e1 in ('ACORDO', 'MERITO_FAVORAVEL_COM_PROVEITO')
          then least(compensacao_alvara_d, compensacao_incontroverso_d, pagamento_acordo_d)
        end as data_pagamento,
        case
          when tipo_evento_e1 not in ('ACORDO', 'MERITO_FAVORAVEL_COM_PROVEITO') then null
          when least(compensacao_alvara_d, compensacao_incontroverso_d, pagamento_acordo_d) is not null
            then 'PAGO'
          else 'CENSURADO_PAGAMENTO'
        end as tipo_evento_e2
      from estagio1
    )

    select
      id_escritorio_assinante,
      tipo_evento_e1,
      tipo_acordo,
      case when acordo_d is not null and acordo_d >= distribuicao_d
        then (acordo_d - distribuicao_d) end as duracao_dias_acordo,
      (data_evento_e1 - distribuicao_d) as duracao_dias_e1,
      tipo_evento_e2,
      case when tipo_evento_e2 is not null then
        (greatest(coalesce(data_pagamento, ultima_mov_d), data_evento_e1) - data_evento_e1)
      end as duracao_dias_e2,
      tipo_evento_sentenca,
      sentenca_favoravel,
      sentenca_improcedente,
      sentenca_extinta,
      case when (data_evento_sentenca - distribuicao_d) >= 0
        then (data_evento_sentenca - distribuicao_d) end as duracao_dias_sentenca,
      tipo_evento_acordao,
      acordao_favoravel,
      acordao_improcedente,
      acordao_extinto,
      case when (data_evento_acordao - distribuicao_d) >= 0
        then (data_evento_acordao - distribuicao_d) end as duracao_dias_acordao,
      tipo_acao, materia, comarca, competencia,
      fase, subfase, juiz_1g, relator_2g
    from estagio2
    where data_evento_e1 is not null
      and (data_evento_e1 - distribuicao_d) >= 0
    """,
    "description": (
        "Coorte de sobrevivência processual em 2 estágios (contratação -> mérito/acordo -> "
        "pagamento) + 2 sub-marcos do Estágio 1 (contratação -> sentença 1G, contratação -> "
        "acórdão de mérito 2G), 1 linha por processo. Usado pelo dashboard Sobrevivência "
        "Processual (TCC)."
    ),
    "params": []
}


# v1: queries.py:3534, "agendamentos_setor_intermediarias_NG" (copiada em 19/11/2026; V2: + a atividade de Emenda). pendencias_intermediarias_NG, pendencias_intermediarias_LA.
QUERIES["agendamentos_setor_intermediarias_NG"] = {
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
                WHEN v.setor_atividade_nome = 'EMENDA - SOLICITAR DOCS COM CLIENTE' THEN v.setor_atividade_nome
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'PENDÊNCIA'                                     AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 20
          AND (v.setor_atividade_nome LIKE 'PENDÊNCIA - %'
               OR v.setor_atividade_nome = 'EMENDA - SOLICITAR DOCS COM CLIENTE')
        """,
        "description": (
            "Agendamentos do setor PENDÊNCIA (NG) via vw_dashboard_agendamentos_detalhados. V2 (24/11/2026): "
            "mais a atividade 'EMENDA - SOLICITAR DOCS COM CLIENTE' (setor EMENDA), com o nome inteiro para não "
            "se misturar com a 'SOLICITAR DOCS COM CLIENTE' do setor PENDÊNCIA; encerrada como Não Cumprido, "
            "também agenda dilação (a regra da NG é por exclusão: só SANAR PENDÊNCIA 1G não agenda)."
        ),
        "params": []
    }


# v1: queries.py:3933, "agendamentos_dilacao_prazo_intermediarias_NG" (copiada em 19/11/2026). pendencias_intermediarias_NG, pendencias_intermediarias_LA.
QUERIES["agendamentos_dilacao_prazo_intermediarias_NG"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome = 'MANIFESTAÇÃO - ELABORAR DILAÇÃO'
        """,
        "description": (
            "Agendamentos 'MANIFESTAÇÃO - ELABORAR DILAÇÃO' (NG) criados pelo fluxo de "
            "encerramento das Pendências Intermediárias — NG não tem um setor dedicado de "
            "Dilação de Prazo como a LA; SOLICITAR DOCS COM CLIENTE encerrado como "
            "'Encerrado Não Cumprido' com motivo 'CLIENTE NÃO RESPONDEU/ENVIOU DOCS' "
            "encaminha para esta atividade do setor MANIFESTAÇÃO."
        ),
        "params": []
    }


# v1: queries.py:3500, "agendamentos_setor_intermediarias_LA" (copiada em 19/11/2026). pendencias_intermediarias_NG, pendencias_intermediarias_LA.
QUERIES["agendamentos_setor_intermediarias_LA"] = {
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
            'PENDÊNCIAS'                                    AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'PENDÊNCIAS - %'
        """,
        "description": "Agendamentos do setor PENDÊNCIAS (LA) via vw_dashboard_agendamentos_detalhados.",
        "params": []
    }


# v1: queries.py:3909, "agendamentos_dilacao_prazo_intermediarias_LA" (copiada em 19/11/2026). pendencias_intermediarias_NG, pendencias_intermediarias_LA.
QUERIES["agendamentos_dilacao_prazo_intermediarias_LA"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND UPPER(v.setor_atividade_nome) LIKE '%DILAÇÃO DE PRAZO%'
        """,
        "description": "Agendamentos de Dilação de Prazo criados pelo fluxo de encerramento das Pendências Intermediárias (LA).",
        "params": []
    }


# V2 (19/11/2026): Pendências Intermediárias no RJ (escritório 27), que a v1 não tem. As mesmas queries do NG
# (agendamentos_setor_intermediarias_NG e agendamentos_dilacao_prazo_intermediarias_NG), só com o escritório trocado:
# o RJ usa o mesmo setor PENDÊNCIA e a mesma atividade de dilação do NG (app/dashboards/pendencias_intermediarias.py).
QUERIES["agendamentos_setor_intermediarias_RJ"] = {
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
                WHEN v.setor_atividade_nome = 'EMENDA - SOLICITAR DOCS COM CLIENTE' THEN v.setor_atividade_nome
                WHEN POSITION(' - ' IN v.setor_atividade_nome) > 0
                THEN SUBSTRING(v.setor_atividade_nome FROM POSITION(' - ' IN v.setor_atividade_nome) + 3)
                ELSE v.setor_atividade_nome
            END                                             AS "ATIVIDADE",
            'PENDÊNCIA'                                     AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 27
          AND (v.setor_atividade_nome LIKE 'PENDÊNCIA - %'
               OR v.setor_atividade_nome = 'EMENDA - SOLICITAR DOCS COM CLIENTE')
        """,
        "description": (
            "Agendamentos do setor PENDÊNCIA (RJ) via vw_dashboard_agendamentos_detalhados, mais a atividade "
            "'EMENDA - SOLICITAR DOCS COM CLIENTE', como no NG (24/11/2026)."
        ),
        "params": []
    }


QUERIES["agendamentos_dilacao_prazo_intermediarias_RJ"] = {
        "database": "lexflow",
        "query": """
        SELECT
            v.agendamento_id                                AS id,
            CAST(v.processo_id AS INTEGER)                  AS processo_id,
            v.agendamento_status::text                      AS "STATUS",
            v.data_hora_criacao                             AS "DATA_HORA_CRIACAO",
            v.data_hora_conclusao                           AS "DATA_HORA_CONCLUSAO",
            v.nome_usuario_atribuido                        AS "FUNCIONARIO_ATRIBUIDO",
            v.id_usuario_encerramento                       AS "ID_USUARIO_ENCERRAMENTO",
            v.nome_usuario_encerramento                     AS "FUNCIONARIO_ENCERRAMENTO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 27
          -- V2 (decisão de 19/11/2026): no RJ a dilação também é pedida como "MANIFESTAR DILAÇÃO DE PRAZO"
          AND v.setor_atividade_nome IN (
              'MANIFESTAÇÃO - ELABORAR DILAÇÃO',
              'MANIFESTAÇÃO - MANIFESTAR DILAÇÃO DE PRAZO'
          )
        """,
        "description": (
            "Agendamentos 'MANIFESTAÇÃO - ELABORAR DILAÇÃO' (RJ) criados pelo fluxo de "
            "encerramento das Pendências Intermediárias — o RJ, como o NG, não tem um setor dedicado de "
            "Dilação de Prazo como a LA; SOLICITAR DOCS COM CLIENTE encerrado como "
            "'Encerrado Não Cumprido' com motivo 'CLIENTE NÃO RESPONDEU/ENVIOU DOCS' "
            "encaminha para esta atividade do setor MANIFESTAÇÃO."
        ),
        "params": []
    }


# v1: queries.py:3671, "agendamentos_setor_emendas_manifestacoes_NG" (copiada em 19/11/2026). emendas_manifestacoes_NG, emendas_manifestacoes_LA.
QUERIES["agendamentos_setor_emendas_manifestacoes_NG"] = {
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
            'MANIFESTAÇÃO'                                  AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            v.numero_processo                               AS "NUMERO_PROCESSO",
            p.uf                                             AS "UF",
            p.id_situacao                                   AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo p ON p.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'MANIFESTAÇÃO - %'
        """,
        "description": "Agendamentos do setor MANIFESTAÇÃO (NG) via vw_dashboard_agendamentos_detalhados — base do dashboard Emendas e Manifestações (NG).",
        "params": []
    }


# v1: queries.py:3602, "agendamentos_setor_emendas_manifestacoes_LA" (copiada em 19/11/2026). emendas_manifestacoes_NG, emendas_manifestacoes_LA.
QUERIES["agendamentos_setor_emendas_manifestacoes_LA"] = {
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
            'INTERMEDIÁRIAS'                                AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            v.numero_processo                               AS "NUMERO_PROCESSO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'INTERMEDIÁRIAS - %'
        """,
        "description": "Agendamentos do setor INTERMEDIÁRIAS (LA) via vw_dashboard_agendamentos_detalhados — base do dashboard Emendas e Manifestações.",
        "params": []
    }


# V2 (19/11/2026): Emendas e Manifestações no RJ (escritório 27), que a v1 não tem. A mesma query do NG
# (agendamentos_setor_emendas_manifestacoes_NG), só com o escritório trocado: o RJ usa o mesmo setor MANIFESTAÇÃO
# (com UF) do NG (app/dashboards/emendas_manifestacoes.py).
QUERIES["agendamentos_setor_emendas_manifestacoes_RJ"] = {
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
            'MANIFESTAÇÃO'                                  AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            v.numero_processo                               AS "NUMERO_PROCESSO",
            p.uf                                             AS "UF",
            p.id_situacao                                   AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo p ON p.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'MANIFESTAÇÃO - %'
        """,
        "description": "Agendamentos do setor MANIFESTAÇÃO (RJ) via vw_dashboard_agendamentos_detalhados — base do dashboard Emendas e Manifestações (RJ).",
        "params": []
    }


# v1: queries.py:3761, "agendamentos_setor_replicas_NG" (copiada em 19/11/2026). replicas_NG, replicas_LA.
QUERIES["agendamentos_setor_replicas_NG"] = {
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
            'RÉPLICA'                                        AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'RÉPLICA - %'
        """,
        "description": "Agendamentos do setor RÉPLICA (NG) via vw_dashboard_agendamentos_detalhados — base do dashboard Réplicas (NG). No NG o setor é RÉPLICA (singular) e tem 3 atividades: ELABORAR RÉPLICA, RÉPLICA CANCELADA e VERIFICAR CONTESTAÇÃO.",
        "params": []
    }


# v1: queries.py:3795, "processos_status_1g_replicas_NG" (copiada em 19/11/2026). replicas_NG, replicas_LA.
QUERIES["processos_status_1g_replicas_NG"] = {
        "database": "lexflow",
        "query": """
        SELECT DISTINCT
            CAST(v.processo_id AS INTEGER)              AS processo_id,
            p.id_status_grau1                           AS "ID_1G",
            spg.nome                                    AS "STATUS_1G",
            p.id_situacao                                   AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        JOIN public.processo p ON p.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        LEFT JOIN public.status_primeiro_grau spg ON p.id_status_grau1 = spg.id
        WHERE v.id_escritorio_assinante = 20
          AND v.setor_atividade_nome LIKE 'RÉPLICA - %'
        """,
        "description": "Status de 1G (primeiro grau) dos processos do setor RÉPLICA (NG) — base do card de taxa de procedência.",
        "params": []
    }


# v1: queries.py:3707, "agendamentos_setor_replicas_LA" (copiada em 19/11/2026). replicas_NG, replicas_LA.
QUERIES["agendamentos_setor_replicas_LA"] = {
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
            'RÉPLICAS'                                       AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'RÉPLICAS - %'
        """,
        "description": "Agendamentos do setor RÉPLICAS (LA) via vw_dashboard_agendamentos_detalhados — base do dashboard Réplicas.",
        "params": []
    }


# v1: queries.py:3741, "processos_status_1g_replicas_LA" (copiada em 19/11/2026). replicas_NG, replicas_LA.
QUERIES["processos_status_1g_replicas_LA"] = {
        "database": "lexflow",
        "query": """
        SELECT DISTINCT
            CAST(v.processo_id AS INTEGER)              AS processo_id,
            p.id_status_grau1                           AS "ID_1G",
            spg.nome                                    AS "STATUS_1G",
            p.id_situacao                                   AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        JOIN public.processo p ON p.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        LEFT JOIN public.status_primeiro_grau spg ON p.id_status_grau1 = spg.id
        WHERE v.id_escritorio_assinante = 21
          AND v.setor_atividade_nome LIKE 'RÉPLICAS - %'
        """,
        "description": "Status de 1G (primeiro grau) dos processos do setor RÉPLICAS (LA) — base do card de taxa de procedência.",
        "params": []
    }


# V2 (19/11/2026): Réplicas no RJ (escritório 27), que a v1 não tem. As mesmas queries do NG
# (agendamentos_setor_replicas_NG e processos_status_1g_replicas_NG), só com o escritório trocado: o RJ usa o mesmo
# setor RÉPLICA do NG (app/dashboards/replicas.py).
QUERIES["agendamentos_setor_replicas_RJ"] = {
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
            'RÉPLICA'                                        AS "SETOR",
            v.agendamento_descricao                         AS "DESCRICAO",
            v.operacao_descricao                            AS "OPERACAO",
            ps.id_situacao                                  AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        LEFT JOIN public.processo ps ON ps.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = ps.id_situacao
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'RÉPLICA - %'
        """,
        "description": "Agendamentos do setor RÉPLICA (RJ) via vw_dashboard_agendamentos_detalhados — base do dashboard Réplicas (RJ). No NG o setor é RÉPLICA (singular) e tem 3 atividades: ELABORAR RÉPLICA, RÉPLICA CANCELADA e VERIFICAR CONTESTAÇÃO.",
        "params": []
    }


QUERIES["processos_status_1g_replicas_RJ"] = {
        "database": "lexflow",
        "query": """
        SELECT DISTINCT
            CAST(v.processo_id AS INTEGER)              AS processo_id,
            p.id_status_grau1                           AS "ID_1G",
            spg.nome                                    AS "STATUS_1G",
            p.id_situacao                                   AS "ID_SITUACAO",
            sit.description                                 AS "SITUACAO"
        FROM public.vw_dashboard_agendamentos_detalhados v
        JOIN public.processo p ON p.id = CAST(v.processo_id AS INTEGER)
        LEFT JOIN public.situacao sit ON sit.id = p.id_situacao
        LEFT JOIN public.status_primeiro_grau spg ON p.id_status_grau1 = spg.id
        WHERE v.id_escritorio_assinante = 27
          AND v.setor_atividade_nome LIKE 'RÉPLICA - %'
        """,
        "description": "Status de 1G (primeiro grau) dos processos do setor RÉPLICA (RJ) — base do card de taxa de procedência.",
        "params": []
    }


# V2 (19/11/2026): Controle de Processos no RJ (escritório 27), que a v1 não tem: o histórico de subfases do RJ
# (log_subfase_processual traz só os escritórios 20 e 21) para o tempo médio por subfase
# (app/dashboards/controle_processos.py). controle_processo e controle_processo_todas_situacoes já trazem todos os
# escritórios (o cálculo recorta pelo escritório).
QUERIES["log_subfase_processual_RJ"] = {
        "database": "lexflow",
        "query": """
        SELECT
            lfp.id_processo                        AS "ID_PROCESSO",
            p.id_escritorio_assinante               AS "ID_ESCRITORIO",
            p.id_situacao                           AS "ID_SITUACAO",
            lfp.id_fase                             AS "ID_FASE",
            f.description                           AS "FASE",
            lfp.id_status_processual                AS "ID_SUBFASE",
            sp.description                          AS "SUBFASE",
            lfp.tipo_movimentacao                   AS "TIPO_MOVIMENTACAO",
            lfp.data                                AS "DATA"
        FROM public.log_fase_processual lfp
        JOIN public.processo p                  ON p.id = lfp.id_processo
        LEFT JOIN public.fase f                 ON lfp.id_fase = f.id
        LEFT JOIN public.status_processual sp   ON lfp.id_status_processual = sp.id
        WHERE p.id_escritorio_assinante = 27
          AND p.id_situacao IN (1, 6)
          AND lfp.id_status_processual IS NOT NULL
        ORDER BY lfp.id_processo, lfp.data
        """,
        "description": (
            "Histórico de movimentação de fase/subfase (log_fase_processual) dos escritórios "
            "NG (20) e LA (21) — usado para estimar o tempo médio de permanência por subfase "
            "no dashboard Controle de Processos. Situação ATIVO (1) e SUSPENSO/SOBRESTADO (6)."
        ),
        "params": []
    }


# Agravos fora de toda query do LexFlow que lê processo (regra da v1 de 06/11/2026, que lá rodava no fim do
# queries.py). Fica no fim do arquivo, depois de todas as queries; agendamentos_* ficam de fora. Ver lexflow_agravo.
from app.lexflow_agravo import aplicar_em as _excluir_agravos

_excluir_agravos(QUERIES)
