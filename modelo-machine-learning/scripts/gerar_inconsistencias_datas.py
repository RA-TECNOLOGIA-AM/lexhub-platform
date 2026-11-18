# -*- coding: utf-8 -*-
"""
Gera Inconsistencias_Datas_Processo.csv: lista de triagem (uso operacional, nao
e a coorte de pesquisa) com processos cujas datas tem bugs reais de cadastro,
pra alguem ir corrigir na origem (LexFlow). Reconstruido em 19/10/2026 porque o
script original que gerou a primeira versao do CSV (12/10/2026) nao foi salvo -
este arquivo passa a ser a fonte reprodutivel daqui pra frente.

Mesmas 4 categorias de bug documentadas no cabecalho de
coorte_sobrevivencia_2_estagios.sql (a janela valida usada la e [1971-01-01,
hoje + 730 dias] - qualquer coisa fora disso e tratada como invalida nessa
pesquisa, mas fica preservada aqui em texto puro pra correcao na origem):

  1. Contratacao com timestamp zero: epoch Unix (1970-01-01 00:00:00 UTC) vira
     1969-12-31 ao converter pra America/Manaus.
  2. Sentenca com data anterior a contratacao: ordem logica impossivel.
  3. Acordao com data anterior a sentenca/contratacao: acordao so existe se
     houve recurso da sentenca, entao nao pode ser anterior a ela (nem a
     contratacao, se nao ha sentenca registrada).
  4. Sentenca/Acordao com ano absurdo (fora da janela 1971-hoje+730): bug de
     formulario com digito a mais/trocado no ano (ex: 20263, 3202).

Excecao tratada desde 20/10/2026 (achado do usuario): quando o acordao anula a
sentenca (id_acordao_merito_grau2 = 8, "SENTENCA ANULADA"), o processo volta
pro 1G e uma NOVA sentenca e proferida depois - entao acordao_data anterior a
sentenca e ESPERADO nesse caso, nao bug. So entra na categoria 3 quando o
acordao tem um resultado de merito de verdade (ou nenhum codigo registrado -
ambiguo, mantido como bug ate confirmar caso a caso). Quantificado em
20/10/2026: de 130 casos flagados como categoria 3, so 5 eram SENTENCA ANULADA.

Nota: este CSV mantem numero_processo em texto puro de proposito - e pra uso
interno de quem vai corrigir o cadastro na origem, nao faz parte da coorte de
pesquisa (que pseudonimiza esse campo, ver scripts/atualizar_dashboard_tcc.py).

Rodar: TCC - Luiz/.venv/bin/python scripts/gerar_inconsistencias_datas.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import asyncio
import os

from dotenv import load_dotenv

BASE_DIR = ML_DIR
CSV_OUT = f"{BASE_DIR}/Inconsistencias_Datas_Processo.csv"

load_dotenv((_os_ml.environ.get("LEXHUB_API_ENV") or REPO_DIR + "/apps/api/.env"))

import asyncpg
import pandas as pd

QUERY = """
with base as (
  select
    p.id,
    p.numero_processo,
    p.segredo_justica,
    (p.contratacao at time zone 'America/Manaus')::date as contratacao_d,
    (p.sentenca at time zone 'America/Manaus')::date as sentenca_d,
    p.acordao_data as acordao_d,
    (p.acordo_fechado at time zone 'America/Manaus')::date as acordo_fechado_d,
    (p.ultima_movimentacao at time zone 'America/Manaus')::date as ultima_mov_d,
    (p.id_acordao_merito_grau2 = 8) as acordao_anulou_sentenca
  from processo p
  where p.contratacao is not null
)
select
  id, numero_processo, segredo_justica,
  case
    when contratacao_d = date '1969-12-31' then
      'Contratacao com timestamp zero'
    when sentenca_d is not null and sentenca_d < contratacao_d then
      'Sentenca com data anterior a contratacao'
    when acordao_d is not null and not acordao_anulou_sentenca
         and sentenca_d is not null and acordao_d < sentenca_d then
      'Acordao com data anterior a sentenca/contratacao'
    when acordao_d is not null and not acordao_anulou_sentenca
         and sentenca_d is null and acordao_d < contratacao_d then
      'Acordao com data anterior a sentenca/contratacao'
    when sentenca_d is not null and (sentenca_d < date '1971-01-01' or sentenca_d > current_date + 730) then
      'Sentenca/Acordao com ano absurdo no futuro (bug de formulario)'
    when acordao_d is not null and (acordao_d < date '1971-01-01' or acordao_d > current_date + 730) then
      'Sentenca/Acordao com ano absurdo no futuro (bug de formulario)'
  end as problema,
  case
    when contratacao_d = date '1969-12-31' then
      'contratacao vira ' || contratacao_d::text || ' apos conversao pra America/Manaus (epoch zero)'
    when sentenca_d is not null and sentenca_d < contratacao_d then
      'sentenca=' || sentenca_d::text || ' e anterior a contratacao=' || contratacao_d::text
    when acordao_d is not null and not acordao_anulou_sentenca
         and sentenca_d is not null and acordao_d < sentenca_d then
      'acordao_data=' || acordao_d::text || ' e anterior a sentenca=' || sentenca_d::text
    when acordao_d is not null and not acordao_anulou_sentenca
         and sentenca_d is null and acordao_d < contratacao_d then
      'acordao_data=' || acordao_d::text || ' e anterior a contratacao=' || contratacao_d::text || ' (sem sentenca registrada)'
    when sentenca_d is not null and (sentenca_d < date '1971-01-01' or sentenca_d > current_date + 730) then
      'sentenca=' || sentenca_d::text || ' tem ano invalido/futuro demais'
    when acordao_d is not null and (acordao_d < date '1971-01-01' or acordao_d > current_date + 730) then
      'acordao_data=' || acordao_d::text || ' tem ano invalido/futuro demais'
  end as detalhe,
  contratacao_d::text as contratacao,
  sentenca_d::text as sentenca,
  acordao_d::text as acordao_data,
  acordo_fechado_d::text as acordo_fechado,
  ultima_mov_d::text as ultima_movimentacao
from base
where contratacao_d = date '1969-12-31'
   or (sentenca_d is not null and sentenca_d < contratacao_d)
   or (acordao_d is not null and not acordao_anulou_sentenca and sentenca_d is not null and acordao_d < sentenca_d)
   or (acordao_d is not null and not acordao_anulou_sentenca and sentenca_d is null and acordao_d < contratacao_d)
   or (sentenca_d is not null and (sentenca_d < date '1971-01-01' or sentenca_d > current_date + 730))
   or (acordao_d is not null and (acordao_d < date '1971-01-01' or acordao_d > current_date + 730))
order by id;
"""


async def main():
    conn = await asyncpg.connect(
        host=os.environ["DB_LEXFLOW_HOST"],
        port=os.environ["DB_LEXFLOW_PORT"],
        database=os.environ["DB_LEXFLOW_NAME"],
        user=os.environ["DB_LEXFLOW_USER"],
        password=os.environ["DB_LEXFLOW_PASSWORD"],
    )
    try:
        rows = await conn.fetch(QUERY)
    finally:
        await conn.close()

    df = pd.DataFrame([dict(r) for r in rows])
    df.to_csv(CSV_OUT, index=False, sep=";", encoding="utf-8-sig")
    print(f"Inconsistencias geradas: {len(df)} processos -> {CSV_OUT}")
    print(df["problema"].value_counts().to_string())


if __name__ == "__main__":
    asyncio.run(main())
