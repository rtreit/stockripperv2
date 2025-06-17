# StockRipper v2 🚀

Advanced AI-powered trading system with distributed agent architecture using MCP (Model Context Protocol) for secure, scalable financial automation.

## 🏗️ Architecture

StockRipper v2 uses a distributed agent system with Python-based MCP servers for external integrations:

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

### 🎯 Agents (with Python MCP Servers)
- **Market Analyst** (Port 8001): Analyzes market data using Python Alpaca MCP server (stdio)
- **Planner** (Port 8002): Creates trading plans with Python Alpaca MCP server (stdio)
- **Mailer** (Port 8003): Sends notifications via Python Gmail MCP server (stdio)

### 🔗 MCP Integration (stdio)
Each agent includes Python-based MCP servers:
- **Alpaca MCP Server**: `./mcp_servers/alpaca/alpaca_mcp_server.py`
- **Gmail MCP Server**: `./mcp_servers/gmail/main.py`
- **stdio Communication**: Secure subprocess communication via stdin/stdout

### 📡 Communication
- **A2A Protocol**: HTTP-based agent-to-agent communication with discovery
- **MCP Integration**: Tool access through secure stdio subprocess communication
- **LangGraph**: State management and workflow orchestration
- **FastAPI**: RESTful endpoints and health checks

## 📁 Project Structure

```
/agents
    /base.py           # Shared A2A agent base class
    /market_analyst/   # Market analysis agent + Dockerfile
    /planner/          # Trading planner agent + Dockerfile  
    /mailer/           # Email notification agent + Dockerfile
/helm/                 # Kubernetes Helm charts
    /templates/        # K8s deployment templates
    /values.yaml       # Configuration values
    /README.md         # Deployment guide
/tests/               # Test suites
/credentials/         # OAuth and API credentials (gitignored)
config.py            # Shared configuration and logging
deploy.ps1           # Automated deployment script
validate-helm.ps1    # Helm chart validation
```

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (local or cloud)
- Helm 3.0+
- kubectl configured
- Required API credentials (OpenAI, Alpaca, Gmail)

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (local or cloud)
- Helm 3.0+
- kubectl configured
- Required API credentials (OpenAI, Alpaca, Gmail)

### 1. Validate Configuration
```powershell
# Validate Helm chart
./validate-helm.ps1

# Check cluster connectivity
kubectl cluster-info
```

### 2. Set Up Secrets
```powershell
# Create namespace
kubectl create namespace stockripper

# Create API key secrets
kubectl create secret generic openai-secret \
  --from-literal=api-key="your-openai-api-key" \
  -n stockripper

kubectl create secret generic alpaca-secret \
  --from-literal=api-key="your-alpaca-api-key" \
  --from-literal=secret-key="your-alpaca-secret-key" \
  -n stockripper
```

### 3. Deploy with Helm
```powershell
# Deploy entire system
./deploy.ps1 -Action install -Namespace stockripper

# Or deploy manually
helm install stockripper ./helm -n stockripper
```

### 4. Verify Deployment
```powershell
kubectl get pods -n stockripper
kubectl get services -n stockripper

# Test A2A discovery
kubectl port-forward service/market-analyst 8001:8001 -n stockripper
curl http://localhost:8001/.well-known/agent.json
```

## 🔧 Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template  
cp .env.example .env

# Edit .env with your credentials
```

### Build Container Images
```powershell
# Build all agent images
docker build -t stockripper/market-analyst:1.0.0 -f agents/market_analyst/Dockerfile .
docker build -t stockripper/planner:1.0.0 -f agents/planner/Dockerfile .
docker build -t stockripper/mailer:1.0.0 -f agents/mailer/Dockerfile .
```

### Run Tests
```bash
pytest tests/
```

## 🔐 Security & Credentials

⚠️ **CRITICAL SECURITY NOTICE**: Never commit real API keys or secrets to Git!

### Quick Secure Setup
```bash
# Use the secure setup script
python setup_secure.py
```

### Required Secrets
Create these Kubernetes secrets before deployment:

```bash
# OpenAI API Key
kubectl create secret generic openai-secret \
  --from-literal=api-key="your-openai-api-key" \
  -n stockripper

# Alpaca Trading API
kubectl create secret generic alpaca-secret \
  --from-literal=api-key="your-alpaca-api-key" \
  --from-literal=secret-key="your-alpaca-secret-key" \
  -n stockripper

# Gmail OAuth Credentials
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=credentials/gmail-credentials.json \
  --from-file=token.json=credentials/gmail-token.json \
  -n stockripper
```

### Credential Files
Place these files in the `credentials/` directory:
- `gmail-credentials.json` - OAuth2 client credentials from Google Cloud Console
- `gmail-token.json` - OAuth2 refresh token (generated on first auth)

See `credentials/README.md` for detailed setup instructions.

### Security Best Practices
- 📋 Read `SECURITY.md` for comprehensive security guidelines
- 🔒 Use `setup_secure.py` to configure environment safely
- 🚫 Never commit `.env` files or real credentials
- 🔄 Regularly rotate API keys and secrets
- 🔍 Review `.gitignore` patterns before committing

## License

MIT
