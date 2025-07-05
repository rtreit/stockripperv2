"""
Debug Market Analyst Agent to understand skill registration
"""
import os
from python_a2a import A2AServer, skill, agent, run_server

print("=== Starting debug session ===")

print("1. Testing @skill decorator on function:")

@skill(
    name="Test Stock Analysis",
    description="Test stock analysis skill",
    tags=["test"],
    examples=["Test example"]
)
def test_analyze_stock(ticker: str = "AAPL") -> str:
    return f"Analysis for {ticker}"

print(f"   test_analyze_stock has _skill_info: {hasattr(test_analyze_stock, '_skill_info')}")
if hasattr(test_analyze_stock, '_skill_info'):
    print(f"   _skill_info: {test_analyze_stock._skill_info}")

print("\n2. Testing @agent decorator on class:")

@agent(
    name="Debug Market Analyst",
    description="Debug version of market analyst",
    version="1.0.0",
    url="http://localhost:8003"
)
class DebugMarketAnalystAgent(A2AServer):
    def __init__(self):
        print("   Before super().__init__()")
        super().__init__()
        print(f"   After super().__init__(), skills: {getattr(self, 'skills', 'NO SKILLS ATTR')}")
    
    @skill(
        name="Debug Analyze Stock",
        description="Debug stock analysis",
        tags=["debug"],
        examples=["Debug analyze AAPL"]
    )
    def analyze_stock(self, ticker: str = "AAPL") -> str:
        return f"Debug analysis for {ticker}"

print("3. Creating agent instance:")
agent_instance = DebugMarketAnalystAgent()

print(f"4. Final agent skills: {getattr(agent_instance, 'skills', 'NO SKILLS ATTR')}")

# Check all attributes
print("\n5. Agent instance attributes:")
for attr in dir(agent_instance):
    if not attr.startswith('_'):
        value = getattr(agent_instance, attr)
        if callable(value) and hasattr(value, '_skill_info'):
            print(f"   {attr}: HAS _skill_info: {value._skill_info}")
        elif attr == 'skills':
            print(f"   {attr}: {value}")

print("\n6. Starting server...")
if __name__ == "__main__":
    run_server(agent_instance, host="0.0.0.0", port=8003)
