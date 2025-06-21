#!/usr/bin/env python3
"""
Start both MCP servers for development and testing
"""

import asyncio
import subprocess
import time
from pathlib import Path

def start_mcp_server(name: str, command: list, port: int):
    """Start an MCP server as a background process"""
    print(f"🚀 Starting {name} MCP Server on port {port}...")
    
    # Use the venv python
    venv_python = str(Path(".venv") / "Scripts" / "python.exe")
    full_command = [venv_python] + command
    
    process = subprocess.Popen(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"   ✅ {name} MCP Server started (PID: {process.pid})")
    return process

def main():
    """Start all MCP servers"""
    print("🔧 Starting MCP Servers for StockRipper v2")
    print("=" * 50)
    
    servers = []
    
    try:
        # Start Alpaca MCP Server
        alpaca_process = start_mcp_server(
            "Alpaca",
            ["./mcp_servers/alpaca/alpaca_mcp_server.py", "--transport", "streamable-http"],
            8000
        )
        servers.append(("Alpaca", alpaca_process))
        
        # Start Gmail MCP Server  
        gmail_process = start_mcp_server(
            "Gmail",
            ["./mcp_servers/gmail/main.py", "--transport", "streamable-http"],
            8004
        )
        servers.append(("Gmail", gmail_process))
        
        print(f"\n🎉 All MCP servers started successfully!")
        print(f"📊 Alpaca MCP Server: http://localhost:8000")
        print(f"📧 Gmail MCP Server: http://localhost:8004")
        print(f"\n💡 You can now run agents that will connect to these servers.")
        print(f"🛑 Press Ctrl+C to stop all servers")
        
        # Wait for interrupt
        try:
            while True:
                time.sleep(1)
                # Check if any process died
                for name, process in servers:
                    if process.poll() is not None:
                        print(f"⚠️  {name} MCP Server died (exit code: {process.returncode})")
                        return
        except KeyboardInterrupt:
            print(f"\n🛑 Shutting down MCP servers...")
            
    finally:
        # Clean up processes
        for name, process in servers:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"   ✅ {name} MCP Server stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"   🔪 {name} MCP Server force killed")
            except Exception as e:
                print(f"   ❌ Error stopping {name} MCP Server: {e}")

if __name__ == "__main__":
    main()

# Contains AI-generated edits.
