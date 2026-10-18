FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl jq \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir oci-cli

WORKDIR /app
COPY oci-arm-catcher.sh entrypoint.sh ./
COPY web/ ./web/
RUN chmod +x /app/oci-arm-catcher.sh /app/entrypoint.sh && mkdir -p /data

ENV WEB_PORT=8090 STATUS_FILE=/data/status LOG_FILE=/data/catcher.log
EXPOSE 8090
ENTRYPOINT ["/app/entrypoint.sh"]
