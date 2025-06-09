#!/usr/bin/env python3
"""
Secure Environment Setup Script for StockRipper A2A/MCP

This script helps set up the environment securely without exposing secrets.
"""

import os
import json
import getpass
from pathlib import Path
from typing import Dict, Optional


def create_secure_env_file():
    """Create .env file from .env.example with user input."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    if env_file.exists():
        overwrite = input("🔄 .env already exists. Overwrite? (y/N): ")
        if overwrite.lower() != 'y':
            return False
    
    print("🔐 Setting up secure environment configuration...")
    print("📝 Enter your API keys and credentials (input will be hidden)")
    
    # Read template
    with open(env_example) as f:
        template = f.read()
    
    # Sensitive keys that should be hidden during input
    sensitive_keys = {
        'OPENAI_API_KEY': 'OpenAI API Key (sk-...)',
        'ANTHROPIC_API_KEY': 'Anthropic API Key',
        'ALPACA_API_KEY': 'Alpaca API Key',
        'ALPACA_SECRET_KEY': 'Alpaca Secret Key',
        'GMAIL_CLIENT_SECRET': 'Gmail Client Secret',
    }
    
    # Non-sensitive keys that can be shown
    regular_keys = {
        'GMAIL_CLIENT_ID': 'Gmail Client ID',
        'ALPACA_BASE_URL': 'Alpaca Base URL (paper-api.alpaca.markets or api.alpaca.markets)',
        'GMAIL_TOKEN_PATH': 'Gmail Token Path (./credentials/gmail_token.json)',
    }
    
    values = {}
    
    # Get sensitive values
    for key, description in sensitive_keys.items():
        while True:
            value = getpass.getpass(f"🔑 {description}: ")
            if value.strip():
                values[key] = value.strip()
                break
            print("❌ Value cannot be empty")
    
    # Get regular values
    for key, description in regular_keys.items():
        value = input(f"📋 {description}: ").strip()
        if value:
            values[key] = value
    
    # Replace placeholders in template
    result = template
    for key, value in values.items():
        placeholder = f"your-{key.lower().replace('_', '-')}-here"
        if placeholder in result:
            result = result.replace(placeholder, value)
        else:
            # Handle variations
            result = result.replace(f"{key}=", f"{key}={value}")
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(result)
    
    # Set secure permissions
    os.chmod(env_file, 0o600)
    print(f"✅ Created {env_file} with secure permissions (600)")
    return True


def create_vscode_mcp_config():
    """Create a secure VS Code MCP configuration."""
    vscode_dir = Path(".vscode")
    mcp_file = vscode_dir / "mcp.json"
    
    if not vscode_dir.exists():
        vscode_dir.mkdir()
    
    if mcp_file.exists():
        overwrite = input("🔄 .vscode/mcp.json exists. Create secure version? (y/N): ")
        if overwrite.lower() != 'y':
            return False
    
    print("🔧 Creating secure VS Code MCP configuration...")
    
    # Get API keys securely
    github_token = getpass.getpass("🔑 GitHub Personal Access Token (optional): ").strip()
    brave_key = getpass.getpass("🔑 Brave Search API Key (optional): ").strip()
    
    config = {
        "servers": {
            "github": {
                "command": "docker",
                "args": [
                    "run", "-i", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "mcp/github"
                ],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": github_token or "your-github-token-here"
                }
            },
            "brave-search": {
                "command": "docker",
                "args": [
                    "run", "-i", "-e", "BRAVE_API_KEY", "mcp/brave-search"
                ],
                "env": {
                    "BRAVE_API_KEY": brave_key or "your-brave-api-key-here"
                }
            },
            "context7": {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"]
            },
            "memory": {
                "command": "npx",
                "args": ["-y", "@mcp-server/memory"]
            }
        }
    }
    
    with open(mcp_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    os.chmod(mcp_file, 0o600)
    print(f"✅ Created {mcp_file} with secure permissions")
    return True


def create_credentials_directory():
    """Create credentials directory with proper security."""
    creds_dir = Path("credentials")
    if not creds_dir.exists():
        creds_dir.mkdir()
        os.chmod(creds_dir, 0o700)
        print("✅ Created credentials/ directory with secure permissions (700)")
    
    # Create placeholder files with secure permissions
    for filename in ["gmail_credentials.json.example", "gmail_token.json.example"]:
        placeholder_file = creds_dir / filename
        if not placeholder_file.exists():
            with open(placeholder_file, 'w') as f:
                json.dump({
                    "note": "This is a placeholder. Replace with real credentials.",
                    "warning": "Never commit real credentials to Git!"
                }, f, indent=2)
            os.chmod(placeholder_file, 0o600)


def check_gitignore():
    """Verify .gitignore has all necessary exclusions."""
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print("❌ .gitignore not found")
        return False
    
    with open(gitignore) as f:
        content = f.read()
    
    required_patterns = [
        ".env",
        "credentials/",
        "*.json",
        "*secret*",
        "*key*",
        "*token*",
        "rendered-templates.yaml"
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        print(f"⚠️  Missing patterns in .gitignore: {missing}")
        return False
    
    print("✅ .gitignore has required security patterns")
    return True


def main():
    """Main setup function."""
    print("🚀 StockRipper A2A/MCP Secure Setup")
    print("=" * 40)
    
    # Check current directory
    if not Path("pyproject.toml").exists():
        print("❌ Run this script from the StockRipper root directory")
        return
    
    # Security checks
    print("\n1. Checking .gitignore security...")
    check_gitignore()
    
    print("\n2. Setting up credentials directory...")
    create_credentials_directory()
    
    print("\n3. Creating secure environment file...")
    if create_secure_env_file():
        print("✅ Environment configured securely")
    
    print("\n4. Setting up VS Code MCP configuration...")
    if create_vscode_mcp_config():
        print("✅ VS Code MCP configuration created")
    
    print("\n🔒 Security Reminders:")
    print("• Never commit .env files or real credentials")
    print("• Use environment variables in production")
    print("• Regularly rotate API keys and secrets")
    print("• Review SECURITY.md for complete guidelines")
    print("\n✅ Setup complete! Your secrets are secure.")


if __name__ == "__main__":
    main()

# Contains AI-generated edits.
