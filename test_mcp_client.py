#!/usr/bin/env python3
"""
Test MCP client usage to understand the correct pattern
"""

import asyncio
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

async def test_mcp_client():
    """Test the correct MCP client usage pattern"""
    
    # Server parameters for Alpaca
    server_params = StdioServerParameters(
        command=".venv/Scripts/python.exe",
        args=["./mcp_servers/alpaca/alpaca_mcp_server.py"],
        env={
            "ALPACA_API_KEY": "test",
            "ALPACA_SECRET_KEY": "test",
            "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
            "PAPER": "True"
        }
    )
    
    print("Testing MCP client connection...")
    
    # Test the proper usage pattern
    try:
        async with stdio_client(server_params) as (read, write):
            print(f"Connected! Read: {type(read)}, Write: {type(write)}")
            
            # Create a ClientSession from the streams
            session = ClientSession(read, write)
            print(f"Session created: {type(session)}")
            
            # Initialize the session
            print("Initializing session...")
            init_result = await session.initialize()
            print(f"Initialized: {init_result}")
            
            # Try to list tools
            print("Listing tools...")
            tools_result = await session.list_tools()
            print(f"Tools: {tools_result}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_client())

# Contains AI-generated edits.
