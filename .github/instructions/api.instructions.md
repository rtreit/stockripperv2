---
applyTo: "**/*.py"
---

## FastAPI Design Rules
1. Prefix all paths with `/api/v1/`.  
2. Use plural nouns for resources, verbs for actions (`/hive/{id}/weight:refresh`).  
3. On successful create: return **201 Created** and `Location` header.  
4. Standard error payload:
```json
{ "error_code": "STR_ID", "message": "Human readable", "details": {} }
5. Auth via AAD bearer tokens; fallback to PAT for GitHub MCP.

## Error Handling & Resilience
* No bare except:—catch specific exceptions.
* Wrap external calls → log context, classify, retry if transient.
* Respond 5xx only for server faults; 4xx for caller errors.
* Never leak stack traces; propagate X-Correlation-Id header.

yaml
Copy
Edit
