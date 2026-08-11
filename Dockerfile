FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    TRANSPORT=stdio \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# Install dependencies first (better layer caching)
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy the MCP server and the vendored search agent
COPY server/ server/

EXPOSE 8000

ENTRYPOINT ["python", "server/mcp_server.py"]
