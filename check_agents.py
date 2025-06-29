#!/usr/bin/env python3
"""
Agent readiness checker tool.
Waits for all agents to be fully running and healthy before proceeding.
"""
import asyncio
import sys
import os
import httpx
import time
from datetime import datetime
from typing import List, Dict, Tuple
from config import get_settings

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class AgentChecker:
    """Tool to check if agents are running and ready."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Define all agents to check
        self.agents = [
            ("Market Analyst", self.settings.market_analyst_url),
            ("Trade Planner", self.settings.planner_url),
            ("Mailer", self.settings.mailer_url)
        ]
        
        print(f"🔍 Agent Readiness Checker")
        print(f"📊 Checking {len(self.agents)} agents...")
    
    async def check_agent_health(self, name: str, url: str) -> bool:
        """Check if a single agent is healthy."""
        try:
            response = await self.client.get(f"{url}/health")
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get("status") == "healthy"
            return False
        except Exception:
            return False
    
    async def check_agent_discovery(self, name: str, url: str) -> Dict:
        """Check agent discovery endpoint for capabilities."""
        try:
            response = await self.client.get(f"{url}/.well-known/agent.json")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception:
            return {}
    
    async def check_agent_endpoints(self, name: str, url: str) -> List[str]:
        """Check what endpoints an agent has available."""
        try:
            response = await self.client.get(f"{url}/openapi.json")
            if response.status_code == 200:
                openapi_data = response.json()
                return list(openapi_data.get("paths", {}).keys())
            return []
        except Exception:
            return []
    
    async def wait_for_agent(self, name: str, url: str, max_wait: int = 120) -> Tuple[bool, Dict]:
        """Wait for a specific agent to be ready."""
        print(f"  ⏳ Waiting for {name} at {url}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check health
            if await self.check_agent_health(name, url):
                # Get discovery info
                discovery = await self.check_agent_discovery(name, url)
                endpoints = await self.check_agent_endpoints(name, url)
                
                print(f"  ✅ {name} is ready!")
                return True, {
                    "discovery": discovery,
                    "endpoints": endpoints,
                    "ready_time": time.time() - start_time
                }
            
            # Wait a bit before retrying
            await asyncio.sleep(2)
        
        print(f"  ❌ {name} failed to start within {max_wait}s")
        return False, {}
    
    async def wait_for_all_agents(self, max_wait: int = 120) -> Dict:
        """Wait for all agents to be ready."""
        print(f"\n🚀 Waiting for all agents to be ready (max {max_wait}s)...")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        
        results = {}
        start_time = time.time()
        
        # Check each agent
        for name, url in self.agents:
            ready, info = await self.wait_for_agent(name, url, max_wait)
            results[name] = {
                "ready": ready,
                "url": url,
                "info": info
            }
            
            if not ready:
                break
        
        total_time = time.time() - start_time
        
        print(f"\n📊 AGENT READINESS SUMMARY")
        print(f"=" * 50)
        print(f"⏰ Total time: {total_time:.1f}s")
        
        all_ready = True
        for name, result in results.items():
            status = "✅ READY" if result["ready"] else "❌ FAILED"
            print(f"🤖 {name}: {status}")
            
            if result["ready"]:
                info = result["info"]
                ready_time = info.get("ready_time", 0)
                endpoints = len(info.get("endpoints", []))
                print(f"   ⏱️  Ready in: {ready_time:.1f}s")
                print(f"   🌐 Endpoints: {endpoints}")
                
                # Show key capabilities
                discovery = info.get("discovery", {})
                capabilities = discovery.get("capabilities", {})
                if capabilities:
                    key_caps = [k for k, v in capabilities.items() if v and k != "google_a2a_compatible"][:3]
                    if key_caps:
                        print(f"   ⚡ Capabilities: {', '.join(key_caps)}")
            else:
                all_ready = False
        
        return {
            "all_ready": all_ready,
            "total_time": total_time,
            "results": results
        }
    
    async def quick_health_check(self) -> bool:
        """Quick health check for all agents."""
        print(f"⚡ Quick health check...")
        
        all_healthy = True
        for name, url in self.agents:
            healthy = await self.check_agent_health(name, url)
            status = "✅" if healthy else "❌"
            print(f"  {status} {name}")
            if not healthy:
                all_healthy = False
        
        return all_healthy
    
    async def test_analyze_endpoint(self) -> bool:
        """Test the Market Analyst analyze endpoint."""
        print(f"\n🧪 Testing Market Analyst analyze endpoint...")
        
        try:
            response = await self.client.post(
                f"{self.settings.market_analyst_url}/analyze",
                json={"ticker": "AAPL"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Analyze endpoint working")
                print(f"  📈 Response: {result.get('status', 'unknown')}")
                return True
            else:
                print(f"  ❌ Analyze endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Analyze endpoint error: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main entry point."""
    checker = AgentChecker()
    
    try:
        # Quick check first
        if await checker.quick_health_check():
            print(f"✅ All agents already running!")
            
            # Test key functionality
            if await checker.test_analyze_endpoint():
                print(f"\n🎉 ALL SYSTEMS READY!")
                print(f"🚀 Agents are fully functional and ready for testing")
                return True
            else:
                print(f"\n⚠️  Agents running but analyze endpoint has issues")
                return False
        else:
            print(f"⏳ Some agents not ready, waiting...")
            
            # Wait for all to be ready
            results = await checker.wait_for_all_agents()
            
            if results["all_ready"]:
                # Test key functionality
                if await checker.test_analyze_endpoint():
                    print(f"\n🎉 ALL SYSTEMS READY!")
                    print(f"🚀 Agents are fully functional and ready for testing")
                    return True
                else:
                    print(f"\n⚠️  Agents ready but analyze endpoint has issues")
                    return False
            else:
                print(f"\n❌ Some agents failed to start")
                print(f"💡 Try starting them manually:")
                print(f"   python run_market_analyst.py")
                print(f"   python run_planner.py")
                print(f"   python run_mailer.py")
                return False
        
    finally:
        await checker.close()


if __name__ == "__main__":
    print("🔍 Agent Readiness Checker")
    print("Checking if all agents are running and ready...")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

# Contains AI-generated edits.
