"""
Simple test to verify the Stock Research Agent works locally
"""
import asyncio
import httpx
import json

async def test_stock_research_agent():
    """Test the Stock Research Agent"""
    print("🔍 Testing Stock Research Agent...")
    
    # Test agent discovery
    async with httpx.AsyncClient() as client:
        try:
            print("📋 Checking agent discovery...")
            response = await client.get("http://localhost:8009/a2a/agent.json")
            agent_info = response.json()
            
            print(f"✅ Agent Name: {agent_info['name']}")
            print(f"✅ Description: {agent_info['description']}")
            print(f"✅ Skills Count: {len(agent_info['skills'])}")
            
            for skill in agent_info['skills']:
                print(f"   - {skill['name']}: {skill['description']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Agent test failed: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_stock_research_agent())


# Contains AI-generated edits.
