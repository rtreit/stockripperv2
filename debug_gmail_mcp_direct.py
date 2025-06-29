#!/usr/bin/env python3
"""
Debug script to directly inspect Gmail MCP tools by connecting to the MCP server.
"""
import asyncio
import sys
import os
from fastmcp import Client

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def debug_gmail_mcp():
    """Connect directly to Gmail MCP server and list all tools."""
    print("🔍 Connecting directly to Gmail MCP server...")
    
    # Use the same configuration as the Mailer agent
    client = Client()
    await client.connect(
        command="python",
        args=["./mcp_servers/gmail/main.py", "--transport", "stdio"],
        env={
            "GOOGLE_APPLICATION_CREDENTIALS": "./credentials/gmail_credentials.json",
            "GMAIL_CREDENTIALS_PATH": "./credentials/gmail_credentials.json",
            "GMAIL_TOKEN_PATH": "./credentials/gmail_token.json"
        }
    )
    
    try:
        async with client:
            print("✅ Connected to Gmail MCP server")
            
            # List all tools
            tools = await client.list_tools()
            print(f"📊 Found {len(tools)} tools:")
            
            # Look for email-sending tools
            send_tools = []
            for i, tool in enumerate(tools, 1):
                tool_name = tool.name
                tool_desc = getattr(tool, 'description', 'No description')
                
                print(f"  {i:2d}. {tool_name}")
                if i <= 5:  # Show description for first 5
                    print(f"      📝 {tool_desc[:80]}...")
                
                # Look for sending-related tools
                if any(keyword in tool_name.lower() for keyword in ['send', 'compose', 'create', 'draft']):
                    send_tools.append((tool_name, tool_desc))
            
            if send_tools:
                print(f"\n📧 Email-related tools found:")
                for name, desc in send_tools:
                    print(f"  🎯 {name}")
                    print(f"     📝 {desc[:100]}...")
            else:
                print(f"\n❌ No obvious email-sending tools found")
                print(f"💡 The tool might have a different name pattern")
            
    except Exception as e:
        print(f"❌ Error connecting to Gmail MCP: {e}")
        print(f"💡 Make sure Gmail credentials are properly configured")


if __name__ == "__main__":
    asyncio.run(debug_gmail_mcp())

# Contains AI-generated edits.
