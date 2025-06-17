#!/usr/bin/env python3
"""
Local development test runner for StockRipper agents with real MCP servers
"""
import asyncio
import os
import sys
import signal
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_local_env():
    """Load local environment variables"""
    env_file = project_root / ".env.local"
    if env_file.exists():
        print(f"📄 Loading environment from {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
        return True
    else:
        print(f"⚠️  {env_file} not found. Copy .env.local.example to .env.local and configure your API keys.")
        return False

def check_required_env():
    """Check if required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY",
        "MARKET_ANALYST_URL", 
        "PLANNER_URL",
        "MAILER_URL"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f"your-{var.lower().replace('_', '-')}-here":
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("📝 Please update your .env.local file with actual values")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def test_single_agent(agent_name: str, port: int):
    """Test a single agent"""
    try:
        print(f"\n🚀 Starting {agent_name} Agent on port {port}")
        
        # Import the specific agent
        if agent_name == "market_analyst":
            from agents.market_analyst.main import MarketAnalystAgent
            agent = MarketAnalystAgent()
        elif agent_name == "planner":
            from agents.planner.main import PlannerAgent
            agent = PlannerAgent()
        elif agent_name == "mailer":
            from agents.mailer.main import MailerAgent
            agent = MailerAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        print(f"✅ {agent_name} agent created successfully")
        print(f"🔧 Setting up MCP servers...")
        
        # Run the agent
        await agent.run()
        
    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down {agent_name} agent...")
        if hasattr(agent, 'cleanup'):
            await agent.cleanup()
    except Exception as e:
        print(f"❌ Error in {agent_name} agent: {e}")
        import traceback
        traceback.print_exc()

async def test_market_analyst():
    """Test just the market analyst agent"""
    await test_single_agent("market_analyst", 8001)

async def test_planner():
    """Test just the planner agent"""
    await test_single_agent("planner", 8002)

async def test_mailer():
    """Test just the mailer agent"""
    await test_single_agent("mailer", 8003)

def main():
    """Main entry point"""
    print("🧪 StockRipper Local Development Environment")
    print("=" * 50)
    
    # Load environment
    if not load_local_env():
        return
    
    # Check environment variables
    if not check_required_env():
        return
    
    # Show available options
    print("\nAvailable test modes:")
    print("1. Market Analyst only (port 8001)")
    print("2. Planner only (port 8002)")
    print("3. Mailer only (port 8003)")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    try:
        if choice == "1":
            print("\n📈 Testing Market Analyst Agent...")
            asyncio.run(test_market_analyst())
        elif choice == "2":
            print("\n📋 Testing Planner Agent...")
            asyncio.run(test_planner())
        elif choice == "3":
            print("\n📧 Testing Mailer Agent...")
            asyncio.run(test_mailer())
        else:
            print("❌ Invalid choice")
            return
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()

# Contains AI-generated edits.
