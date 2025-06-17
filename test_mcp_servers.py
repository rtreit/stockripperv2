#!/usr/bin/env python3
"""
Test script to validate MCP servers are working locally via stdio.
This script tests the basic connectivity and functionality of the MCP servers
before running the full agents.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import structlog
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Setup logging
logging = structlog.get_logger(__name__)

# Test configurations for MCP servers
MCP_SERVER_CONFIGS = {
    "alpaca": {
        "command": "python",
        "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
        "env": {
            "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
            "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
            "ALPACA_BASE_URL": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            "PAPER": "True"
        }
    },
    "gmail": {
        "command": "python",
        "args": ["./mcp_servers/gmail/main.py", "--transport", "stdio"],
        "env": {
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials/gmail_credentials.json"),
            "GMAIL_CREDENTIALS_PATH": os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials/gmail_credentials.json"),
            "GMAIL_TOKEN_PATH": os.getenv("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")
        }
    }
}


async def test_mcp_server(server_name: str, config: Dict[str, Any]) -> bool:
    """Test a single MCP server connection and basic functionality."""
    
    print(f"\n🧪 Testing MCP server: {server_name}")
    print(f"   Command: {config['command']} {' '.join(config['args'])}")
    
    try:
        # Prepare environment
        server_env = os.environ.copy()
        server_env.update(config.get("env", {}))
        
        # Check if the server script exists
        script_path = Path(config["args"][0])
        if not script_path.exists():
            print(f"   ❌ Server script not found: {script_path}")
            return False
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
            env=config.get("env", {})
        )
        
        print(f"   ⏳ Starting server process...")
        
        # Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            session = ClientSession(read, write)
            
            # Initialize the session
            await session.initialize()
            print(f"   ✅ Connected to {server_name} MCP server")
            
            # List available tools
            try:
                tools_result = await session.list_tools()
                tools = tools_result.tools if hasattr(tools_result, 'tools') else []
                print(f"   📋 Available tools: {len(tools)}")
                
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"      - {tool.name}: {tool.description}")
                if len(tools) > 3:
                    print(f"      ... and {len(tools) - 3} more")
                    
            except Exception as e:
                print(f"   ⚠️  Warning: Could not list tools: {e}")
                tools = []
            
            # List available resources
            try:
                resources_result = await session.list_resources()
                resources = resources_result.resources if hasattr(resources_result, 'resources') else []
                print(f"   📚 Available resources: {len(resources)}")
                
            except Exception as e:
                print(f"   ⚠️  Warning: Could not list resources: {e}")
                resources = []
            
            print(f"   ✅ {server_name} MCP server test completed successfully")
            return True
            
    except Exception as e:
        print(f"   ❌ Failed to test {server_name} MCP server: {e}")
        return False


async def check_environment() -> bool:
    """Check if the environment is properly configured."""
    
    print("🔧 Checking environment configuration...")
    
    # Check for required environment variables
    required_vars = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY",
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   ℹ️  These variables are required for full MCP server functionality")
        print("   ℹ️  Copy .env.example to .env and fill in your credentials")
        return False
    
    # Check for credentials directory
    creds_dir = Path("./credentials")
    if not creds_dir.exists():
        print(f"   ⚠️  Credentials directory not found: {creds_dir}")
        print("   ℹ️  Create ./credentials directory for Gmail authentication")
        return False
    
    print("   ✅ Environment configuration looks good")
    return True


async def main():
    """Main test function."""
    
    print("🚀 StockRipper v2 MCP Server Test Suite")
    print("=" * 50)
    
    # Check environment
    env_ok = await check_environment()
    if not env_ok:
        print("\n⚠️  Environment issues detected. Some tests may fail.")
        print("   Update your .env file and credentials before running agents.")
    
    # Test each MCP server
    results = {}
    for server_name, config in MCP_SERVER_CONFIGS.items():
        try:
            success = await test_mcp_server(server_name, config)
            results[server_name] = success
        except KeyboardInterrupt:
            print(f"\n⏹️  Test interrupted for {server_name}")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error testing {server_name}: {e}")
            results[server_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for server_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {server_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} MCP servers working")
    
    if passed_tests == total_tests:
        print("🎉 All MCP servers are working! You can now run the agents.")
    else:
        print("⚠️  Some MCP servers failed. Check the errors above.")
        print("   Make sure your .env file is configured correctly.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

# Contains AI-generated edits.
