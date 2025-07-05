#!/usr/bin/env python3
"""
Run Market Analyst agent locally for development and testing.
This script starts the Market Analyst agent with MCP server integration.
"""

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

from agents.market_analyst.main import StockResearchAgent


def main():
    """Main function to run the Stock Research Agent."""
    
    print("Starting Stock Research Agent")
    print("=" * 40)
    
    try:
        # Create and run the agent
        agent = StockResearchAgent()
        print(f"📊 Agent: Stock Research Agent")
        print(f"🌐 URL: http://localhost:8009")
        print(f"⚡ Agent initialized successfully")
        
        print("\n🎯 Agent is starting...")
        print("   - Press Ctrl+C to stop")
        print("   - Check http://localhost:8009/a2a/agent.json for discovery")
        print("   - Check http://localhost:8009/ for web interface")
        
        # Run the agent using the run_server function directly
        from python_a2a import run_server
        run_server(agent, host="0.0.0.0", port=8009)
        
    except KeyboardInterrupt:
        print("\n👋 Stock Research Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Stock Research Agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Contains AI-generated edits.
