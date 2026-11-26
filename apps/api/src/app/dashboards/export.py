"""Arquivo da exportação (CSV ou XLSX), igual à v1: mesmos cabeçalhos, mesma formatação de valores.

Funções puras: escolhem os campos, formatam as linhas e geram os bytes. A rota cuida de acesso e auditoria.
"""

import csv
import io
import zipfile
from datetime import date, datetime
from typing import Any

from openpyxl import Workbook

from app.dashboards.base import DashboardModule, ExportPart, ExportSpec

FORMATS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
ZIP = "application/zip"  # CSV de um relatório com partes: um .zip com um CSV por parte


class ExportError(ValueError):
    """Formato ou campo pedido que o servidor não conhece (vira 400)."""


def pick_format(raw: str | None) -> str:
    fmt = (raw or "csv").strip().lower()
    if fmt not in FORMATS:
        raise ExportError("Formato inválido. Use csv ou xlsx.")
    return fmt


def pick_report(
    module: DashboardModule, relatorio: str | None, unit_ref: str = ""
) -> ExportSpec | None:
    """O relatório pedido: o principal (sem ?relatorio) ou um dos export_reports, na versão da unidade
    (ExportSpec.por_unidade). None = não exporta."""
    if not relatorio:
        spec = module.export
    else:
        spec = module.export_reports.get(relatorio)
        if spec is None:
            raise ExportError(f"Relatório desconhecido: {relatorio}")
    return spec.por_unidade.get(unit_ref, spec) if spec else None


def pick_options(spec: ExportSpec, raw: dict[str, str]) -> dict[str, str]:
    """As escolhas da janela (ex.: criterio), com o padrão (a primeira) quando não vem. Valor desconhecido = erro."""
    escolhas: dict[str, str] = {}
    for opt in spec.options:
        valor = (raw.get(opt.key) or "").strip().lower() or next(iter(opt.choices))
        if valor not in opt.choices:
            raise ExportError(f"{opt.label} inválido: '{valor}'. Use {', '.join(opt.choices)}.")
        escolhas[opt.key] = valor
    return escolhas


def pick_fields(spec: ExportSpec, campos: list[str]) -> list[str]:
    """Os campos pedidos, na ordem pedida; nenhum = todos. Campo que o servidor não conhece = erro."""
    if not campos:
        return list(spec.fields)
    unknown = [c for c in campos if c not in spec.fields]
    if unknown:
        raise ExportError(f"Campo desconhecido: {', '.join(unknown)}")
    return list(dict.fromkeys(campos))


def format_value(value: Any) -> str:
    """Igual à v1 (_formatar_valor_export_comercial_ng): vazio, Sim/Não, dd/mm/aaaa ou texto."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    return str(value)


def table(
    spec: ExportSpec, slugs: list[str], rows: list[dict[str, Any]]
) -> tuple[list[str], list[list[str]]]:
    headers = [spec.labels[s] for s in slugs]
    return headers, [[format_value(row.get(spec.fields[s])) for s in slugs] for row in rows]


def to_csv(headers: list[str], data: list[list[str]]) -> bytes:
    """utf-8 com BOM (o Excel abre com acento certo), como na v1."""
    out = io.StringIO()
    writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(data)
    return out.getvalue().encode("utf-8-sig")


def to_xlsx(headers: list[str], data: list[list[str]], sheet_name: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    ws.append(headers)
    for line in data:
        ws.append(line)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def to_xlsx_por_aba(
    spec: ExportSpec, slugs: list[str], rows: list[dict[str, Any]], sheet_name: str
) -> bytes:
    """Uma aba por valor de `spec.sheet_by` (sem essa coluna dentro da aba). Sem linhas: uma aba só, vazia."""
    colunas = [s for s in slugs if spec.fields[s] != spec.sheet_by]
    grupos: dict[str, list[dict[str, Any]]] = {nome: [] for nome in spec.sheet_order}
    for row in rows:
        grupos.setdefault(format_value(row.get(spec.sheet_by)) or "—", []).append(row)
    abas = [(nome, linhas) for nome, linhas in grupos.items() if linhas]
    wb = Workbook()
    wb.remove(wb.active)
    for nome, linhas in abas or [(sheet_name, [])]:
        headers, data = table(spec, colunas, linhas)
        ws = wb.create_sheet(_nome_aba(spec.sheet_titles.get(nome, nome)))
        ws.append(headers)
        for line in data:
            ws.append(line)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def combined(prefix_parts: tuple[ExportPart, ...], **kwargs: Any) -> ExportSpec:
    """O relatório que junta as partes: campos e rótulos de cada uma com o prefixo, na ordem das partes."""

    async def _todas(ctx: Any) -> list[dict[str, Any]]:
        # A rota monta o arquivo parte a parte; aqui, as linhas de todas juntas (com a parte), para quem precisar.
        return [{**r, "_parte": p.prefix} for p in prefix_parts for r in await p.spec.rows(ctx)]

    fields = {f"{p.prefix}.{s}": c for p in prefix_parts for s, c in p.spec.fields.items()}
    labels = {
        f"{p.prefix}.{s}": rotulo for p in prefix_parts for s, rotulo in p.spec.labels.items()
    }
    return ExportSpec(fields=fields, labels=labels, rows=_todas, parts=prefix_parts, **kwargs)


def split_parts(spec: ExportSpec, slugs: list[str]) -> list[tuple[ExportPart, list[str]]]:
    """Os campos escolhidos de cada parte (sem o prefixo), só das partes com algum campo, na ordem das partes."""
    escolhidas = []
    for p in spec.parts:
        dela = [s.split(".", 1)[1] for s in slugs if s.startswith(f"{p.prefix}.")]
        if dela:
            escolhidas.append((p, dela))
    return escolhidas


def to_xlsx_abas(abas: list[tuple[str, list[str], list[list[str]]]]) -> bytes:
    """Um XLSX com uma aba por (nome, cabeçalhos, linhas), como _gerar_xlsx_export_multi_sheet da v1."""
    wb = Workbook()
    wb.remove(wb.active)
    for nome, headers, data in abas:
        ws = wb.create_sheet(_nome_aba(nome))
        ws.append(headers)
        for line in data:
            ws.append(line)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def to_zip(arquivos: list[tuple[str, bytes]]) -> bytes:
    """Um .zip com os arquivos (nome, bytes), como _gerar_zip_export_multi_csv da v1."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in arquivos:
            z.writestr(nome, conteudo)
    return buffer.getvalue()


def _nome_aba(nome: str) -> str:
    """O Excel não aceita : \\ / ? * [ ] no nome da aba, nem mais de 31 caracteres."""
    for c in ":\\/?*[]":
        nome = nome.replace(c, "-")
    return nome[:31] or "Aba"


def filename(dashboard_key: str, unit_code: str, fmt: str, partes: list[str] | None = None) -> str:
    """protocolo_lexpre_NG_relatorio.xlsx (padrão da v1: <dashboard>_<unidade>_relatorio). Com o relatório e as
    opções escolhidas no meio, como a v1: execucao_NG_saida_relatorio.csv, acordos_NG_atividades_por_prazo_..."""
    meio = "".join(f"_{p}" for p in (partes or []) if p)
    return f"{dashboard_key.replace('-', '_')}_{unit_code}{meio}_relatorio.{fmt}"
