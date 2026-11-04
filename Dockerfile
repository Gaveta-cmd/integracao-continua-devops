# Imagem enxuta (alpine) para a Calculadora DevOps.
# Contrato com o desenvolvedor: `python -m src.app` sobe o servidor HTTP
# na porta definida por PORT (padrao 8080). Ver docs/A2-tarefas.md.
FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HISTORICO_PATH=/data/historico.json

# Usuario sem privilegios (nao roda como root) e pasta de dados do historico.
RUN addgroup -S -g 10001 app \
    && adduser -S -u 10001 -G app app \
    && mkdir -p /data \
    && chown app:app /data

WORKDIR /app

# Sem dependencias de runtime (so biblioteca padrao). Se o desenvolvedor
# adicionar pacotes, criar requirements.txt e copiar/instalar aqui ANTES
# do COPY do codigo, para reaproveitar o cache de camadas.
COPY src/ ./src/
COPY frontend/ ./frontend/

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- "http://127.0.0.1:${PORT}/healthz" || exit 1

CMD ["python", "-m", "src.app"]
