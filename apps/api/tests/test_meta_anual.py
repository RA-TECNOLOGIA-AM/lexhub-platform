"""Meta anual (Financeiro): o cálculo da v1 sobre a planilha do financeiro (Google Sheets) e a fonte de planilhas."""

import asyncio
import io

from openpyxl import Workbook

from app import sheets
from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/meta-anual"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def repasse(data: str, hono: float, sucumbencia: float = 0.0) -> dict:
    """Uma linha da aba REPASSES CLIENTES (só as colunas que o cálculo usa)."""
    return {"DATA DO TED": data, "HONO": hono, "SUCUMBÊNCIA": sucumbencia}


def _pronto(repo, sources, banco="sheets_financeiro_ng", ref="NG"):
    repo.grant(USER_ID, "NG", "meta-anual", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], banco)] = (
        ref  # unidade ligada só a essa planilha
    )
    sources.data["REPASSES CLIENTES"] = [
        repasse("2026-02-10", 1_000_000),  # 1º trimestre
        repasse("2026-08-05", 2_000_000, 600_000),  # 3º trimestre
        repasse("2026-11-03", 1_000_000),  # 4º trimestre, até hoje (11/11)
        repasse("2026-11-30", 9_000_000),  # depois de hoje: fora do acumulado
        repasse("2025-11-01", 500_000),  # o ano anterior até o mesmo dia
    ]


def test_meta_anual_le_a_planilha_e_calcula_como_a_v1(client, signer, repo, sources):
    _pronto(repo, sources)
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == "Planilha do financeiro"
    d = body["data"]
    assert d["year"] == 2026 and d["as_of"] == "2026-11-11" and d["trimestre_atual"] == "4T"
    # acumulado até hoje: 1,0 + 2,6 + 1,0 mi (o TED de 30/11 fica de fora); 4,6 mi >= Base (4,4 mi)
    assert d["ytd"]["atingido"] == 4_600_000
    assert d["ytd"]["zona"] == "BASE" and d["ytd"]["proxima_zona"] == "AVANCADA"
    assert d["ytd"]["atingido_compare"] == 500_000
    cards = {c["trimestre"]: c for c in d["cards_trimestre"]}
    assert cards["3T"]["atingido"] == 2_600_000 and cards["4T"]["status"] == "em_curso"
    assert d["predicao"]["super_meta_anual"]["meta"] == 6_900_000
    assert sources.last.db_name == "sheets_financeiro_ng"


def test_meta_anual_da_la_le_a_planilha_da_la_com_as_metas_da_la(client, signer, repo, sources):
    """A LA (sem a planilha da NG) lê a sua (sheets_financeiro_la) e usa as metas da v1 da LA."""
    _pronto(repo, sources, banco="sheets_financeiro_la", ref="LA")
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert sources.last.db_name == "sheets_financeiro_la"
    assert d["ytd"]["metas"]["SUPER"] == 11_000_000  # NG: 6,9 mi
    # 4,6 mi: abaixo da Triste da LA (5,59 mi)
    assert d["ytd"]["zona"] == "TRISTE" and d["ytd"]["proxima_zona"] == "BASE"


def test_meta_anual_sem_planilha_ligada_503(client, signer, repo):
    repo.grant(USER_ID, "NG", "meta-anual", "all")
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 503


def test_xlsx_vira_linhas_como_na_v1():
    wb = Workbook()
    ws = wb.active
    ws.title = "REPASSES CLIENTES"
    ws.append(["DATA DO TED", " HONO ", None, "HONO"])
    ws.append(["2026-01-02", 10, "x", 20])
    ws.append([None, None, None, None])  # linha vazia: some
    buf = io.BytesIO()
    wb.save(buf)
    abas = sheets._parse_xlsx(buf.getvalue())
    # cabeçalho limpo, coluna sem nome ignorada e nome repetido desduplicado (HONO_2)
    assert abas == {"REPASSES CLIENTES": [{"DATA DO TED": "2026-01-02", "HONO": 10, "HONO_2": 20}]}


def test_planilha_e_fonte_da_v2_e_fetch_sheet_le_a_fonte_do_dashboard():
    from app.registered_sources import RegisteredSourceFetcher
    from app.sources import (
        source_fetcher,
    )  # depois do app carregado (ciclo app.sources <-> cópias da v1)

    assert sheets.is_sheet("sheets_financeiro_ng") and not sheets.is_sheet("ng")
    # O link da planilha antiga está cifrado no banco (PR 3): lida como as fontes da tela.
    assert isinstance(
        source_fetcher(None, "sheets_financeiro_ng", object()), RegisteredSourceFetcher
    )

    class Fonte:
        async def fetch(self, aba):
            return [{"aba": aba}]

    async def ler():
        token = sheets.usar_fonte(Fonte())
        try:
            return await sheets.fetch_sheet("financeiro_NG")
        finally:
            sheets.soltar_fonte(token)

    assert asyncio.run(ler()) == [{"aba": "REPASSES CLIENTES"}]
