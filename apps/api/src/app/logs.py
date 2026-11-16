"""Logs do terminal: uma linha por evento, com hora, nível colorido e de onde veio.

    14:03:22  INFO   bancos   ng conectado em 0,6s (pool 2-10, até 2 consultas simultâneas)
    14:03:25  INFO   http     200  GET  dashboard protocolo · NG  1,42s  piloto@lexgroup.com.br

Só formata e liga os loggers; quem decide o que logar são os módulos. Cores só em terminal de
verdade (some quando a saída vai para arquivo ou quando NO_COLOR está definida).
"""

import logging
import os
import sys

# Logger -> etiqueta curta. O primeiro prefixo que bater vale (os mais específicos antes).
_SCOPES: tuple[tuple[str, str], ...] = (
    ("app.requests", "http"),
    ("app.startup", "api"),
    ("app.auth", "login"),
    ("app.database", "bancos"),
    ("app.source_cache", "cache"),
    ("app.cache_warmer", "aquecedor"),
    ("app.analyses", "cálculo"),
    ("app.dashboards", "cálculo"),
    ("uvicorn", "uvicorn"),
)
_SCOPE_WIDTH = max(len(label) for _, label in _SCOPES)

# Bibliotecas que falam demais em INFO (cada chamada HTTP ao Supabase vira uma linha).
_QUIET = ("httpx", "httpcore", "hpack", "asyncio", "multipart")

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

_LEVEL_COLORS = {
    logging.DEBUG: DIM,
    logging.INFO: GREEN,
    logging.WARNING: YELLOW,
    logging.ERROR: RED,
    logging.CRITICAL: BOLD + RED,
}
_LEVEL_NAMES = {logging.WARNING: "AVISO", logging.ERROR: "ERRO", logging.CRITICAL: "CRÍTICO"}


def scope_of(logger_name: str) -> str:
    """Etiqueta curta do logger ('app.database' -> 'bancos'); desconhecido = último pedaço."""
    for prefix, label in _SCOPES:
        if logger_name == prefix or logger_name.startswith(prefix + "."):
            return label
    return logger_name.rsplit(".", 1)[-1]


def wants_color(stream) -> bool:
    """Cor só em terminal interativo e sem NO_COLOR (https://no-color.org)."""
    if os.environ.get("NO_COLOR"):
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


class Paint:
    """Pinta texto com ANSI, ou não faz nada quando a cor está desligada."""

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        return "".join(styles) + text + RESET


class TerminalFormatter(logging.Formatter):
    """`hora  NÍVEL  escopo  mensagem` (+ traceback quando houver)."""

    def __init__(self, color: bool):
        super().__init__()
        self.paint = Paint(color)

    def format(self, record: logging.LogRecord) -> str:
        p = self.paint
        when = self.formatTime(record, "%H:%M:%S")
        level = _LEVEL_NAMES.get(record.levelno, record.levelname).ljust(5)
        scope = scope_of(record.name).ljust(_SCOPE_WIDTH)
        message = record.getMessage()
        if record.levelno >= logging.ERROR:
            message = p(message, RED)
        elif record.levelno >= logging.WARNING:
            message = p(message, YELLOW)
        line = f"{p(when, DIM)}  {p(level, _LEVEL_COLORS.get(record.levelno, ''))}  {p(scope, CYAN)}  {message}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


_HANDLER_FLAG = "_lexhub_terminal"


def configure_logging(level: str = "INFO", stream=None) -> None:
    """Liga os logs da API no terminal. Pode ser chamada de novo (troca o nível, não duplica).

    Os logs do uvicorn passam a sair no mesmo formato; o log de acesso dele é desligado porque
    `app.request_log` escreve uma linha melhor por requisição (rota, usuário, tempo).
    """
    stream = stream or sys.stderr
    # Windows: saída redirecionada para arquivo pode estar em cp1252; acento estranho não derruba o log.
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(errors="replace")
        except (ValueError, OSError):
            pass
    if sys.platform == "win32" and wants_color(stream):
        os.system("")  # liga as sequências ANSI no console antigo do Windows

    root = logging.getLogger()
    numeric = logging.getLevelName(level.upper())
    root.setLevel(numeric if isinstance(numeric, int) else logging.INFO)

    handler = next((h for h in root.handlers if getattr(h, _HANDLER_FLAG, False)), None)
    if handler is None:
        handler = logging.StreamHandler(stream)
        setattr(handler, _HANDLER_FLAG, True)
        root.addHandler(handler)
    handler.setFormatter(TerminalFormatter(color=wants_color(stream)))

    for name in _QUIET:
        logging.getLogger(name).setLevel(logging.WARNING)

    # uvicorn configura os próprios handlers antes de carregar a app: troca pelo nosso formato.
    for name in ("uvicorn", "uvicorn.error"):
        uv = logging.getLogger(name)
        uv.handlers.clear()
        uv.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.propagate = False
    access.disabled = True


def seconds(value: float) -> str:
    """Duração legível em pt-BR: 0,08s / 1,4s / 2min 05s."""
    if value < 1:
        return f"{value:.2f}s".replace(".", ",")
    if value < 10:
        return f"{value:.1f}s".replace(".", ",")
    if value < 60:
        return f"{round(value)}s"
    minutes, rest = divmod(round(value), 60)
    return f"{minutes}min {rest:02d}s" if rest else f"{minutes}min"
