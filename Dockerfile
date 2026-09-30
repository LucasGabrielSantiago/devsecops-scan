# ---------- Etapa 1: instala dependências ----------
# nosemgrep
FROM python:3.14-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Etapa 2: imagem final enxuta ----------
# Risco aceito: a tag não é fixada por digest para receber os patches de
# segurança da imagem oficial; a imagem é reconstruída e analisada pelo
# Trivy a cada push, o que barra CVEs HIGH/CRITICAL antes do deploy.
# nosemgrep
FROM python:3.14-slim

# pip atualizado (o pip da imagem base costuma ter CVEs conhecidas)
RUN pip install --no-cache-dir --upgrade pip

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
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

CMD ["uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
