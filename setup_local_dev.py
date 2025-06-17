#!/usr/bin/env python3
"""
Local development setup and validation script for StockRipper v2.
This script helps developers set up their local environment and validate
that all MCP servers and agents are working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import subprocess

import structlog

# Setup basic logging
logging = structlog.get_logger(__name__)


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_required_files() -> bool:
    """Check if all required files exist."""
    required_files = [
        "requirements.txt",
        "config.py",
        ".env.example",
        "mcp_servers/alpaca/alpaca_mcp_server.py",
        "mcp_servers/gmail/main.py",
        "agents/market_analyst/main.py",
        "agents/planner/main.py", 
        "agents/mailer/main.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True


def setup_environment() -> bool:
    """Setup environment file and directories."""
    
    # Check if .env exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("⚠️  .env file not found. Creating from .env.example...")
            try:
                with open(".env.example", "r") as example:
                    content = example.read()
                with open(".env", "w") as env_file:
                    env_file.write(content)
                print("✅ Created .env file from .env.example")
                print("   ❗ Please edit .env and add your API keys!")
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file exists")
    
    # Create credentials directory
    creds_dir = Path("credentials")
    if not creds_dir.exists():
        try:
            creds_dir.mkdir()
            print("✅ Created credentials directory")
            
            # Create README in credentials
            readme_content = """# Credentials Directory

This directory should contain your API credentials:

## Gmail API
- gmail_credentials.json: OAuth2 client credentials from Google Cloud Console
- gmail_token.json: Generated OAuth2 token (created automatically on first run)

## Setup Instructions

### Gmail API Setup
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download the JSON file and save as gmail_credentials.json

### Alpaca API Setup
1. Sign up at Alpaca Markets (https://alpaca.markets/)
2. Get your API key and secret from the dashboard
3. Add them to your .env file

Note: Never commit credentials to version control!
"""
            with open(creds_dir / "README.md", "w") as f:
                f.write(readme_content)
                
        except Exception as e:
            print(f"❌ Failed to create credentials directory: {e}")
            return False
    else:
        print("✅ Credentials directory exists")
    
    return True


def install_dependencies() -> bool:
    """Install Python dependencies."""
    
    print("📦 Installing Python dependencies...")
    
    try:
        # Install main requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Main dependencies installed")
        
        # Install MCP server dependencies
        alpaca_reqs = Path("mcp_servers/alpaca/requirements.txt")
        if alpaca_reqs.exists():
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(alpaca_reqs)
            ], capture_output=True, text=True, check=True)
            print("✅ Alpaca MCP server dependencies installed")
        
        # Install Gmail MCP server dependencies
        gmail_dir = Path("mcp_servers/gmail")
        if (gmail_dir / "pyproject.toml").exists():
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", str(gmail_dir)
            ], capture_output=True, text=True, check=True)
            print("✅ Gmail MCP server dependencies installed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False


async def test_agent_imports() -> bool:
    """Test that all agents can be imported."""
    
    print("🧪 Testing agent imports...")
    
    agents_to_test = [
        ("Market Analyst", "agents.market_analyst.main", "MarketAnalystAgent"),
        ("Planner", "agents.planner.main", "PlannerAgent"),
        ("Mailer", "agents.mailer.main", "MailerAgent")
    ]
    
    success_count = 0
    
    for agent_name, module_path, class_name in agents_to_test:
        try:
            # Import the module
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            # Try to instantiate (this will test config loading)
            agent = agent_class()
            print(f"   ✅ {agent_name}: imported and instantiated")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ {agent_name}: {e}")
    
    if success_count == len(agents_to_test):
        print("✅ All agents imported successfully")
        return True
    else:
        print(f"❌ {len(agents_to_test) - success_count} agents failed to import")
        return False


def create_run_script() -> bool:
    """Create convenient run scripts for local development."""
    
    # Create run_market_analyst.py
    market_analyst_script = '''#!/usr/bin/env python3
"""Run Market Analyst agent locally."""
import asyncio
from agents.market_analyst.main import MarketAnalystAgent

async def main():
    agent = MarketAnalystAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Create run_planner.py
    planner_script = '''#!/usr/bin/env python3
"""Run Planner agent locally."""
import asyncio
from agents.planner.main import PlannerAgent

async def main():
    agent = PlannerAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Create run_mailer.py
    mailer_script = '''#!/usr/bin/env python3
"""Run Mailer agent locally."""
import asyncio
from agents.mailer.main import MailerAgent

async def main():
    agent = MailerAgent()
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    scripts = [
        ("run_market_analyst.py", market_analyst_script),
        ("run_planner.py", planner_script),
        ("run_mailer.py", mailer_script)
    ]
    
    try:
        for script_name, script_content in scripts:
            with open(script_name, "w") as f:
                f.write(script_content)
        print("✅ Created run scripts for local development")
        return True
    except Exception as e:
        print(f"❌ Failed to create run scripts: {e}")
        return False


async def main():
    """Main setup and validation function."""
    
    print("🚀 StockRipper v2 Local Development Setup")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Environment Setup", setup_environment),
        ("Dependencies", install_dependencies),
        ("Agent Imports", test_agent_imports),
        ("Run Scripts", create_run_script)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}...")
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
                
            if result:
                passed += 1
            else:
                print(f"❌ {check_name} failed")
                
        except Exception as e:
            print(f"❌ {check_name} failed with error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Setup Summary:")
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit your .env file with your API keys")
        print("2. Set up Gmail credentials (see credentials/README.md)")
        print("3. Run: python test_mcp_servers.py")
        print("4. Run individual agents:")
        print("   - python run_market_analyst.py")
        print("   - python run_planner.py") 
        print("   - python run_mailer.py")
    else:
        print(f"\n⚠️  Setup incomplete ({total - passed} issues)")
        print("Please fix the issues above before running agents.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

# Contains AI-generated edits.
