# ---------- Etapa 1: instala dependências ----------
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Etapa 2: imagem final enxuta ----------
FROM python:3.12-slim

# Atualiza pacotes do SO para reduzir CVEs detectadas pelo Trivy
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Usuário sem privilégios (o container não roda como root)
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=build /install /usr/local
COPY --chown=appuser:appuser src/ ./src/

USER appuser
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/home/appuser/tarefas.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
