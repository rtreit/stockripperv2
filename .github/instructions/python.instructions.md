---
applyTo: "**/*.py"
---

## Python Code Style & Libraries
| Aspect        | Guideline |
| --------------|-----------|
| Target ver    | **Python ≥ 3.11** + `from __future__ import annotations` |
| Formatting    | `black --line-length 100` |
| Lint / typing | `ruff` («ANN*», forbid `print`, wildcard imports, allow long test names) · `mypy --strict` |
| Naming        | `snake_case`, `UPPER_CASE`, rare `PascalCase` classes |
| Strings       | single-quotes; f-strings; triple-quoted docs |
| Type hints    | mandatory everywhere; use `typing.Annotated` for constraints |
| Validation    | **Pydantic v2 BaseModel** for any external input |
| Tests         | `pytest` + `pytest-asyncio`; long descriptive names OK |

### Preferred Libraries
- HTTP → **httpx.AsyncClient** (30 s timeout, tenacity retries)  
- Web API → **FastAPI** with strict Pydantic models, routers per domain  
- Background tasks < 30 s → async; > 30 s → **Celery** + Redis  
- Data ops → pandas / polars (avoid heavy libs in serverless)  
- LLM → LangChain ≥ 0.3 (LangGraph nodes) or Semantic Kernel  
- Logging → **structlog** (JSON prod, pretty dev)  
- Circuit breaker → `asyncio-circuitbreaker`

### Concurrency & Performance
- `async def` + `await` everywhere—never block the loop.  
- CPU-bound ➜ `ThreadPoolExecutor` or worker process.  
- Batch outbound calls (LLM embeddings, HTTP).  
- Memory-map large files; avoid loading full datasets into driver.  
- Profile first with **scalene** or **perf** before tuning.  
