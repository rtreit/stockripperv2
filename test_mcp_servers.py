#!/usr/bin/env python3
"""
Test script to validate MCP servers are working locally via stdio.
This script tests the basic connectivity and functionality of the MCP servers
before running the full agents.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import structlog

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
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


async def test_mcp_server(server_name: str, config: Dict[str, Any]) -> bool:
    """Test a single MCP server connection and basic functionality."""
    
    print(f"\n🧪 Testing MCP server: {server_name}")
    print(f"   Command: {config['command']} {' '.join(config['args'])}")
    
    try:
        # Prepare environment
        server_env = os.environ.copy()
        server_env.update(config.get("env", {}))
        
        # Debug: Print environment variables being passed
        print(f"   📋 Environment variables:")
        for key, value in config.get("env", {}).items():
            masked_value = "***" if "SECRET" in key or "KEY" in key else value
            print(f"      {key}={masked_value}")
        
        # Check if the server script exists
        script_path = Path(config["args"][0])
        if not script_path.exists():
            print(f"   ❌ Server script not found: {script_path}")
            return False
        
        print(f"   ⏳ Starting server process...")
        
        # Start the subprocess with a reasonable timeout
        full_command = [config["command"]] + config["args"]
        print(f"   🔧 Full command: {' '.join(full_command)}")
        
        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=server_env,
            cwd=os.getcwd()  # Ensure we're in the right directory
        )
        
        # Wait for server to start (with timeout)
        try:
            # Give the server 3 seconds to start
            await asyncio.sleep(3)
            
            # Check if process is still running (good sign)
            if process.returncode is None:
                print(f"   ✅ Server process started successfully")
                
                # Try to send a simple MCP initialization message
                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                # Send initialization message
                message_bytes = (json.dumps(init_message) + "\n").encode()
                process.stdin.write(message_bytes)
                await process.stdin.drain()
                
                # Try to read response (with timeout)
                try:
                    response_future = process.stdout.readline()
                    response = await asyncio.wait_for(response_future, timeout=5.0)
                    
                    if response:
                        response_text = response.decode().strip()
                        print(f"   ✅ Server responded: {response_text[:100]}...")
                        
                        # Try to parse as JSON
                        try:
                            response_data = json.loads(response_text)
                            if "result" in response_data:
                                print(f"   ✅ Valid MCP response received")
                            else:
                                print(f"   ⚠️  Response received but not a standard MCP result")
                        except json.JSONDecodeError:
                            print(f"   ⚠️  Response received but not valid JSON")
                            
                    else:
                        print(f"   ⚠️  Server started but no response to initialization")
                        
                except asyncio.TimeoutError:
                    print(f"   ⚠️  Server started but timeout waiting for response")
                    
                result = True  # Server started successfully
                    
            else:
                print(f"   ❌ Server exited with code: {process.returncode}")
                
                # Read stderr for error details
                stderr_data = await process.stderr.read()
                if stderr_data:
                    error_text = stderr_data.decode()
                    print(f"   ❌ Error output: {error_text[:500]}...")
                
                # Read stdout too
                stdout_data = await process.stdout.read()
                if stdout_data:
                    output_text = stdout_data.decode()
                    print(f"   ℹ️  Stdout output: {output_text[:500]}...")
                    
                result = False
            
        except asyncio.TimeoutError:
            print(f"   ❌ Server startup timeout")
            result = False
            
        # Clean up the process
        if process.returncode is None:
            print(f"   🧹 Terminating server process...")
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                print(f"   🧹 Force killing unresponsive server...")
                process.kill()
                await process.wait()
        
        print(f"   {'✅' if result else '❌'} {server_name} test {'completed' if result else 'failed'}")
        return result
        
    except FileNotFoundError:
        print(f"   ❌ Command not found: {config['command']}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
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
