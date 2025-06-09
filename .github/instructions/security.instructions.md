*(security checklist for every language)*
---
applyTo: "**"
---

## Security Checklist
1. Validate input with allow-lists (Pydantic or equivalent).  
2. When shelling-out: use `shlex.quote`, never `shell=True`.  
3. Crypto: high-level `cryptography` APIs; audit any direct `hazmat` use.  
4. Run **pip-audit** in CI; block CVE severity ≥ 7.0.  
5. Add headers: HSTS, CSP, X-Content-Type-Options, etc.  
6. Pre-commit: run **gitleaks** to avoid secret leakage.  