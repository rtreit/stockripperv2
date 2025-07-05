# StockRipper v2 Helm Deployment

This Helm chart deploys the StockRipper v2 trading system with A2A (Agent-to-Agent) protocol and MCP (Model Context Protocol) integration.

## Architecture

The system consists of:

### Agents
- **Market Analyst** (`market-analyst`): Analyzes market data using Alpaca MCP server
- **Planner** (`planner`): Creates trading plans based on analysis
- **Mailer** (`mailer`): Sends notifications via Gmail MCP server

### MCP Servers
- **Alpaca MCP** (`alpaca-mcp`): Provides market data and trading capabilities
- **Gmail MCP** (`gmail-mcp`): Handles email sending functionality

## Prerequisites

1. **Kubernetes cluster** (v1.19+)
2. **Helm 3.0+**
3. **Ingress controller** (e.g., nginx-ingress)
4. **Required credentials**:
   - OpenAI API key
   - Alpaca API credentials
   - Gmail OAuth credentials

## Installation

### 1. Prepare Secrets

First, create the required secrets:

```bash
# OpenAI API Key
kubectl create secret generic openai-secret \
  --from-literal=api-key="your-openai-api-key" \
  -n stockripper

# Alpaca API Credentials  
kubectl create secret generic alpaca-secret \
  --from-literal=api-key="your-alpaca-api-key" \
  --from-literal=secret-key="your-alpaca-secret-key" \
  -n stockripper

# Gmail OAuth Credentials
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=path/to/credentials.json \
  --from-file=token.json=path/to/token.json \
  -n stockripper
```

### 2. Install the Chart

```bash
# Add local chart repository (if needed)
helm repo add stockripper ./helm

# Install with default values
helm install stockripper-v2 ./helm \
  --namespace stockripper \
  --create-namespace

# Install with custom values
helm install stockripper-v2 ./helm \
  --namespace stockripper \
  --create-namespace \
  --values custom-values.yaml
```

### 3. Verify Deployment

```bash
# Check pod status
kubectl get pods -n stockripper

# Check services
kubectl get svc -n stockripper

# Check ingress
kubectl get ingress -n stockripper
```

## Configuration

### Environment Variables

Key configuration options in `values.yaml`:

```yaml
env:
  openai:
    model: "gpt-4o-mini"
  logging:
    level: "INFO"
    format: "json"
  a2a:
    timeout: 30
    retryAttempts: 3
```

### Image Configuration

```yaml
global:
  imageRegistry: "ghcr.io/yourusername"
  imagePullPolicy: "IfNotPresent"
```

### Resource Limits

Each component has configurable resource limits:

```yaml
marketAnalyst:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
```

## Accessing Services

### Local Development

Add to your `/etc/hosts`:

```
127.0.0.1 market-analyst.local
127.0.0.1 planner.local  
127.0.0.1 mailer.local
```

### API Endpoints

- **Market Analyst**: `http://market-analyst.local/`
- **Planner**: `http://planner.local/`
- **Mailer**: `http://mailer.local/`

### Agent Discovery

Each agent exposes A2A discovery at:
- `/.well-known/agent.json` - Agent metadata
- `/health` - Health check
- `/ready` - Readiness check

## Monitoring

Optional Prometheus monitoring:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    namespace: monitoring
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check secrets and image availability
2. **Network issues**: Verify service and ingress configuration
3. **Authentication errors**: Validate API keys and credentials

### Debug Commands

```bash
# Check pod logs
kubectl logs -f deployment/market-analyst -n stockripper

# Describe pod for events
kubectl describe pod <pod-name> -n stockripper

# Test service connectivity
kubectl port-forward svc/market-analyst 8001:8001 -n stockripper
```

## Upgrades

```bash
# Upgrade to new version
helm upgrade stockripper-v2 ./helm \
  --namespace stockripper \
  --values values.yaml

# Rollback if needed
helm rollback stockripper-v2 1 --namespace stockripper
```

## Uninstall

```bash
# Remove the release
helm uninstall stockripper-v2 --namespace stockripper

# Remove secrets (if needed)
kubectl delete secret openai-secret alpaca-secret gmail-credentials -n stockripper

# Remove namespace
kubectl delete namespace stockripper
```

## Development

### Building Images

Each agent and MCP server needs to be containerized:

```bash
# Build market analyst
docker build -t ghcr.io/yourusername/stockripper/market-analyst:1.0.0 \
  -f agents/market_analyst/Dockerfile .

# Build planner  
docker build -t ghcr.io/yourusername/stockripper/planner:1.0.0 \
  -f agents/planner/Dockerfile .

# Build mailer
docker build -t ghcr.io/yourusername/stockripper/mailer:1.0.0 \
  -f agents/mailer/Dockerfile .
```

### Local Testing

```bash
# Template validation
helm template stockripper-v2 ./helm --debug

# Dry run
helm install stockripper-v2 ./helm --dry-run --debug

# Lint chart
helm lint ./helm
```

## Security Considerations

1. **Secrets Management**: Use external secret management (e.g., External Secrets Operator)
2. **Network Policies**: Implement network segmentation
3. **RBAC**: Configure appropriate service accounts
4. **Image Security**: Use signed images and vulnerability scanning

## Support

For issues and questions:
- Check the troubleshooting section
- Review pod logs and events
- Validate configuration values
- Verify network connectivity between services

