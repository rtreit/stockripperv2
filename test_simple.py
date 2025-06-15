#!/usr/bin/env python3
"""
Simple test script to validate MCP stdio agent setup
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("🔍 Testing imports...")
        
        # Test config import
        from config import get_settings, setup_logging
        print("✅ Config imports successful")
        
        # Test base agent import
        from agents.base import BaseA2AAgent
        print("✅ Base agent imports successful")
        
        # Test individual agent imports
        from agents.market_analyst.main import MarketAnalystAgent
        print("✅ Market Analyst agent imports successful")
        
        from agents.planner.main import PlannerAgent
        print("✅ Planner agent imports successful")
        
        from agents.mailer.main import MailerAgent
        print("✅ Mailer agent imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        print("\n🔍 Testing configuration...")
        
        # Set minimal required env vars
        os.environ.setdefault("MARKET_ANALYST_URL", "http://localhost:8001")
        os.environ.setdefault("PLANNER_URL", "http://localhost:8002")
        os.environ.setdefault("MAILER_URL", "http://localhost:8003")
        
        from config import get_settings
        settings = get_settings()
        
        print(f"✅ Settings loaded: {settings.market_analyst_url}")
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_agent_creation():
    """Test agent creation without running"""
    try:
        print("\n🔍 Testing agent creation...")
        
        # Set API keys (dummy values for testing)
        os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")
        os.environ.setdefault("ALPACA_API_KEY", "test-key")
        os.environ.setdefault("ALPACA_SECRET_KEY", "test-secret")
        
        from agents.market_analyst.main import MarketAnalystAgent
        
        # Try to create agent (don't start it)
        agent = MarketAnalystAgent()
        print("✅ Market Analyst agent created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running StockRipper MCP Stdio Tests\n")
    
    success = True
    success &= test_imports()
    success &= test_config()
    success &= test_agent_creation()
    
    if success:
        print("\n🎉 All tests passed! MCP stdio integration is working.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)

# Contains AI-generated edits.
