# StockRipper v2 Local Development Guide

This guide explains how to set up and run StockRipper v2 agents locally for development and testing.

## Quick Start

### 1. Initial Setup

```bash
# Install dependencies and set up environment
python setup_local_dev.py

# Validate configuration
python validate_local.py
```

### 2. Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API credentials:
   ```bash
   # Required for Alpaca trading
   ALPACA_API_KEY=your_actual_alpaca_api_key
   ALPACA_SECRET_KEY=your_actual_alpaca_secret_key
   
   # Required for OpenAI/LLM
   OPENAI_API_KEY=your_actual_openai_api_key
   ```

### 3. Set Up Gmail (Optional)

For email notifications via Gmail:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download JSON and save as `./credentials/gmail_credentials.json`

### 4. Test MCP Servers

```bash
# Test MCP server connectivity
python test_mcp_servers.py
```

### 5. Run Individual Agents

```bash
# Run Market Analyst (port 8001)
python run_market_analyst.py

# Run Planner (port 8002) 
python run_planner.py

# Run Mailer (port 8003)
python run_mailer.py
```

## Architecture Overview

StockRipper v2 uses a distributed agent architecture with MCP (Model Context Protocol) servers:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Market Analyst │    │     Planner     │    │     Mailer      │
│   (Port 8001)   │    │   (Port 8002)   │    │   (Port 8003)   │
│                 │    │                 │    │                 │
│  Uses: Alpaca   │    │  Uses: Alpaca   │    │  Uses: Gmail    │
│  MCP Server     │    │  MCP Server     │    │  MCP Server     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  A2A Registry   │
                    │  (Port 8000)    │
                    └─────────────────┘
```

## MCP Servers

### Alpaca MCP Server
- **Location**: `./mcp_servers/alpaca/`
- **Purpose**: Stock trading, market data, portfolio management
- **Communication**: stdio (JSON-RPC over stdin/stdout)
- **Used by**: Market Analyst, Planner

### Gmail MCP Server  
- **Location**: `./mcp_servers/gmail/`
- **Purpose**: Email notifications, trade alerts
- **Communication**: stdio (JSON-RPC over stdin/stdout)
- **Used by**: Mailer

## Agent Details

### Market Analyst Agent
- **Port**: 8001
- **Purpose**: Analyze stocks, market conditions, technical indicators
- **MCP Tools**: Alpaca trading data, market research
- **Endpoints**:
  - `GET /.well-known/agent.json` - Agent discovery
  - `GET /health` - Health check
  - `POST /analyze` - Stock analysis

### Planner Agent
- **Port**: 8002
- **Purpose**: Create trading plans, risk management, order execution
- **MCP Tools**: Alpaca trading, portfolio management
- **Endpoints**:
  - `GET /.well-known/agent.json` - Agent discovery
  - `GET /health` - Health check
  - `POST /plan` - Create trading plan

### Mailer Agent
- **Port**: 8003
- **Purpose**: Send email notifications about trades and alerts
- **MCP Tools**: Gmail sending, composition
- **Endpoints**:
  - `GET /.well-known/agent.json` - Agent discovery
  - `GET /health` - Health check
  - `POST /send-email` - Send notification

## Development Workflow

### 1. Code Changes
Make changes to agent code in `agents/*/main.py`

### 2. Quick Validation
```bash
python validate_local.py
```

### 3. Test MCP Connectivity
```bash
python test_mcp_servers.py
```

### 4. Run Specific Agent
```bash
python run_market_analyst.py  # or run_planner.py, run_mailer.py
```

### 5. Test Agent Endpoints
```bash
# Health check
curl http://localhost:8001/health

# Agent discovery
curl http://localhost:8001/.well-known/agent.json

# Agent-specific endpoint
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "analysis_type": "technical"}'
```

## Configuration Files

### `.env`
Main environment configuration:
- API keys (Alpaca, OpenAI, Gmail)
- Agent URLs and ports
- Logging configuration

### `config.py`
Pydantic settings model that loads from `.env`:
- Type validation
- Default values
- Environment variable mapping

### MCP Server Config
Each agent configures its MCP servers in the constructor:

```python
mcp_servers = {
    "alpaca": {
        "command": "python",
        "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
        "env": {
            "ALPACA_API_KEY": settings.alpaca_api_key,
            "ALPACA_SECRET_KEY": settings.alpaca_secret_key,
            # ...
        }
    }
}
```

## Troubleshooting

### Agent Won't Start
1. Check environment variables: `python validate_local.py`
2. Verify MCP servers: `python test_mcp_servers.py`
3. Check port conflicts: `netstat -an | findstr :8001`

### MCP Server Issues
1. Check script exists: `ls mcp_servers/alpaca/alpaca_mcp_server.py`
2. Test Python execution: `python mcp_servers/alpaca/alpaca_mcp_server.py`
3. Check dependencies: `pip install -r requirements.txt`

### Gmail Setup Issues
1. Verify credentials file: `ls credentials/gmail_credentials.json`
2. Check Google Cloud Console OAuth2 setup
3. Ensure Gmail API is enabled

### Network Issues
1. Check firewall settings for ports 8001-8003
2. Verify localhost accessibility
3. Check Windows Defender/antivirus blocking

## Production Deployment

For production deployment on Kubernetes, see:
- [HELM_DEPLOYMENT.md](HELM_DEPLOYMENT.md) - Kubernetes/Helm deployment
- [SECURITY.md](SECURITY.md) - Security considerations
- [Dockerfile](Dockerfile) - Container configuration

## A2A Protocol

StockRipper v2 implements the A2A (Agent-to-Agent) protocol for inter-agent communication:

- **Discovery**: Agents expose `/.well-known/agent.json` endpoints
- **Communication**: JSON-RPC over HTTP
- **Capabilities**: Each agent declares its capabilities
- **Registry**: Optional central registry for agent discovery

Example agent discovery:
```json
{
  "name": "Market Analyst",
  "url": "http://localhost:8001",
  "version": "1.0.0",
  "capabilities": [
    "stock_analysis",
    "market_research", 
    "technical_analysis"
  ],
  "endpoints": [...]
}
```

## Contributing

1. Make changes to agent code
2. Run validation: `python validate_local.py`
3. Test MCP connectivity: `python test_mcp_servers.py`
4. Test individual agents
5. Update tests if needed
6. Submit PR with description

## Support

For issues:
1. Check this guide first
2. Run diagnostic scripts
3. Check logs in agent output
4. Create issue with details

# Contains AI-generated edits.
