---
applyTo: "**/*.cs"
---

## C# / .NET Guidelines
- Enable **nullable reference types** and treat warnings as errors.  
- Use **ILogger<>** for structured logging (Trace → Critical).  
- Dependency Injection via `IServiceCollection`.  
- Prefer **records** for immutable data containers; classes for behavior.  
- End-to-end async: `async Task` / `async ValueTask`.  
- Unit tests with **xUnit**; mocks with **Moq**.  
