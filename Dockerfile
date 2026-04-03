# Kubeflow MCP Server Container
# Build: docker build -t kubeflow-mcp .
# Run:   docker run -it kubeflow-mcp serve

FROM python:3.12-slim

LABEL org.opencontainers.image.source="https://github.com/kubeflow/mcp-server"
LABEL org.opencontainers.image.description="Kubeflow MCP Server - AI interface for Kubeflow Training"
LABEL org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install dependencies
RUN uv sync --extra trainer --no-dev

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Default command
ENTRYPOINT ["uv", "run", "kubeflow-mcp"]
CMD ["serve"]
