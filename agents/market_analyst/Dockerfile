# Market Analyst Agent Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including Node.js for MCP servers
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install MCP servers via npm
RUN npm install -g @modelcontextprotocol/server-everything @modelcontextprotocol/server-filesystem

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY agents/__init__.py agents/
COPY agents/base.py agents/
COPY agents/market_analyst/ agents/market_analyst/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run the application
CMD ["python", "-m", "agents.market_analyst.main"]

# Contains AI-generated edits.
