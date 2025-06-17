#!/usr/bin/env python3
"""
Quick local validation script - tests agent creation and MCP configuration
without starting full servers. This is useful for rapid development iteration.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_minimal_env():
    """Set up minimal environment for testing"""
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-local")
    os.environ.setdefault("MARKET_ANALYST_URL", "http://localhost:8001")
    os.environ.setdefault("PLANNER_URL", "http://localhost:8002")
    os.environ.setdefault("MAILER_URL", "http://localhost:8003")
    os.environ.setdefault("ALPACA_API_KEY", "test-key")
    os.environ.setdefault("ALPACA_SECRET_KEY", "test-secret")
    os.environ.setdefault("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    os.environ.setdefault("GMAIL_CREDENTIALS_PATH", "./credentials/gmail_credentials.json")
    os.environ.setdefault("GMAIL_TOKEN_PATH", "./credentials/gmail_token.json")


def test_agent_mcp_config(agent_class, agent_name: str) -> bool:
    """Test MCP configuration for a specific agent."""
    try:
        print(f"\n🔍 Testing {agent_name} agent...")
        
        # Create agent (this will set up MCP config but not start servers)
        agent = agent_class()
        
        print(f"✅ {agent_name} agent created successfully")
        print(f"📡 Configured MCP servers: {list(agent.mcp_servers_config.keys())}")
        
        # Check MCP server configuration
        for server_name, config in agent.mcp_servers_config.items():
            print(f"  📋 MCP Server: {server_name}")
            print(f"    Command: {config.get('command', 'Not set')}")
            print(f"    Args: {config.get('args', [])}")
            
            # Check if server script exists
            args = config.get('args', [])
            if args and args[0].endswith('.py'):
                script_path = Path(args[0])
                if script_path.exists():
                    print(f"    Script: ✅ {script_path}")
                else:
                    print(f"    Script: ❌ {script_path} (not found)")
            
            env_vars = config.get('env', {})
            print(f"    Environment variables: {len(env_vars)} configured")
            
            # Show environment variables (without revealing secrets)
            for key, value in env_vars.items():
                if any(secret in key.lower() for secret in ['key', 'secret', 'token', 'password']):
                    display_value = "***" if value else "(empty)"
                else:
                    display_value = value
                print(f"      {key}: {display_value}")
        
        # Test agent card
        try:
            agent_card = agent.get_agent_card()
            print(f"  📄 Agent card: ✅ {agent_card.get('name', 'Unknown')}")
        except Exception as e:
            print(f"  📄 Agent card: ❌ {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ {agent_name} agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_config():
    """Test MCP server configuration for all agents without starting processes"""
    try:
        setup_minimal_env()
        
        print("🚀 StockRipper v2 Local Configuration Validation")
        print("=" * 55)
        
        # Test agents
        agent_tests = [
            ("Market Analyst", "agents.market_analyst.main", "MarketAnalystAgent"),
            ("Planner", "agents.planner.main", "PlannerAgent"),
            ("Mailer", "agents.mailer.main", "MailerAgent")
        ]
        
        passed = 0
        total = len(agent_tests)
        
        for agent_name, module_path, class_name in agent_tests:
            try:
                # Import the module
                module = __import__(module_path, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                # Test the agent
                if test_agent_mcp_config(agent_class, agent_name):
                    passed += 1
                    
            except Exception as e:
                print(f"\n❌ Failed to import {agent_name}: {e}")
        
        # Summary
        print("\n" + "=" * 55)
        print(f"📊 Validation Summary: {passed}/{total} agents configured correctly")
        
        if passed == total:
            print("🎉 All agents configured correctly!")
            print("\nNext steps:")
            print("1. Run: python test_mcp_servers.py  # Test MCP server connectivity")
            print("2. Run individual agents for full testing")
        else:
            print("⚠️  Some agents have configuration issues")
            print("Please fix the errors above before running MCP server tests")
            
        return passed == total
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        return False

def test_agent_discovery():
    """Test agent discovery endpoint configuration"""
    try:
        setup_minimal_env()
        
        print("\n🔍 Testing agent discovery configuration...")
        
        from agents.market_analyst.main import MarketAnalystAgent
        from agents.planner.main import PlannerAgent
        from agents.mailer.main import MailerAgent
        
        agents = [
            ("Market Analyst", MarketAnalystAgent()),
            ("Planner", PlannerAgent()),
            ("Mailer", MailerAgent())        ]
        
        for name, agent in agents:
            card = agent.get_agent_card()
            print(f"✅ {name}: {card['url']}")
            capabilities = card.get('capabilities', [])
            if isinstance(capabilities, dict):
                print(f"   Capabilities: {list(capabilities.keys())}")
            else:
                print(f"   Capabilities: {capabilities}")
            endpoints = card.get('endpoints', [])
            if isinstance(endpoints, dict):
                print(f"   Endpoints: {list(endpoints.keys())}")
            else:
                endpoint_names = [ep.get('path', 'unknown').split('/')[-1] if isinstance(ep, dict) else str(ep) for ep in endpoints]
                print(f"   Endpoints: {endpoint_names}")
            
        return True
        
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_mcp_servers_available():
    """Check if MCP servers are installed and available"""
    try:
        print("\n🔍 Checking MCP server availability...")
        
        import subprocess
        
        # Test Alpaca MCP server
        alpaca_script = Path("./mcp_servers/alpaca/alpaca_mcp_server.py")
        if alpaca_script.exists():
            print("✅ Alpaca MCP server script found")
        else:
            print("❌ Alpaca MCP server script not found")
            
        # Test Gmail MCP server
        gmail_script = Path("./mcp_servers/gmail/main.py")
        if gmail_script.exists():
            print("✅ Gmail MCP server script found")
        else:
            print("❌ Gmail MCP server script not found")
            
        # Test Python availability
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True,
            timeout=5        )
        
        if result.returncode == 0:
            print(f"✅ Python available: {result.stdout.strip()}")
        else:
            print("❌ Python not available")
            
        return True
        
    except Exception as e:
        print(f"⚠️  Could not check MCP servers: {e}")
        return False

if __name__ == "__main__":
    print("🧪 StockRipper Local Validation")
    print("=" * 40)
    
    success = True
    success &= test_mcp_config()
    success &= test_agent_discovery()
    success &= check_mcp_servers_available()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Local validation passed!")
        print("\nNext steps:")
        print("1. Copy .env.local.example to .env.local")
        print("2. Add your real API keys to .env.local")
        print("3. Run: python run_local.py")
    else:
        print("❌ Some validation issues found")
        
# Contains AI-generated edits.
