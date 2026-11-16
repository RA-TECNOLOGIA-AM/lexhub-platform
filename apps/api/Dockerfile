# LexHub API V2: imagem de produção (Docker Swarm, 1 réplica).
# Build a partir de apps/api:  docker build -t lexhub-api:dev .
# Segredos NÃO entram na imagem: vêm do ambiente/secrets da stack (ver README).

# ---------- etapa 1: instala as dependências num venv ----------
FROM python:3.12-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- etapa 2: imagem final, só o venv e o código ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    TZ=America/Sao_Paulo \
    NO_COLOR=1 \
    PORT=8000

# Usuário sem privilégios: o processo da API nunca roda como root.
RUN groupadd --system app && useradd --system --gid app --no-create-home app

COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY --chown=app:app src ./src

USER app
EXPOSE 8000

# Liveness: /health não depende de banco, então o container só é reiniciado se a API travar.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health', timeout=4)"

# 1 worker de propósito: o cache das fontes e o aquecedor ficam em memória (um processo só).
# Atrás do proxy do Swarm, defina FORWARDED_ALLOW_IPS com o IP/rede do proxy para o uvicorn
# confiar no X-Forwarded-For (IP real do cliente na auditoria e no limite do login por TV).
CMD ["sh", "-c", "exec uvicorn app.main:app --app-dir src --host 0.0.0.0 --port ${PORT} --proxy-headers --no-server-header"]
