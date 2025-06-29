#!/usr/bin/env python3
"""
Debug tool to list all available Gmail MCP tools.
"""
import asyncio
import sys
import os
import httpx
from config import get_settings

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def list_mailer_tools():
    """List all available tools from the Mailer agent."""
    settings = get_settings()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{settings.mailer_url}/mcp-status")
            if response.status_code == 200:
                result = response.json()
                print("📊 Mailer MCP Status:")
                print(f"{result}")
                return result
            else:
                print(f"❌ Failed to get MCP status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def call_mailer_tool_list():
    """Try to get a list of tools from the Mailer via debug endpoint."""
    settings = get_settings()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Check if there's a tools endpoint
            response = await client.get(f"{settings.mailer_url}/openapi.json")
            if response.status_code == 200:
                openapi = response.json()
                print("📋 Available Mailer endpoints:")
                for path in openapi.get("paths", {}):
                    print(f"  - {path}")
            
        except Exception as e:
            print(f"❌ Error getting endpoints: {e}")


async def main():
    print("🔍 Gmail MCP Tools Debug")
    print("=" * 40)
    
    print("\n1. Checking Mailer MCP Status...")
    await list_mailer_tools()
    
    print("\n2. Checking Available Endpoints...")
    await call_mailer_tool_list()
    
    print(f"\n💡 The Gmail MCP server has 41 tools loaded.")
    print(f"🔧 We need to find the correct tool name for sending emails.")
    print(f"📧 Common Gmail API operations include:")
    print(f"   - send_message")
    print(f"   - compose_message") 
    print(f"   - create_draft")
    print(f"   - send_email")
    print(f"   - gmail_send")


if __name__ == "__main__":
    asyncio.run(main())

# Contains AI-generated edits.
