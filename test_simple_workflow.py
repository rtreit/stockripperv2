#!/usr/bin/env python3
"""
Simple HTTP-based test to verify the A2A agent workflow works.
This test simulates market data input and verifies agent responses.
"""
import asyncio
import sys
import os
import httpx
import json
from datetime import datetime
from config import get_settings

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class SimpleWorkflowTest:
    """Simple test client using HTTP to verify agent functionality."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=60.0)
        print(f"🎯 Simple A2A Agent Workflow Test")
        print(f"📧 Email recipient: {self.settings.default_email_recipient}")
    
    async def test_all_agents_health(self) -> bool:
        """Check if all agents are running."""
        agents = [
            ("Market Analyst", self.settings.market_analyst_url),
            ("Planner", self.settings.planner_url),
            ("Mailer", self.settings.mailer_url)
        ]
        
        all_healthy = True
        for name, url in agents:
            try:
                response = await self.client.get(f"{url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ {name} is healthy: {health_data}")
                else:
                    print(f"❌ {name} unhealthy: {response.status_code}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ Cannot connect to {name}: {e}")
                all_healthy = False
        
        return all_healthy
    
    async def test_market_analyst_analysis(self) -> bool:
        """Test Market Analyst analysis capabilities."""
        print("\n📊 Testing Market Analyst Analysis...")
        
        try:
            # Test the analyze endpoint
            response = await self.client.post(
                f"{self.settings.market_analyst_url}/analyze",
                json={"ticker": "AAPL"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Market Analyst analysis successful")
                print(f"📈 Analysis result: {result.get('analysis', 'No analysis')[:100]}...")
                return True
            else:
                print(f"❌ Market Analyst analysis failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Market Analyst test failed: {e}")
            return False
    
    async def test_planner_planning(self) -> bool:
        """Test Planner planning capabilities."""
        print("\n📋 Testing Trade Planner...")
        
        try:
            # Test the plan endpoint
            response = await self.client.post(
                f"{self.settings.planner_url}/plan",
                json={
                    "ticker": "AAPL",
                    "action": "buy",
                    "analysis": "Strong bullish signal with high volume"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Trade Planner successful")
                print(f"📋 Plan result: {result.get('plan', 'No plan')[:100]}...")
                return True
            else:
                print(f"❌ Trade Planner failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Trade Planner test failed: {e}")
            return False
    
    async def test_mailer_email(self) -> bool:
        """Test Mailer email capabilities."""
        print("\n📧 Testing Mailer Email Sending...")
        
        test_email_data = {
            "to": self.settings.default_email_recipient,
            "subject": "StockRipper A2A Workflow Test",
            "body": f"""
📊 Test Email from StockRipper A2A Workflow

This test email was sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 
to verify the email delivery system is working.

🤖 System: StockRipper v2 Multi-Agent Workflow
📬 Recipient: {self.settings.default_email_recipient}

If you receive this email, the workflow system is functioning correctly!
            """.strip()
        }
        
        try:
            response = await self.client.post(
                f"{self.settings.mailer_url}/send-email",
                json=test_email_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mailer email sent successfully")
                print(f"📧 Email result: {result}")
                return True
            else:
                print(f"❌ Mailer email failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Mailer test failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Run simple workflow tests."""
    print("🚀 Simple A2A Agent Workflow Test")
    print("=" * 50)
    print("This test verifies each agent works independently")
    print()
    
    client = SimpleWorkflowTest()
    
    try:
        # Health check for all agents
        if not await client.test_all_agents_health():
            print("\n❌ Some agents are not running. Start them with:")
            print("   python run_market_analyst.py")
            print("   python run_planner.py") 
            print("   python run_mailer.py")
            return False
        
        # Test each agent individually
        print("\n🎯 Testing individual agent capabilities...")
        
        analyst_success = await client.test_market_analyst_analysis()
        planner_success = await client.test_planner_planning()
        mailer_success = await client.test_mailer_email()
        
        # Results
        print("\n" + "=" * 50)
        print("📊 SIMPLE WORKFLOW TEST RESULTS")
        print("=" * 50)
        print(f"📊 Market Analyst: {'✅ PASSED' if analyst_success else '❌ FAILED'}")
        print(f"📋 Trade Planner: {'✅ PASSED' if planner_success else '❌ FAILED'}")
        print(f"📧 Mailer: {'✅ PASSED' if mailer_success else '❌ FAILED'}")
        
        all_passed = analyst_success and planner_success and mailer_success
        
        if all_passed:
            print(f"\n🎉 ALL AGENT TESTS PASSED!")
            print(f"📧 Check {client.settings.default_email_recipient} for test email")
            print(f"🔄 Next: Test full A2A inter-agent communication")
        else:
            print(f"\n⚠️  Some agent tests failed. Check agent logs.")
        
        return all_passed
        
    finally:
        await client.close()


if __name__ == "__main__":
    print("🔬 Simple Agent Workflow Testing")
    print("Make sure all agents are running first!")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

# Contains AI-generated edits.
