---
applyTo: "**/*.bicep"
---

## Bicep / Azure IaC Rules
- Put reusable modules in `infra/modules`; avoid `existing` unless referencing shared resources.  
- Resource naming pattern: `{proj}{env}{region}{type}` → `stockripperdevuseastkv`.  
- Tag every resource with `owner`, `purpose`, `env`.  
- Use `@description` for every param & output; generate docs via **arm2doc**.  
- Role assignments: call the RBAC module—**never** inline `Microsoft.Authorization/roleAssignments`.  
- Enable diagnostics / logs by default; pipe to Log Analytics.  
