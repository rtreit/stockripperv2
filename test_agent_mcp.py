#!/usr/bin/env python3
"""
Test the agent's MCP integration specifically
"""

import asyncio
import os
from pathlib import Path
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

async def test_agent_mcp_integration():
    """Test the MCP integration that the agent uses"""
    
    print("🧪 Testing Agent MCP Integration")
    print("=" * 40)
    
    # Configure Alpaca MCP server (same as in agent)
    venv_python = str(Path(".venv") / "Scripts" / "python.exe")
    
    server_config = {
        "command": venv_python,
        "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
        "env": {
            "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
            "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
            "ALPACA_BASE_URL": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            "PAPER": "True"
        }
    }
    
    print(f"📡 Starting MCP server: alpaca")
    print(f"   Command: {server_config['command']} {' '.join(server_config['args'])}")
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config["env"]
        )
        
        print("🔌 Connecting to MCP server...")
        
        # Use the correct pattern from your test
        async with stdio_client(server_params) as (read, write):
            print("✅ Connected to MCP server")
            
            # Create session
            session = ClientSession(read, write)
            print("✅ Created client session")
            
            # Initialize session
            print("🔄 Initializing session...")
            init_result = await session.initialize()
            print(f"✅ Session initialized: {init_result}")
            
            # List tools
            print("🔍 Listing available tools...")
            tools_result = await session.list_tools()
            tools = tools_result.tools if hasattr(tools_result, 'tools') else []
            
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   📋 {tool.name}: {tool.description}")
            
            # Test calling a tool (if available)
            if tools:
                first_tool = tools[0]
                print(f"\n🧪 Testing tool call: {first_tool.name}")
                try:
                    # Call with minimal parameters (this might fail, but we want to see the response)
                    result = await session.call_tool(first_tool.name, {})
                    print(f"✅ Tool call successful: {result}")
                except Exception as tool_error:
                    print(f"⚠️  Tool call failed (expected for some tools): {tool_error}")
            
            print("\n🎉 MCP integration test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agent_mcp_integration())
    exit(0 if success else 1)

# Contains AI-generated edits.
