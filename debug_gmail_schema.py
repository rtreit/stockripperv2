#!/usr/bin/env python3
"""Test Gmail MCP tool parameters directly."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_gmail_tool():
    """Test the Gmail MCP tool to see what parameters it expects."""
    try:
        server_params = StdioServerParameters(
            command="python", 
            args=["mcp_servers/gmail/gmail_mcp_server.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # List tools to get detailed info
                tools_result = await session.list_tools()
                
                # Find send_gmail_message tool
                for tool in tools_result.tools:
                    if tool.name == "send_gmail_message":
                        print("Tool: send_gmail_message")
                        print(f"Description: {tool.description}")
                        if hasattr(tool, 'inputSchema'):
                            print(f"Input Schema: {json.dumps(tool.inputSchema, indent=2)}")
                        break
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gmail_tool())
