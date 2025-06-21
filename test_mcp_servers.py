#!/usr/bin/env python3
"""
Test script to validate MCP servers are working locally via stdio.
This script tests the basic connectivity and functionality of the MCP servers
before running the full agents.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest
import structlog
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.exceptions import ClientError, McpError

# Load environment variables from .env file
try:
    load_dotenv()
    print("🔧 Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not found, using system environment variables only")

# Setup logging
logging = structlog.get_logger(__name__)

# Test configurations for MCP servers
# Use the UV virtual environment Python
VENV_PYTHON = str(Path(".venv") / "Scripts" / "python.exe")

MCP_SERVER_CONFIGS = {
    "alpaca": {
        "command": VENV_PYTHON,
        "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
        "env": {
            "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
            "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
            "ALPACA_BASE_URL": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            "PAPER": "True"
        }
    },    "gmail": {
        "command": VENV_PYTHON,
        "args": ["./mcp_servers/gmail/main.py", "--transport", "stdio"],
        "env": {
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials/google_credentials.json"),
            "GMAIL_TOKEN_PATH": os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json"),
            "WORKSPACE_MCP_PORT": os.getenv("WORKSPACE_MCP_PORT", "8004"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "")
        }
    }
}


@pytest.mark.asyncio
@pytest.mark.parametrize("server_name", list(MCP_SERVER_CONFIGS.keys()))
async def test_mcp_server(server_name: str) -> None:
    """Test a single MCP server connection and basic functionality."""
    config = MCP_SERVER_CONFIGS[server_name]
    assert await run_test_for_server(server_name, config)


async def run_test_for_server(server_name: str, config: Dict[str, Any]) -> bool:
    """Helper function to run the test for a single server using fastmcp.Client."""
    print(f"\n🧪 Testing MCP server: {server_name}")

    # The FastMCP client expects a specific config format.
    # We wrap our single server config in the format it expects.
    client_config = {"mcpServers": {server_name: config}}

    # The client will manage the subprocess and communication.
    client = Client(client_config)
    result = False

    try:
        # The `async with` block handles connection, initialization, and cleanup.
        async with client:
            print(f"   ✅ Client session started for {server_name}.")
            print(f"   🔎 Requesting available tools...")

            # Use the high-level client method to list tools.
            tools = await client.list_tools()

            if tools:
                print(f"   🎉 Found {len(tools)} tools for {server_name}!")
                for tool in tools:
                    print(f"      - {tool.name}")
                result = True
            else:
                print(f"   ❌ FAIL: 0 tools found for {server_name}.")
                result = False

    except (ClientError, McpError, asyncio.TimeoutError) as e:
        print(f"   ❌ A client or protocol error occurred: {e}")
        result = False
    except Exception as e:
        print(f"   ❌ An unexpected error occurred during testing:")
        import traceback
        traceback.print_exc()
        result = False

    print(f"   {'✅' if result else '❌'} {server_name} test {'completed' if result else 'failed'}")
    return result


# This is the main entry point for running the tests
async def main():
    """Run all MCP server tests."""
    results = {}
    for name, config in MCP_SERVER_CONFIGS.items():
        results[name] = await run_test_for_server(name, config)

    print("\n==================== TEST SUMMARY ====================")
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"- {name}: {status}")
    print("======================================================")

    # Exit with a non-zero code if any test failed
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    # To run this script directly, we can use asyncio.run()
    # Note: This is for standalone execution, not for pytest.
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
