#!/usr/bin/env python3
"""
Run Mailer agent locally for development and testing.
This script starts the Mailer agent with MCP server integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.mailer.main import MailerAgent


async def main():
    """Main function to run the Mailer agent."""
    
    print("🚀 Starting Mailer Agent")
    print("=" * 40)
    
    try:
        # Create and run the agent
        agent = MailerAgent()
        print(f"📊 Agent: {agent.agent_card.name}")
        print(f"🌐 URL: {agent.agent_card.url}")
        print(f"📡 MCP Servers: {list(agent.mcp_servers_config.keys())}")
        print(f"⚡ Capabilities: {agent.agent_card.capabilities}")
        
        print("\n🎯 Agent is starting...")
        print("   - Press Ctrl+C to stop")
        print("   - Check http://localhost:8003/.well-known/agent.json for discovery")
        print("   - Check http://localhost:8003/health for health status")
        
        # Run the agent
        await agent.run()
        
    except KeyboardInterrupt:
        print("\n👋 Mailer Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Mailer Agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

