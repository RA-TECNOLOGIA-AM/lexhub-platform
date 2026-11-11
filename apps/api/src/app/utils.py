"""Funções utilitárias para o projeto."""
import calendar
from datetime import date, datetime, time
from typing import Any, Optional
from zoneinfo import ZoneInfo

# Fuso horário usado para truncar ``timestamptz`` em data de calendário.
# As colunas de data/hora do LexFlow são ``timestamptz``, sempre armazenadas e
# devolvidas pelo asyncpg em UTC — sem essa conversão, ``.date()`` pega o dia
# em UTC, que diverge do dia local do escritório em qualquer horário entre
# 20h e 23h59 (Manaus é UTC-4, sem horário de verão). Confirmado em
# 2026-09-16: uma tarefa encerrada às 21h de Manaus aparecia contada no dia
# seguinte em qualquer contagem "por período" do sistema — bug sistêmico, não
# isolado a um dashboard, pois toda filtragem por período passa por aqui.
# NG e LA-AM (a maior parte da base) ficam em Manaus; LA-RJ (UTC-3) fica com
# um erro residual de 1h em vez do erro de até 4h de antes — esta função não
# recebe contexto de escritório para diferenciar por UF.
_FUSO_HORARIO_PADRAO = ZoneInfo("America/Manaus")


def _para_data_local(dt: datetime) -> date:
    """Data de calendário local a partir de um datetime, convertendo para o
    fuso padrão quando ``dt`` tiver timezone (aware); naive é mantido como está.

    Exceção: ``dt`` em exatamente meia-noite UTC (``00:00:00``, sem
    microssegundos) não representa um horário real — é uma coluna "só data"
    gravada como ``timestamptz`` (ex.: ``processo.execucao``/DATA_EXECUCAO,
    confirmado em 2026-10-07: ~100% dos valores recentes caem em meia-noite
    UTC exata). Convertida para Manaus, toda meia-noite UTC vira 20h do dia
    anterior, deslocando a data um dia pra trás sistematicamente. Um evento
    real praticamente nunca acontece no segundo exato da meia-noite UTC, então
    nesse caso usamos a data em UTC diretamente, sem conversão de fuso.
    """
    if dt.tzinfo is not None:
        if dt.time() == time(0, 0, 0, 0):
            return dt.date()
        dt = dt.astimezone(_FUSO_HORARIO_PADRAO)
    return dt.date()


def parse_date_from_db(date_str: str) -> Optional[date]:
    """Converte data/hora do banco de dados para objeto date (fuso local).

    Suporta formatos:
    - "2026-01-19 17:07:36.058" (formato SQL datetime)
    - "2026-01-19T17:07:36.058" (formato ISO)
    - "2026-01-19T17:07:36.058Z" (formato ISO com Z)
    - "2026-01-19" (apenas data)

    Args:
        date_str: String com a data no formato do banco de dados

    Returns:
        Objeto date ou None se não conseguir fazer o parse
    """
    if not date_str:
        return None

    # datetime é subclasse de date — checar datetime antes
    if isinstance(date_str, datetime):
        return _para_data_local(date_str)
    if isinstance(date_str, date):
        return date_str

    # Converter string para datetime
    date_str = str(date_str).strip()

    # Tentar formato SQL datetime: "2026-01-19 17:07:36.058" (sem timezone)
    try:
        # Remover microsegundos se houver
        date_str_clean = date_str.split('.')[0] if '.' in date_str else date_str
        return datetime.strptime(date_str_clean, "%Y-%m-%d %H:%M:%S").date()
    except ValueError:
        pass

    # Tentar formato ISO com T: "2026-01-19T17:07:36", "...Z" ou "...+00:00"
    try:
        if 'T' in date_str:
            return _para_data_local(datetime.fromisoformat(date_str.replace("Z", "+00:00")))
    except ValueError:
        pass

    # Tentar apenas data: "2026-01-19"
    try:
        return datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
    except ValueError:
        pass

    return None


