---
applyTo: "**"
---

# Randy's Global Coding Playbook

Follow these rules for any code you **generate, review, or refactor** in this workspace.

## Core Philosophy
- **Security-first**: safe defaults, least privilege, constant-time comparisons, never store plaintext secrets.  
- **Functional over OO**: prefer pure functions & immutable data; use classes only when unavoidable.  
- **Readability > Cleverness**: clarity beats micro-optimisation.  
- **Automation mindset**: if you do it twice, script it (CLI, CI, IaC).  
- **Think loud, fail fast**: pseudocode → PoC → iterate; surface errors early with explicit logging & typed contracts.  

## General Style
- Strict typing, linting, and formatting (`ruff`, `mypy --strict`, `black --line-length 100`).  
- All config via env vars, parsed once with **Pydantic v2 Settings**.  
- Use **structlog** for JSON logs in prod, pretty logs in dev.  
- Never leak stack traces; propagate **X-Correlation-Id**.  

## Response Expectations
When I ask for code:  
1. Produce a complete, runnable snippet.  
2. Comment *why*, not *what*.  
3. Include test stubs **only** if I ask for tests.  
4. Append the line `# Contains AI-generated edits.` at EOF.  
