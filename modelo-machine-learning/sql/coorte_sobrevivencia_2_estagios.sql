-- ============================================================================
-- Coorte de sobrevivencia em 2 estagios - LexFlow (projeto Supabase sohdxpfdreyfwjcribal)
-- TCC Luiz Reis - Modelagem de Sobrevivencia com Riscos Competitivos
--
-- Estagio 1: distribuicao -> desfecho (Acordo / Merito favoravel com proveito
--            economico / Merito sem proveito ou desfavoravel / Censurado)
-- Estagio 2: para quem chegou em Acordo ou Merito favoravel com proveito,
--            tempo ate o pagamento efetivo (alvara compensado/incontroverso
--            ou pagamento de acordo) vs. ainda nao pago (censurado)
--
-- Marco zero (t=0): DISTRIBUICAO do processo (data real de inicio da
-- tramitacao judicial), nao a contratacao (relacao comercial com o
-- escritorio, que pode ser bem antes ou bem depois da distribuicao - mediana
-- da diferenca = 0 dias, mas com cauda grande pros dois lados). Trocado em
-- 03/11/2026 (achado do usuario): contratacao media o relacionamento com o
-- escritorio, nao o tempo processual de verdade. Distribuicao tambem cobre
-- mais processos (~88k vs ~70k com contratacao preenchida, no universo sem
-- segredo de justica) - a coorte cresceu de ~40,8k para ~58,2k processos.
--
-- 06/11/2026: processos de AGRAVO (numero CNJ com origem 0000/9000/9001/9002)
-- excluidos da coorte - sao cadastrados no LexFlow como processos proprios,
-- mas nao sao acoes. Mesma regra aplicada em todos os dashboards do LexHub
-- (queries.py). Efeito: coorte 58.434 -> 57.195 (-1.239).
--
-- Limpeza de dados aplicada (ver Inconsistencias_Datas_Processo.csv para o
-- detalhe processo a processo, nao corrigido na origem ainda):
--   - Qualquer data fora da janela [1971-01-01, hoje + 730 dias] e tratada
--     como NULL, em qualquer um dos campos de data. Isso cobre dois bugs
--     reais encontrados na base:
--       (a) "timestamp zero" (epoch Unix 1970-01-01 UTC vira 1969-12-31 ao
--           converter para America/Manaus) - 4 processos tinham isso em
--           `contratacao` (campo que nao e mais o t=0; `distribuicao` em si
--           nao tem nenhum caso desse sentinela especifico, e so 2 processos
--           fora da janela de validade no total, vs. 19 em `contratacao`);
--       (b) anos com digito extra/trocado (ex: 20263, 3202) em sentenca/
--           acordao_data - poucos casos, mas quebravam duracao_dias.
--   - Processos cuja `distribuicao` fica invalida apos a limpeza NAO tem
--     ancora (t=0) valida e sao descartados inteiramente da coorte.
--   - Todas as conversoes de timestamptz para date usam America/Manaus
--     explicitamente (ver bug historico corrigido em utils.py do projeto -
--     .date() sem fuso zerava ~4h/dia).
--
-- Regra de precedencia dos eventos do Estagio 1:
--   - Acordo compete de verdade: se fechado antes (ou no mesmo dia) do fim
--     do merito, ele vence e encerra a tramitacao.
--   - Sentenca (1G) e Acordao (2G) NAO competem entre si - sao sequenciais
--     (acordao so existe se houve recurso da sentenca). Quando acordao
--     existe, ele e o desfecho de merito valido, mesmo que a data cadastrada
--     do acordao apareca (por erro de registro, ~315 casos observados)
--     antes da sentenca - por isso a data final do merito usa
--     GREATEST(sentenca, acordao) em vez de uma comparacao ingênua.
--   - EXCECAO (corrigida em 20/10/2026, achado do usuario): quando
--     id_acordao_merito_grau2 = 8 ("SENTENCA ANULADA"), o acordao nao decidiu
--     merito - so anulou a sentenca e devolveu o processo pro 1G, que profere
--     uma NOVA sentenca depois (sobrescrita no mesmo campo `sentenca`). Nesse
--     caso o desfecho de merito valido e o da sentenca (nova), nao o do
--     acordao - por isso sentenca_d as vezes aparece ANTERIOR a acordao_d sem
--     ser erro de cadastro (~5 dos ~175 processos com esse codigo na base
--     inteira apanhavam a regra de precedencia errada antes dessa correcao).
--   - Favoravel "com proveito economico" = categorias 1 e 3 dos catalogos
--     sentenca_merito_primeiro_grau / acordao_merito_segundo_grau
--     (PROCEDENTE / PARCIALMENTE PROCEDENTE, ambas "COM PROVEITO ECONOMICO").
--     So essas seguem para o Estagio 2 (ha dinheiro a cobrar).
--
-- Escritorio (id_escritorio_assinante, confirmado via tabela escritorio_assinante):
--   20 = NG (Nicolas Gomes) | 21 = LA/AM (Luis Albert AM) | 27 = LA/RJ (Luis Albert RJ)
--
-- Covariaveis adicionadas em 13/10/2026 (mais dimensoes p/ dashboard + Fase 3):
--   - comarca (public.comarca.nome) e competencia (public.competencias.nome):
--     atributos fixados na distribuicao do processo -> entram como covariavel
--     plena no Cox/Fine-Gray, igual tipo_acao/materia.
--   - fase (public.fase.description) e subfase (public.status_processual.description,
--     e isso que o resto do sistema chama de "subfase" - nao existe id_subfase
--     separado): estado ATUAL/mutavel do processo, nao um atributo fixo em t=0.
--     Entram so como ranking exploratorio no dashboard, NAO como covariavel do
--     modelo formal (viés de causalidade reversa / lookahead).
--   - juiz_1g e relator_2g: so preenchidos apos o merito ser decidido na
--     instancia correspondente (texto livre, nao FK). Mesmo motivo acima:
--     exploratorio apenas, population scoped a quem ja foi decidido naquela
--     instancia (sentenca p/ juiz_1g, acordao p/ relator_2g).
--
-- Pseudonimizacao (19/10/2026, Fase 1 do plano de TCC): esta query ainda
-- seleciona numero_processo em texto puro (precisa pra alguns scripts de
-- auditoria rodarem direto contra ela). Quem consome o resultado pra pesquisa
-- (scripts/atualizar_dashboard_tcc.py) troca esse campo por um hash SHA-256
-- antes de gravar em disco - ver pseudonimizar_numero_processo() la. O
-- endpoint de producao (queries.py / tcc_sobrevivencia_processual) nunca
-- expos numero_processo pra comecar.
-- ============================================================================

