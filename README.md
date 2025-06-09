# StockRipper v2

Scaffolding for a multi-agent trading assistant composed of three agents:
MarketAnalyst, Planner and Mailer. Each agent will run in its own container and
communicate via the A2A protocol as described in `HighLevelSpec.md`.

## Layout

```
/agents
    /market_analyst
    /planner
    /mailer
/helm
/tests
```

## Development

Install dependencies with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install -r requirements.txt --system
```

Then run the test suite:

```bash
pytest
```

## Secrets

API keys for Alpaca and Gmail are provided to the cluster via Kubernetes
`Secret` manifests. Charts in `helm/` reference these secrets; create them prior
to installation:

```bash
kubectl create secret generic alpaca-creds --from-literal=key=YOURKEY
kubectl create secret generic gmail-creds --from-literal=token=YOURTOKEN
```

## License

MIT
