#!/usr/bin/env python3
"""
Comprehensive end-to-end test for the StockRipper multi-agent workflow.
Tests the full pipeline: Market Analyst → Trade Planner → Mailer
"""
import asyncio
import sys
import os
import httpx
from datetime import datetime
from config import get_settings

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class E2EWorkflowTest:
    """End-to-end workflow tester for the multi-agent system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_ticker = "AAPL"
        
        print("🧪 StockRipper End-to-End Workflow Test")
        print("=" * 50)
        print(f"📊 Test ticker: {self.test_ticker}")
        print(f"📧 Email recipient: {self.settings.default_email_recipient}")
        print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
        print()
    
    async def test_market_analyst(self) -> dict:
        """Test the Market Analyst agent"""
        print("🔍 Step 1: Testing Market Analyst...")
        
        try:
            response = await self.client.post(
                f"{self.settings.market_analyst_url}/analyze",
                json={"ticker": self.test_ticker}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Market analysis completed")
                print(f"  📈 Status: {result.get('status', 'unknown')}")
                analysis_preview = str(result.get('analysis', ''))[:100] + "..."
                print(f"  📄 Analysis preview: {analysis_preview}")
                return result
            else:
                print(f"  ❌ Market analysis failed: HTTP {response.status_code}")
                print(f"  📄 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Market analysis error: {e}")
            return None
    
    async def test_trade_planner(self, analysis: str) -> dict:
        """Test the Trade Planner agent"""
        print("\n📋 Step 2: Testing Trade Planner...")
        
        try:
            response = await self.client.post(
                f"{self.settings.planner_url}/plan",
                json={
                    "ticker": self.test_ticker,
                    "action": "buy",
                    "analysis": analysis
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Trade planning completed")
                print(f"  📊 Status: {result.get('status', 'unknown')}")
                plan_preview = str(result.get('plan', ''))[:100] + "..."
                print(f"  📋 Plan preview: {plan_preview}")
                return result
            else:
                print(f"  ❌ Trade planning failed: HTTP {response.status_code}")
                print(f"  📄 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Trade planning error: {e}")
            return None
    
    async def test_mailer(self, analysis: str, plan: str) -> dict:
        """Test the Mailer agent"""
        print("\n📧 Step 3: Testing Mailer (REAL EMAIL)...")
        
        try:
            response = await self.client.post(
                f"{self.settings.mailer_url}/send_notification",
                json={
                    "ticker": self.test_ticker,
                    "analysis": analysis,
                    "plan": plan,
                    "notification_type": "trade_analysis"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Email sent successfully!")
                print(f"  📧 Status: {result.get('status', 'unknown')}")
                print(f"  📮 Recipient: {self.settings.default_email_recipient}")
                
                # Show email details if available
                if 'email_details' in result:
                    details = result['email_details']
                    print(f"  📄 Subject: {details.get('subject', 'N/A')}")
                    print(f"  🆔 Message ID: {details.get('message_id', 'N/A')}")
                
                return result
            else:
                print(f"  ❌ Email sending failed: HTTP {response.status_code}")
                print(f"  📄 Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Email sending error: {e}")
            return None
    
    async def test_full_workflow(self) -> bool:
        """Test the complete workflow"""
        print("🚀 Running Complete Multi-Agent Workflow...")
        print()
        
        # Step 1: Market Analysis
        analysis_result = await self.test_market_analyst()
        if not analysis_result:
            return False
        
        analysis = analysis_result.get('analysis', '')
        if not analysis:
            print("  ❌ No analysis content received")
            return False
        
        # Step 2: Trade Planning
        plan_result = await self.test_trade_planner(analysis)
        if not plan_result:
            return False
        
        plan = plan_result.get('plan', '')
        if not plan:
            print("  ❌ No plan content received")
            return False
        
        # Step 3: Email Notification
        email_result = await self.test_mailer(analysis, plan)
        if not email_result:
            return False
        
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("✅ Market analysis generated")
        print("✅ Trade plan created")
        print("✅ Email notification sent")
        print(f"📧 Check {self.settings.default_email_recipient} for the email")
        
        return True
    
    async def test_individual_endpoints(self) -> bool:
        """Test each agent endpoint individually"""
        print("🔍 Testing Individual Agent Endpoints...")
        print()
        
        success_count = 0
        total_tests = 3
        
        # Test Market Analyst health
        try:
            response = await self.client.get(f"{self.settings.market_analyst_url}/health")
            if response.status_code == 200:
                print("✅ Market Analyst: Healthy")
                success_count += 1
            else:
                print(f"❌ Market Analyst: Unhealthy (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Market Analyst: Error ({e})")
        
        # Test Trade Planner health
        try:
            response = await self.client.get(f"{self.settings.planner_url}/health")
            if response.status_code == 200:
                print("✅ Trade Planner: Healthy")
                success_count += 1
            else:
                print(f"❌ Trade Planner: Unhealthy (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Trade Planner: Error ({e})")
        
        # Test Mailer health
        try:
            response = await self.client.get(f"{self.settings.mailer_url}/health")
            if response.status_code == 200:
                print("✅ Mailer: Healthy")
                success_count += 1
            else:
                print(f"❌ Mailer: Unhealthy (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ Mailer: Error ({e})")
        
        print(f"\n📊 Health Check Results: {success_count}/{total_tests} agents healthy")
        return success_count == total_tests
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Main test runner"""
    test = E2EWorkflowTest()
    
    try:
        # First check if all agents are healthy
        if not await test.test_individual_endpoints():
            print("\n❌ Some agents are not healthy. Aborting workflow test.")
            print("💡 Make sure all agents are running:")
            print("   python run_market_analyst.py")
            print("   python run_planner.py")
            print("   python run_mailer.py")
            return False
        
        print()
        
        # Run the full workflow test
        success = await test.test_full_workflow()
        
        if success:
            print("\n🎊 ALL TESTS PASSED!")
            print("The StockRipper multi-agent system is working correctly.")
            print(f"📧 A real email was sent to {test.settings.default_email_recipient}")
        else:
            print("\n❌ WORKFLOW TEST FAILED")
            print("Check the logs above for specific issues.")
        
        return success
        
    finally:
        await test.close()


if __name__ == "__main__":
    print("🚀 StockRipper E2E Workflow Test")
    print("Testing Market Analyst → Trade Planner → Mailer workflow")
    print("This will send a REAL email to the configured recipient!")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

# Contains AI-generated edits.
