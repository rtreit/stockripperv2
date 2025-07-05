#!/usr/bin/env python3
"""
Test the complete workflow: Market Analyst -> Mailer in Kubernetes
"""
import asyncio
import httpx
from config import get_settings
from datetime import datetime
import json

async def test_market_analyst_k8s():
    """Test the market analyst service running in K8s"""
    print("🔍 Testing Market Analyst in Kubernetes...")
    
    # First, let's check if the service is healthy
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            health_response = await client.get("http://localhost:8001/health")
            print(f"✅ Market Analyst Health Check: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Market Analyst Health Check Failed: {e}")
            return None
        
        # Test the analyze endpoint with IBM
        try:
            analyze_request = {
                "ticker": "IBM"
            }
            
            print(f"📊 Requesting analysis for IBM...")
            response = await client.post(
                "http://localhost:8001/analyze",
                json=analyze_request
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Market Analysis Response:")
                print(f"Status: {result.get('status')}")
                analysis = result.get('analysis', '')
                print(f"Analysis (first 200 chars): {analysis[:200]}...")
                return analysis
            else:
                print(f"❌ Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Analysis request failed: {e}")
            return None

async def test_mailer_k8s(analysis_content):
    """Test sending the analysis via email through the mailer service"""
    print("\n📧 Testing Mailer Service in Kubernetes...")
    
    if not analysis_content:
        print("❌ No analysis content to send")
        return False
    
    # Create a trade plan with the analysis
    trade_plan = {
        "symbol": "IBM",
        "action": "ANALYSIS", 
        "price": "Current Market Price",
        "analysis": analysis_content,
        "timestamp": datetime.now().isoformat(),
        "recommendation": "See detailed analysis below",
        "analyst": "Market Analyst Agent (K8s)",
        "source": "StockRipper v2 Kubernetes Deployment"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check mailer health
            health_response = await client.get("http://localhost:8003/health")
            print(f"✅ Mailer Health Check: {health_response.status_code}")
        except Exception as e:
            print(f"❌ Mailer Health Check Failed: {e}")
            return False
        
        try:
            print("📨 Sending analysis via email...")
            response = await client.post(
                "http://localhost:8003/trade-notification",
                json={"trade_plan": trade_plan}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Email sent successfully!")
                print(f"Response: {result}")
                return True
            else:
                print(f"❌ Email sending failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Email request failed: {e}")
            return False

async def main():
    """Main workflow test"""
    print("🚀 Testing StockRipper v2 Kubernetes Workflow")
    print("=" * 60)
    
    # Step 1: Get IBM analysis from Market Analyst
    analysis = await test_market_analyst_k8s()
    
    if analysis:
        # Step 2: Send analysis via email through Mailer
        email_success = await test_mailer_k8s(analysis)
        
        if email_success:
            print("\n🎉 Complete workflow test PASSED!")
            print("✅ Market Analyst analyzed IBM stock")
            print("✅ Mailer sent the analysis via email")
        else:
            print("\n❌ Workflow test FAILED at email step")
    else:
        print("\n❌ Workflow test FAILED at analysis step")

if __name__ == "__main__":
    asyncio.run(main())

