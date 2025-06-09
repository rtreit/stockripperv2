# Security Checklist for StockRipper A2A/MCP Deployment

## ⚠️ CRITICAL: Never Commit Secrets to Git

### Pre-Commit Security Checks

Before committing any code, ensure:

1. **No hardcoded API keys, tokens, or secrets in code**
2. **All sensitive configuration uses environment variables**
3. **No actual credentials in `.vscode/mcp.json` or similar config files**
4. **No real values in `.env` files (use `.env.example` only)**
5. **No credential files in the repository**

### Files That Must Never Contain Real Secrets

- ❌ `.vscode/mcp.json` - Use placeholder values only
- ❌ `.env` - Should not exist in repo (use `.env.example`)
- ❌ `config.py` - Should only reference environment variables
- ❌ Any `*.yaml` files in `helm/` - Use template variables only
- ❌ `rendered-templates.yaml` - Generated file, should be in `.gitignore`
- ❌ Any files in `credentials/` directory

### Secure Configuration Pattern

✅ **Correct approach:**
```python
# config.py
openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
```

❌ **Never do this:**
```python
# config.py
openai_api_key = "sk-real-api-key-here"  # NEVER!
```

### Environment Variable Management

1. **Development:**
   - Copy `.env.example` to `.env`
   - Add real values to `.env` (git-ignored)
   - Never commit `.env`

2. **Production/Kubernetes:**
   - Use Kubernetes Secrets
   - Set environment variables in deployment
   - Use Helm values files with templates

3. **Testing:**
   - Use mock values or test-specific environment
   - Never use production credentials in tests

### API Key Security

- **OpenAI/Anthropic:** Start with `sk-` - extremely sensitive
- **Alpaca:** Trading API keys - financial risk if exposed
- **Gmail:** OAuth tokens - email access risk
- **GitHub:** Personal access tokens - code repository access

### Kubernetes/Helm Security

1. **Create secrets manually:**
   ```bash
   kubectl create secret generic openai-secret --from-literal=api-key=your-real-key
   ```

2. **Use sealed secrets or external secret operators for production**

3. **Never put real secrets in `values.yaml`**

### Pre-Deployment Checklist

- [ ] All API keys stored as Kubernetes secrets
- [ ] Environment variables properly configured
- [ ] No secrets in container images
- [ ] Network policies configured for agent communication
- [ ] TLS/HTTPS enabled for all endpoints
- [ ] RBAC configured with least privilege
- [ ] Monitoring and logging configured (without logging secrets)

### Git Security Commands

```bash
# Check for potential secrets before committing
git diff --staged | grep -i -E "(api[_-]?key|secret|password|token)"

# Remove file from git history if accidentally committed
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secret/file' \
  --prune-empty --tag-name-filter cat -- --all
```

### Emergency Response

If secrets are accidentally committed:

1. **Immediately revoke/regenerate the exposed credentials**
2. **Remove from git history using `git filter-branch` or BFG Repo-Cleaner**
3. **Force push to overwrite history (coordinate with team)**
4. **Update all deployment configurations**
5. **Audit logs for any unauthorized access**

### Regular Security Maintenance

- **Monthly:** Rotate API keys and secrets
- **Weekly:** Review access logs and monitoring
- **Daily:** Check for new security advisories for dependencies
- **Per-deployment:** Validate no secrets in logs or error messages

## Tools for Secret Detection

- **git-secrets:** Prevents committing secrets to Git
- **truffleHog:** Scans git history for secrets
- **detect-secrets:** Pre-commit hook for secret detection
- **GitGuardian:** Automated secret scanning

## Configuration Security

### VS Code MCP Configuration
- Copy `.vscode/mcp.json.template` to `.vscode/mcp.json`
- Fill in your real API keys in the copied file
- Never commit the real `mcp.json` file (it's in `.gitignore`)

### GitHub and VS Code Folders
The following folders may contain sensitive information and are excluded from git:
- `.vscode/` - VS Code settings that may contain API keys
- `.github/secrets/` - GitHub secrets (if created locally)
- `.github/personal/` - Personal GitHub configurations
- `.github/local/` - Local GitHub configurations

# Contains AI-generated edits.
