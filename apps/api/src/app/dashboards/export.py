"""Arquivo da exportação (CSV ou XLSX), igual à v1: mesmos cabeçalhos, mesma formatação de valores.

Funções puras: escolhem os campos, formatam as linhas e geram os bytes. A rota cuida de acesso e auditoria.
"""

import csv
import io
from datetime import date, datetime
from typing import Any

from openpyxl import Workbook

from app.dashboards.base import ExportSpec

FORMATS = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class ExportError(ValueError):
    """Formato ou campo pedido que o servidor não conhece (vira 400)."""


def pick_format(raw: str | None) -> str:
    fmt = (raw or "csv").strip().lower()
    if fmt not in FORMATS:
        raise ExportError("Formato inválido. Use csv ou xlsx.")
    return fmt


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


def filename(dashboard_key: str, unit_code: str, fmt: str) -> str:
    """protocolo_lexpre_NG_relatorio.xlsx (padrão da v1: <dashboard>_<unidade>_relatorio)."""
    return f"{dashboard_key.replace('-', '_')}_{unit_code}_relatorio.{fmt}"
