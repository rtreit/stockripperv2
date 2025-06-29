#!/usr/bin/env python3
"""Direct test of Gmail MCP server to understand parameter requirements."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_gmail_direct():
    """Test Gmail MCP server directly."""
    try:
        server_params = StdioServerParameters(
            command="python", 
            args=["mcp_servers/gmail/main.py", "--single-user"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # List tools
                tools_result = await session.list_tools()
                print(f"Found {len(tools_result.tools)} tools")
                
                # Find send_gmail_message
                send_tool = None
                for tool in tools_result.tools:
                    if tool.name == "send_gmail_message":
                        send_tool = tool
                        break
                
                if send_tool:
                    print(f"Tool: {send_tool.name}")
                    print(f"Description: {send_tool.description}")
                    if hasattr(send_tool, 'inputSchema'):
                        print(f"Schema: {json.dumps(send_tool.inputSchema, indent=2)}")
                    
                    # Try to call the tool
                    try:
                        result = await session.call_tool(
                            "send_gmail_message",
                            {
                                "user_google_email": "rtreit@gmail.com",
                                "to": "randyt@outlook.com",
                                "subject": "Test from MCP Direct",
                                "body": "This is a direct test of the Gmail MCP server."
                            }
                        )
                        print(f"Result: {result}")
                    except Exception as e:
                        print(f"Tool call error: {e}")
                else:
                    print("send_gmail_message tool not found")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gmail_direct())
