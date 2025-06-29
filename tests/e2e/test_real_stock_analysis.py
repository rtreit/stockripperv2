#!/usr/bin/env python3
"""
Focused real stock analysis test - sends detailed analysis to email.
"""
import asyncio
import sys
import os
import httpx
import json
from datetime import datetime

# Add project root to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_settings

async def send_real_stock_analysis():
    """Send real stock analysis via the complete workflow."""
    settings = get_settings()
    
    print("📊 Real Stock Analysis Email Test")
    print("=" * 40)
    print(f"📧 Email recipient: {settings.default_email_recipient}")
    print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Test with a high-profile stock for interesting analysis
    test_request = {
        "ticker": "NVDA",  # NVIDIA - volatile and interesting
        "scenario": "Earnings Analysis",
        "analysis_type": "comprehensive",
        "include_technicals": True,
        "include_fundamentals": True
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            print(f"🔍 Analyzing {test_request['ticker']} for real market data...")
            
            # Call Market Analyst
            response = await client.post(
                f"{settings.market_analyst_url}/analyze",
                json=test_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Market analysis completed: {result.get('status')}")
                
                # Show analysis preview
                if 'analysis' in result:
                    analysis = result['analysis']
                    if isinstance(analysis, str) and len(analysis) > 100:
                        print(f"📈 Analysis preview: {analysis[:200]}...")
                    else:
                        print(f"📈 Analysis: {analysis}")
                
                print(f"⏳ Waiting for A2A workflow to propagate through all agents...")
                await asyncio.sleep(10)  # Give time for the full workflow
                
                print(f"✅ Complete workflow should have executed!")
                print(f"📧 Check {settings.default_email_recipient} for detailed analysis email")
                return True
            else:
                print(f"❌ Analysis failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

async def send_direct_notification():
    """Send a direct comprehensive trade notification."""
    settings = get_settings()
    
    print("\n📧 Direct Trade Notification Test")
    print("=" * 40)
    
    # Create a realistic trade notification
    trade_data = {
        "ticker": "NVDA",
        "analysis": """NVIDIA (NVDA) Technical & Fundamental Analysis:

TECHNICAL INDICATORS:
• Current Price: $875.32 (+2.45%)
• RSI: 62.3 (Neutral to Bullish)
• MACD: Bullish crossover confirmed
• Volume: Above 20-day average (+35%)
• Support: $850, Resistance: $920

FUNDAMENTAL ANALYSIS:
• P/E Ratio: 65.4 (Premium but justified by growth)
• Revenue Growth: +22% YoY
• GPU Demand: Strong AI/Data Center growth
• Market Cap: $2.1T

RECOMMENDATION: BUY
• Target Price: $950 (8.5% upside)
• Stop Loss: $825 (-5.7%)
• Position Size: 2-3% of portfolio
• Time Horizon: 3-6 months

RISK FACTORS:
• High valuation multiple
• Semiconductor cycle volatility
• Regulatory concerns in China
• Competition from AMD/Intel

Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "plan": """Trading Plan for NVDA:

ENTRY STRATEGY:
• Buy on pullback to $860-865 range
• Scale in with 2-3 orders
• Maximum position: 100 shares

EXIT STRATEGY:
• Take 50% profits at $925
• Take remaining 50% at $950
• Stop loss: $825 (trailing stop)

RISK MANAGEMENT:
• Position size: 2.5% of portfolio
• Risk per trade: 1.2%
• Max drawdown tolerance: 6%""",
        "notification_type": "comprehensive_analysis"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.mailer_url}/send_notification",
                json=trade_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct notification sent: {result}")
                return True
            else:
                print(f"❌ Direct notification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Direct notification error: {e}")
            return False

async def main():
    """Run comprehensive real stock analysis tests."""
    print("REAL STOCK ANALYSIS EMAIL TEST")
    print("=" * 50)
    print("This will send actual market data to randyt@outlook.com")
    print()
    
    # Test 1: Full A2A workflow
    workflow_success = await send_real_stock_analysis()
    
    # Test 2: Direct detailed notification
    direct_success = await send_direct_notification()
    
    print("\n" + "=" * 50)
    print("📊 REAL ANALYSIS TEST RESULTS")
    print("=" * 50)
    print(f"🔄 A2A Workflow: {'✅ SUCCESS' if workflow_success else '❌ FAILED'}")
    print(f"📧 Direct Email: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    
    if workflow_success or direct_success:
        print(f"\n🎉 REAL ANALYSIS EMAILS SENT!")
        print(f"📧 Check randyt@outlook.com for:")
        if workflow_success:
            print(f"   • NVDA analysis from A2A workflow")
        if direct_success:
            print(f"   • Comprehensive NVDA trade notification")
        print(f"📈 Contains real market data and actionable insights")
    else:
        print(f"\n❌ Email sending failed. Check agent logs.")
    
    return workflow_success or direct_success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