with base as (
  select
    p.id,
    p.numero_processo,
    p.id_escritorio_assinante,   -- 20=NG, 21=LA (AM) - RJ (27) fora desde 09/11/2026
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
    -- 09/11/2026: estudo do TCC so com NG (20) e LA/AM (21). LA/RJ (27) sai da coorte
    -- (quase sem desfechos - 96% censurado - e ja ficava fora dos modelos das Fases 3-6);
    -- id 3 e escritorio de teste.
    and p.id_escritorio_assinante in (20, 21)
    -- 06/11/2026: agravo fora da coorte (processo proprio no LexFlow, nao e acao).
    -- Agravo = CNJ com 20 digitos e origem (4 ultimos) 0000/9000/9001/9002.
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
    -- id_acordao_merito_grau2 = 8 ("SENTENCA ANULADA"): o 2G anulou a sentenca e
    -- devolveu o processo pro 1G, que profere uma NOVA sentenca depois (sobrescrita
    -- no mesmo campo `sentenca` - por isso sentenca_d as vezes fica ANTERIOR ao
    -- acordao_d nesses casos, sem ser bug de data). O acordao nao decidiu merito
    -- nenhum aqui, entao o desfecho de verdade e o da sentenca (nova), nao o do
    -- acordao. Achado do usuario em 20/10/2026, confirmado: so ~175 processos tem
    -- esse codigo em toda a base (~0,4% da coorte).
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
    end as data_evento_e1
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
  id,
  numero_processo,
  id_escritorio_assinante,
  distribuicao_d,

  -- Estagio 1
  tipo_evento_e1,
  data_evento_e1,
  (data_evento_e1 - distribuicao_d) as duracao_dias_e1,
  id_sentenca_merito_grau1,
  id_acordao_merito_grau2,

  -- Estagio 2 (null para quem nao chegou em ACORDO / MERITO_FAVORAVEL_COM_PROVEITO)
  tipo_evento_e2,
  data_pagamento,
  case when tipo_evento_e2 is not null then
    (greatest(coalesce(data_pagamento, ultima_mov_d), data_evento_e1) - data_evento_e1)
  end as duracao_dias_e2,

  -- Covariaveis (uso pleno no modelo: tipo_acao, materia, valor_causa, escritorio, comarca, competencia)
  tipo_acao, materia, valor_causa, id_comarca, comarca, uf, competencia,

  -- Exploratorias apenas (conhecidas so no desfecho - ver cabecalho do script
  -- atualizar_dashboard_tcc.py / fase3_cox.py para a justificativa de nao
  -- entrarem como covariavel do Cox/Fine-Gray): fase, subfase (status atual
  -- do processo), juiz_1g e relator_2g (quem decidiu, preenchido so apos o
  -- merito na instancia correspondente)
  fase, subfase, juiz_1g, relator_2g

from estagio2
where data_evento_e1 is not null                       -- descarta quem nao tem nem evento nem censura valida
  and (data_evento_e1 - distribuicao_d) >= 0;            -- descarta residual de duracao negativa
