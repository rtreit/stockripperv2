#!/usr/bin/env python3
"""
Test script to run a single agent with stdio MCP servers locally
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.market_analyst.main import MarketAnalystAgent
from config import setup_logging


async def test_market_analyst():
    """Test the market analyst agent with stdio MCP servers"""
    
    # Set required environment variables
    os.environ.setdefault("OPENAI_API_KEY", "your-openai-key-here")
    os.environ.setdefault("ALPACA_API_KEY", "your-alpaca-key-here")
    os.environ.setdefault("ALPACA_SECRET_KEY", "your-alpaca-secret-here")
    os.environ.setdefault("MARKET_ANALYST_URL", "http://localhost:8001")
    os.environ.setdefault("PLANNER_URL", "http://localhost:8002")
    os.environ.setdefault("MAILER_URL", "http://localhost:8003")
    
    # Setup logging with settings
    from config import get_settings
    settings = get_settings()
    setup_logging(settings)
    
    print("🚀 Starting Market Analyst Agent with stdio MCP servers...")
    
    try:
        agent = MarketAnalystAgent()
        print("✅ Agent initialized successfully")
        print("📡 Starting agent server (Ctrl+C to stop)...")
        
        await agent.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down agent...")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_market_analyst())

# Contains AI-generated edits.