def parse_datetime_from_db(date_str: str) -> Optional[datetime]:
    """Converte string de data do banco de dados para objeto datetime.
    
    Suporta os mesmos formatos de parse_date_from_db, mas retorna datetime.
    
    Args:
        date_str: String com a data no formato do banco de dados
        
    Returns:
        Objeto datetime ou None se não conseguir fazer o parse
    """
    if not date_str:
        return None
    
    # Se já for um objeto datetime, retornar direto
    if isinstance(date_str, datetime):
        return date_str
    if isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())
    
    # Converter string para datetime
    date_str = str(date_str).strip()
    
    # Tentar formato SQL datetime: "2026-01-19 17:07:36.058"
    try:
        # Tentar com microsegundos primeiro
        if '.' in date_str and len(date_str.split('.')[1]) <= 6:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                pass
        
        # Sem microsegundos
        date_str_clean = date_str.split('.')[0]
        return datetime.strptime(date_str_clean, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    
    # Tentar formato ISO com T: "2026-01-19T17:07:36"
    try:
        if 'T' in date_str:
            date_str_clean = date_str.replace("Z", "+00:00")
            if '+' in date_str_clean or date_str_clean.endswith('Z'):
                return datetime.fromisoformat(date_str_clean)
            else:
                # Sem timezone, remover microsegundos se houver
                date_str_clean = date_str_clean.split('.')[0]
                return datetime.fromisoformat(date_str_clean)
    except ValueError:
        pass
    
    # Tentar apenas data: "2026-01-19"
    try:
        return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
    except ValueError:
        pass

    return None


def _shift_months(referencia: date, months: int) -> date:
    """Desloca `referencia` em `months` meses civis, mantendo o dia do mês.

    Quando o mês de destino é mais curto que o dia original (ex.: 31/01 -> fevereiro),
    o dia é ajustado (clamped) para o último dia do mês de destino.
    """
    month_index = referencia.month - 1 + months
    year = referencia.year + month_index // 12
    month = month_index % 12 + 1
    ultimo_dia_mes = calendar.monthrange(year, month)[1]
    dia = min(referencia.day, ultimo_dia_mes)
    return date(year, month, dia)


def resolver_periodo_comparativo(
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[date, date, date, date]:
    """Resolve o período atual e o período comparativo ("mesmo período do mês anterior").

    Retorna (início_atual, fim_atual, início_anterior, fim_anterior), onde o período
    anterior é o mesmo recorte de dia-do-mês um mês civil antes do período atual
    (ex.: 01/08-20/08 -> período anterior 01/07-20/07), em vez de uma janela rolante
    de N dias colada ao fim do mês anterior.

    Quando `from_date`/`to_date` não são informados, o período atual é o mês corrente
    até hoje (dia 1 até hoje).
    """
    if from_date and to_date:
        data_inicio_atual = from_date
        data_fim_atual = to_date
    else:
        hoje = date.today()
        data_fim_atual = hoje
        data_inicio_atual = hoje.replace(day=1)

    data_inicio_anterior = _shift_months(data_inicio_atual, -1)
    data_fim_anterior = _shift_months(data_fim_atual, -1)
    return data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior


def normalizar_filtro_ids(valor: Any) -> set[int]:
    """Filtro por ID que aceita um valor ou vários (``?area_atuacao_id=1&area_atuacao_id=2``). Vazio = sem filtro."""
    if valor is None:
        return set()
    itens = valor if isinstance(valor, (list, tuple, set)) else [valor]
    ids: set[int] = set()
    for item in itens:
        try:
            ids.add(int(item))
        except (TypeError, ValueError):
            continue
    return ids


def normalizar_filtro_textos(valor: Any) -> set[str]:
    """Filtro de texto (ex.: UF) que aceita um valor ou vários; compara em maiúsculas, sem espaços. Vazio = sem filtro."""
    if valor is None:
        return set()
    itens = valor if isinstance(valor, (list, tuple, set)) else [valor]
    return {str(item).strip().upper() for item in itens if item is not None and str(item).strip()}
