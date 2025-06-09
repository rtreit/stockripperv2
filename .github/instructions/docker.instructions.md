---
applyTo: "Dockerfile*"
---

## Dockerfile Standards
- Base image: `python:3.11-slim`; create venv in `/opt/venv`.  
- Multi-stage build: `builder` installs build deps, `final` only wheels & code.  
- Never run as root → create `app:app` (UID 1001).  
- Pin OS packages then `rm -rf /var/lib/apt/lists/*`.  
- Add health probe:  
  `HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1`  
- Use OCI labels (`org.opencontainers.image.*`) for provenance.  
