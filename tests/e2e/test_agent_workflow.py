#!/usr/bin/env python3
"""
Working A2A workflow test using the existing analyze endpoint.
This test uses the endpoints that are actually available and working.
"""
import asyncio
import sys
import os
import httpx
import json
from datetime import datetime

# Add project root to Python path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_settings


class WorkingA2ATest:
    """Test using the actual working endpoints."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=60.0)
        print(f"🎯 Working A2A Workflow Test")
        print(f"📧 Email recipient: {self.settings.default_email_recipient}")
    
    async def test_working_market_analysis(self) -> bool:
        """Test the working analyze endpoint that we can see in the logs."""
        print("\n📊 Testing Working Market Analysis...")
        
        # Test different market scenarios
        scenarios = [
            {"ticker": "AAPL", "scenario": "Strong Buy Signal"},
            {"ticker": "TSLA", "scenario": "Sell Signal"}, 
            {"ticker": "MSFT", "scenario": "Hold Signal"}
        ]
        
        all_success = True
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📈 Scenario {i}: {scenario['scenario']} - {scenario['ticker']}")
            
            try:
                # Call the analyze endpoint that we know exists and works
                response = await self.client.post(
                    f"{self.settings.market_analyst_url}/analyze",
                    json=scenario
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ Market Analyst responded: {result.get('status', 'unknown')}")
                    
                    # Display any analysis if available
                    if 'analysis' in result:
                        analysis = result['analysis']
                        if isinstance(analysis, str) and len(analysis) > 0:
                            print(f"  📈 Analysis: {analysis[:100]}...")
                        else:
                            print(f"  📈 Analysis result: {analysis}")
                    
                    print(f"  ⏳ Waiting 5 seconds for A2A workflow to complete...")
                    await asyncio.sleep(5)  # Allow time for A2A communication
                    
                else:
                    print(f"  ❌ Analysis failed: {response.status_code} - {response.text}")
                    all_success = False
                    
            except Exception as e:
                print(f"  ❌ Scenario failed: {e}")
                all_success = False
        
        return all_success
    
    async def test_mailer_trade_notification(self) -> bool:
        """Test the Mailer's trade-notification endpoint."""
        print("\n📧 Testing Mailer Trade Notification...")
        
        trade_plan = {
            "symbol": "AAPL",
            "action": "BUY",
            "price": "$175.50",
            "analysis": "Strong bullish breakout with high volume confirmation",
            "timestamp": datetime.now().isoformat(),
            "recommendation": "STRONG BUY",
            "target_price": "$195.00",
            "stop_loss": "$162.00"
        }
        
        try:
            response = await self.client.post(
                f"{self.settings.mailer_url}/trade-notification",
                json={"trade_plan": trade_plan}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Mailer responded: {result}")
                print(f"  📧 Email should be sent to {self.settings.default_email_recipient}")
                return True
            else:
                print(f"  ❌ Mailer failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"  ❌ Mailer test failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Run working A2A workflow tests."""
    print("🚀 Working A2A Workflow Test")
    print("=" * 50)
    print("Testing the endpoints that are actually working")
    print()
    
    client = WorkingA2ATest()
    
    try:
        # Test market analysis workflow
        print("🎯 Testing Market Analysis Workflow...")
        analysis_success = await client.test_working_market_analysis()
        
        # Test direct email notification
        print("🎯 Testing Direct Email Notification...")
        email_success = await client.test_mailer_trade_notification()
        
        # Results
        print("\n" + "=" * 50)
        print("📊 WORKING A2A TEST RESULTS")
        print("=" * 50)
        print(f"📊 Market Analysis: {'✅ PASSED' if analysis_success else '❌ FAILED'}")
        print(f"📧 Email Notification: {'✅ PASSED' if email_success else '❌ FAILED'}")
        
        all_passed = analysis_success and email_success
        
        if all_passed:
            print(f"\n🎉 TESTS PASSED!")
            print(f"📧 Check {client.settings.default_email_recipient} for emails")
            print(f"🔄 The A2A workflow should be working automatically")
        else:
            print(f"\n⚠️  Some tests failed. Check agent logs.")
        
        return all_passed
        
    finally:
        await client.close()


if __name__ == "__main__":
    print("🔬 Working A2A Workflow Testing")
    print("Testing the actual working endpoints!")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

