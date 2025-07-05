#!/usr/bin/env python3
"""
Run Market Analyst agent locally for development and testing.
This script starts the Market Analyst agent with MCP server integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not found, using system environment variables only")

from agents.market_analyst.main import main as market_analyst_main


def main():
    """Main function to run the Market Analyst Agent."""
    
    print("Starting Market Analyst Agent")
    print("=" * 40)
    
    try:
        print(f"📊 Agent: Market Analyst Agent")
        print(f"🌐 URL: http://localhost:8001")
        
        print("\n🎯 Agent is starting...")
        print("   - Press Ctrl+C to stop")
        print("   - Check http://localhost:8001/.well-known/agent.json for discovery")
        print("   - Check http://localhost:8001/health for health status")
        
        # Run the agent using its own main function
        asyncio.run(market_analyst_main())
        
    except KeyboardInterrupt:
        print("\n👋 Market Analyst Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Market Analyst Agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
