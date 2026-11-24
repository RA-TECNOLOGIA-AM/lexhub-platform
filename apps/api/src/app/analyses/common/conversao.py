"""Conversões dos valores do banco: as regras comuns das análises (V2).

As cópias da v1 tinham, cada uma, o próprio `_to_date` (38 cópias, todas com o mesmo resultado), `_to_int`
(21 cópias iguais) e `_converter_valor` (17 cópias, duas regras). Aqui fica uma só de cada.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.utils import parse_date_from_db


def para_data(valor: Any) -> date | None:
    """Valor bruto do banco -> `date` (datetime vira a data dele, no fuso de Manaus); ausente ou inválido ->
    None."""
    if not valor:
        return None
    convertido = parse_date_from_db(valor)
    if isinstance(convertido, datetime):
        return convertido.date()
    if isinstance(convertido, date):
        return convertido
    return None


def para_inteiro(valor: Any) -> int | None:
    """Valor bruto do banco -> `int` (`int(valor)`); None, "" ou inválido -> None."""
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def para_valor(valor: Any, *, remover_nbsp: bool = True) -> float:
    """Valor monetário -> float, com a regra pt-BR (Comercial e LexPre): tira "R$" e espaços; com "." e ","
    o ponto é milhar e a vírgula decimal (1.234,56); só "," é decimal (470,00); só "." é decimal (470.00).
    None, vazio ou inválido -> 0.0. `remover_nbsp=False`: o espaço não separável fica (as cópias do Pré-protocolo
    da v1 só tiravam o espaço comum; um valor com ele vira 0.0)."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float, Decimal)):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return 0.0
    texto = texto.replace("R$", "")
    if remover_nbsp:
        texto = texto.replace("\u00a0", "")
    texto = texto.replace(" ", "").strip()
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except (ValueError, TypeError):
        return 0.0


def para_valor_digitos(valor: Any) -> float:
    """Valor monetário -> float, com a regra da Execução, Acordos e Recursal da v1: vírgula vira ponto e só
    ficam dígitos e pontos. None ou inválido -> 0.0.

    V2: separador de milhar em texto. Com "." e "," juntos ("1.234,56") o ponto é milhar; com mais de um ponto e
    sem vírgula ("1.234.567"), também. Na v1 os dois viravam 0.0. Os formatos gravados hoje pelo LexFlow ("1234.56",
    "1234", "470,50") dão o mesmo resultado de antes."""
    if valor is None:
        return 0.0
    try:
        if isinstance(valor, (Decimal, int, float)):
            return float(valor)
        if isinstance(valor, str):
            limpo = valor.strip()
            if ("," in limpo and "." in limpo) or ("," not in limpo and limpo.count(".") > 1):
                limpo = limpo.replace(".", "")
            limpo = limpo.replace(",", ".")
            limpo = "".join(c for c in limpo if c.isdigit() or c == ".")
            return float(limpo) if limpo else 0.0
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return 0.0
