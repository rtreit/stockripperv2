# Helm Deployment Guide for StockRipper v2

This guide explains how to deploy the A2A-compliant StockRipper agents using Helm instead of Docker Compose.

## Prerequisites

- Kubernetes cluster (local or cloud)
- Helm 3.x installed
- kubectl configured for your cluster
- Docker images built and pushed to a registry

## Quick Start

### 1. Build and Push Images

```powershell
# Build all agent images
docker build -t stockripper/market-analyst:1.0.0 -f agents/market_analyst/Dockerfile .
docker build -t stockripper/planner:1.0.0 -f agents/planner/Dockerfile .
docker build -t stockripper/mailer:1.0.0 -f agents/mailer/Dockerfile .

# Build MCP server images (you'll need to create these)
docker build -t stockripper/alpaca-mcp:1.0.0 -f mcp-servers/alpaca/Dockerfile .
docker build -t stockripper/gmail-mcp:1.0.0 -f mcp-servers/gmail/Dockerfile .

# Push to your registry
docker push ghcr.io/yourusername/stockripper/market-analyst:1.0.0
docker push ghcr.io/yourusername/stockripper/planner:1.0.0
docker push ghcr.io/yourusername/stockripper/mailer:1.0.0
docker push ghcr.io/yourusername/stockripper/alpaca-mcp:1.0.0
docker push ghcr.io/yourusername/stockripper/gmail-mcp:1.0.0
```

### 2. Create Namespace

```powershell
kubectl create namespace stockripper
```

### 3. Set Up Secrets

Create secrets for API keys and credentials:

```powershell
# OpenAI API Key
kubectl create secret generic openai-secret \
  --from-literal=api-key="your-openai-api-key" \
  -n stockripper

# Alpaca Trading API
kubectl create secret generic alpaca-secret \
  --from-literal=api-key="your-alpaca-api-key" \
  --from-literal=secret-key="your-alpaca-secret-key" \
  -n stockripper

# Gmail credentials (if using Gmail MCP)
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=./credentials/gmail_credentials.json \
  --from-file=token.json=./credentials/gmail_token.json \
  -n stockripper
```

### 4. Update Values

Copy the values template and customize:

```powershell
cp helm/values.yaml helm/values-production.yaml
```

Edit `helm/values-production.yaml` to update:
- Image registry URLs
- API endpoints
- Resource limits
- Ingress hosts

### 5. Deploy with Helm

```powershell
# Deploy to Kubernetes
helm install stockripper ./helm -f helm/values-production.yaml -n stockripper

# Or upgrade existing deployment
helm upgrade stockripper ./helm -f helm/values-production.yaml -n stockripper
```

## Configuration

### Environment Variables

The deployment uses the following environment variables (set via Helm values):

#### Global Settings
- `OPENAI_API_KEY`: OpenAI API key (from secret)
- `OPENAI_MODEL`: LLM model to use (default: gpt-4o-mini)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format (default: json)

#### Agent URLs
- `MARKET_ANALYST_URL`: Market Analyst service URL
- `PLANNER_URL`: Planner service URL  
- `MAILER_URL`: Mailer service URL

#### MCP Servers
- `ALPACA_MCP_URL`: Alpaca MCP server URL
- `GMAIL_MCP_SERVER_URL`: Gmail MCP server URL

#### Trading (Alpaca)
- `ALPACA_API_KEY`: Alpaca API key (from secret)
- `ALPACA_SECRET_KEY`: Alpaca secret key (from secret)
- `ALPACA_BASE_URL`: Alpaca API endpoint

#### Email (Gmail)
- `GMAIL_CLIENT_ID`: Gmail OAuth client ID
- `GMAIL_CLIENT_SECRET`: Gmail OAuth client secret
- `DEFAULT_EMAIL_RECIPIENT`: Default email recipient

### Helm Values Structure

```yaml
global:
  namespace: stockripper
  imageRegistry: ghcr.io/yourusername
  imagePullPolicy: IfNotPresent

marketAnalyst:
  enabled: true
  replicaCount: 1
  image:
    repository: stockripper/market-analyst
    tag: "1.0.0"
  service:
    port: 8001
  ingress:
    enabled: true
    hosts:
      - host: market-analyst.example.com

planner:
  enabled: true
  # ... similar structure

mailer:
  enabled: true
  # ... similar structure

mcpServers:
  alpaca:
    enabled: true
    # ... MCP server config
  gmail:
    enabled: true
    # ... MCP server config
```

## Networking

### Service Discovery

Each agent exposes:
- **HTTP API**: A2A endpoints on port 8001-8003
- **Discovery**: `/.well-known/agent.json` for A2A discovery
- **Health**: `/health` for health checks

### Ingress

Ingress controllers route external traffic:
- `market-analyst.example.com` → Market Analyst
- `planner.example.com` → Planner
- `mailer.example.com` → Mailer

### Internal Communication

Agents communicate via Kubernetes services:
- `market-analyst:8001`
- `planner:8002`
- `mailer:8003`
- `alpaca-mcp:9001`
- `gmail-mcp:9002`

## Monitoring

### Health Checks

Each pod includes:
- **Liveness probe**: `/health` endpoint
- **Readiness probe**: `/ready` endpoint
- **Startup probe**: For slow-starting containers

### Logs

Structured JSON logs are available via:

```powershell
# View logs for specific agent
kubectl logs -f deployment/market-analyst -n stockripper

# View all agent logs
kubectl logs -f -l app.kubernetes.io/name=stockripper -n stockripper
```

### Metrics (Optional)

Enable Prometheus monitoring:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

## Scaling

### Horizontal Scaling

Scale agents based on load:

```powershell
# Scale market analyst to 3 replicas
kubectl scale deployment market-analyst --replicas=3 -n stockripper

# Or via Helm values
helm upgrade stockripper ./helm --set marketAnalyst.replicaCount=3 -n stockripper
```

### Resource Management

Set resource requests and limits:

```yaml
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```powershell
   kubectl describe pod <pod-name> -n stockripper
   ```

2. **Secret Access**
   ```powershell
   kubectl get secrets -n stockripper
   kubectl describe secret openai-secret -n stockripper
   ```

3. **Service Connectivity**
   ```powershell
   kubectl get services -n stockripper
   kubectl port-forward service/market-analyst 8001:8001 -n stockripper
   ```

4. **Check A2A Discovery**
   ```powershell
   curl http://localhost:8001/.well-known/agent.json
   ```

### Debug Commands

```powershell
# Check all resources
kubectl get all -n stockripper

# Describe problematic pods
kubectl describe pod <pod-name> -n stockripper

# Check ingress
kubectl get ingress -n stockripper

# View Helm status
helm status stockripper -n stockripper

# Check Helm values
helm get values stockripper -n stockripper
```

## Uninstall

To remove the deployment:

```powershell
# Uninstall Helm release
helm uninstall stockripper -n stockripper

# Delete namespace (optional)
kubectl delete namespace stockripper
```

## Migration from Docker Compose

If migrating from Docker Compose:

1. **Export environment variables** from `.env` to Kubernetes secrets
2. **Convert volumes** to PersistentVolumeClaims if needed
3. **Update networking** from container names to Kubernetes services
4. **Configure ingress** for external access
5. **Set up monitoring** and logging aggregation

## Security Considerations

- Store sensitive data in Kubernetes secrets, not ConfigMaps
- Use RBAC to limit pod permissions
- Configure network policies for pod-to-pod communication
- Regularly update base images for security patches
- Use non-root containers when possible

# Contains AI-generated edits.
