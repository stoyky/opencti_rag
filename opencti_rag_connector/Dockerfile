FROM python:3.11-slim
ENV CONNECTOR_TYPE=EXTERNAL_IMPORT

# Copy the connector
COPY src /opt/opencti-rag-connector
COPY enterprise-attack.json /opt/opencti-rag-connector

# Install Python modules
# hadolint ignore=DL3003
RUN apt update && apt -y upgrade && \
    apt install -y libmagic-dev libffi-dev libxml2-dev libxslt-dev

RUN cd /opt/opencti-rag-connector && \
    pip3 install --no-cache-dir -r requirements.txt
    # apk del git build-base

# Expose and entrypoint
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]