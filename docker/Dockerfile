FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

ARG SERVER
ARG IMAGE_TITLE
ARG VERSION
ARG REVISION
ARG CREATED
ARG SOURCE_DIRTY

LABEL org.opencontainers.image.title="${IMAGE_TITLE}" \
      org.opencontainers.image.description="NEPA MCP ${SERVER} streamable HTTP server" \
      org.opencontainers.image.source="https://github.com/GSA-TTS/nepa-mcp" \
      org.opencontainers.image.url="https://github.com/GSA-TTS/nepa-mcp" \
      org.opencontainers.image.documentation="https://github.com/GSA-TTS/nepa-mcp/tree/main/docker" \
      org.opencontainers.image.licenses="BSD-3-Clause" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}" \
      gov.gsa.nepa-mcp.source-dirty="${SOURCE_DIRTY}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    HOME=/home/appuser

WORKDIR /app

COPY docker/constraints.txt docker/runtime-requirements.txt ./${SERVER}/requirements.txt /tmp/requirements/
RUN python -m pip install --no-cache-dir \
      --constraint /tmp/requirements/constraints.txt \
      --requirement "/tmp/requirements/requirements.txt" \
      --requirement /tmp/requirements/runtime-requirements.txt \
    && rm -rf /tmp/requirements \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser

COPY --chown=10001:10001 nepa_mcp ./nepa_mcp
COPY --chown=10001:10001 nepa_mcp_common ./nepa_mcp_common
COPY --chown=10001:10001 ${SERVER} ./${SERVER}
COPY --chown=10001:10001 docker/${SERVER}/entry.py ./entry.py

USER 10001:10001
EXPOSE 8080
CMD ["python", "/app/entry.py"]
