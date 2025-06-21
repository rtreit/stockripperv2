"""
Base A2A Agent implementation using the latest python-a2a SDK
"""
import asyncio
import uuid
import subprocess
import json
import os
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from fastapi import FastAPI
import uvicorn
from python_a2a import A2AServer, skill, agent, AgentCard, A2AClient
from python_a2a.models import Task, TaskStatus, TaskState, Message, MessageRole
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
import structlog

from config import get_settings


logger = structlog.get_logger(__name__)


class BaseA2AAgent(A2AServer, ABC):
    """
    Base class for A2A-compliant agents with MCP integration via stdio
    """
    
    def __init__(self, 
                 name: str,
                 description: str,
                 url: str,
                 version: str = "1.0.0",
                 mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None,
                 capabilities: Optional[Dict[str, Any]] = None):
        """Initialize the A2A agent"""
        
        self.settings = get_settings()
        self.correlation_id = str(uuid.uuid4())
        
        # Create agent card
        agent_card = AgentCard(
            name=name,
            description=description,
            url=url,
            version=version,
            capabilities=capabilities or {}
        )
        
        super().__init__(agent_card=agent_card)        # MCP configuration and sessions
        self.mcp_servers_config = mcp_servers or {}
        self.mcp_sessions = {}
        self.mcp_client_managers = {}  # Store async context managers
        self.mcp_tools = {}
        
        # A2A clients for agent communication
        self.agent_clients = {}
        
        self.logger = logger.bind(
            agent_name=name,
            correlation_id=self.correlation_id
        )
        
        # FastAPI app for HTTP endpoints
        self.app = FastAPI(
            title=f"{name.title()} Agent",
            description=description,
            version=version
        )
        
        # Setup discovery endpoint
        self._setup_discovery_endpoint()
    
    def _setup_discovery_endpoint(self) -> None:
        """Setup the /.well-known/agent.json discovery endpoint"""
        
        @self.app.get("/.well-known/agent.json")
        async def agent_discovery():
            """Agent discovery endpoint per A2A protocol"""
            return self.get_agent_card()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "agent": self.agent_card.name}
        
        @self.app.get("/mcp-status")
        async def mcp_status():
            """MCP servers status endpoint"""
            status = {}
            for server_name, session in self.mcp_sessions.items():
                if hasattr(session, 'connected') and session.connected:
                    tools_count = len(self.mcp_tools.get(server_name, []))
                    status[server_name] = {
                        "connected": True,
                        "tools_count": tools_count
                    }
                else:
                    status[server_name] = {"connected": False}
            return {"mcp_servers": status}
    
    @abstractmethod
    def get_agent_card(self) -> Dict[str, Any]:
        """Return detailed agent card for discovery - to be implemented by subclasses"""
        pass    
    async def setup_routes(self) -> None:
        """Setup additional FastAPI routes - to be implemented by subclasses"""
        pass
    
    async def setup(self) -> None:
        """Setup the agent (initialize MCP servers, etc.)"""        # Connect to external MCP servers
        await self._start_mcp_servers()
        
        # Setup agent clients for cross-agent communication
        self._setup_agent_clients()
    async def _start_mcp_servers(self) -> None:
        """Connect to external MCP servers (parallel for faster startup)"""
        self.logger.info("Connecting to external MCP servers...")
        
        # Start all MCP server connections in parallel
        tasks = []
        for server_name, config in self.mcp_servers_config.items():
            task = asyncio.create_task(
                self._connect_to_mcp_server(server_name, config),
                name=f"mcp_connect_{server_name}"
            )
            tasks.append(task)
        
        # Wait for all connections to complete (or timeout)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Completed MCP servers connection")
    
    async def _connect_to_mcp_server(self, server_name: str, config: Dict[str, Any]) -> None:
        """Connect to an MCP server via stdio"""
        self.logger.info(f"[{server_name}] Connecting to MCP server via stdio")
        
        # Get command from config
        command = config.get("command")
        if not command:
            self.logger.error(f"[{server_name}] No command specified in config")
            return        
        self.logger.info(f"[{server_name}] Command: {command}")
        
        try:            # Create stdio server parameters
            server_params = StdioServerParameters(
                command=command[0],
                args=command[1:] if len(command) > 1 else [],
                env=None
            )
              # Create stdio client and session with timeout
            stdio_client_manager = stdio_client(server_params)
            self.mcp_client_managers[server_name] = stdio_client_manager            # Enter the async context to start the server with timeout
            (read_stream, write_stream) = await asyncio.wait_for(
                stdio_client_manager.__aenter__(), 
                timeout=10.0
            )
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session with timeout
            await asyncio.wait_for(session.initialize(), timeout=2.0)
            
            # Store the session
            self.mcp_sessions[server_name] = session
            
            # Get available tools from the server with timeout
            tools = await asyncio.wait_for(session.list_tools(), timeout=1.0)
            self.mcp_tools[server_name] = tools.tools
            
            self.logger.info(f"[{server_name}] Connected successfully with {len(tools.tools)} tools")
                        
        except asyncio.TimeoutError:
            self.logger.warning(f"[{server_name}] Timeout connecting to MCP server")
        except Exception as e:
            self.logger.warning(f"[{server_name}] Failed to connect to MCP server: {e}")
            # Continue without this MCP server - agent can still run
            self.mcp_sessions[server_name] = None
            self.mcp_tools[server_name] = []
    
    async def cleanup(self) -> None:
        """Cleanup MCP client managers and sessions"""
        # Close MCP client managers (which will also close sessions and subprocesses)
        for server_name, client_manager in self.mcp_client_managers.items():
            try:
                await client_manager.__aexit__(None, None, None)
                self.logger.info(f"Closed MCP client manager: {server_name}")
            except Exception as e:
                self.logger.error(f"Error closing MCP client manager {server_name}: {e}")
    
    async def run(self) -> None:
        """Run the agent with both A2A and HTTP servers"""
        try:
            # Setup MCP and routes
            await self.setup()
            await self.setup_routes()
            
            # Extract port from URL
            url_parts = self.agent_card.url.split(":")
            port = int(url_parts[-1]) if len(url_parts) > 2 else 8000
            
            # Run FastAPI server
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            self.logger.info(f"Starting {self.agent_card.name} agent on port {port}")
            await server.serve()
            
        finally:
            # Cleanup on shutdown
            await self.cleanup()
    
    def _setup_agent_clients(self) -> None:
        """Setup A2A clients for communicating with other agents"""
        agent_urls = {
            "market_analyst": self.settings.market_analyst_url,
            "planner": self.settings.planner_url,
            "mailer": self.settings.mailer_url,        }
        
        for agent_name, url in agent_urls.items():
            if url != self.agent_card.url:  # Don't create client for self
                self.agent_clients[agent_name] = A2AClient(url)
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool from a specific server"""
        if server_name not in self.mcp_sessions:
            raise ValueError(f"MCP server '{server_name}' not available")
        
        session = self.mcp_sessions[server_name]
        if not session:
            raise ValueError(f"MCP server '{server_name}' not connected")
        
        if server_name not in self.mcp_tools:
            raise ValueError(f"No tools available for MCP server '{server_name}'")
        
        # Find the tool
        tools = self.mcp_tools[server_name]
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in server '{server_name}'")
        
        try:
            # Call the tool using the MCP session
            result = await session.call_tool(tool_name, kwargs)
            self.logger.info(f"Called MCP tool {tool_name} on {server_name}", result=result)
            return result
        except Exception as e:
            self.logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {e}")
            raise
    
    async def get_mcp_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """Get MCP tools, optionally filtered by server name"""
        if server_name:
            return self.mcp_tools.get(server_name, [])
        
        # Return all tools from all servers
        all_tools = []
        for tools in self.mcp_tools.values():
            all_tools.extend(tools)
        return all_tools
    
    async def list_mcp_servers(self) -> List[str]:
        """List available MCP server names"""
        return list(self.mcp_sessions.keys())
    
    async def communicate_with_agent(self,
                                   agent_name: str, 
                                   message: str) -> str:
        """Send a message to another agent"""
        if agent_name not in self.agent_clients:
            raise ValueError(f"No client for agent '{agent_name}'")
        
        client = self.agent_clients[agent_name]
        try:
            response = await client.ask(message)
            self.logger.info(f"Communicated with {agent_name}", 
                           message=message, response=response)
            return response
        except Exception as e:
            self.logger.error(f"Error communicating with {agent_name}: {e}")
            raise
    
    @abstractmethod
    async def process_task(self, task: Task) -> Task:
        """Process an A2A task - to be implemented by subclasses"""
        pass
    
    def handle_task(self, task: Task) -> Task:
        """Handle incoming A2A task (sync wrapper for async process_task)"""
        try:
            # Add correlation ID
            task.correlation_id = self.correlation_id
            
            # Run async task processing
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.process_task(task))
        except Exception as e:
            self.logger.error(f"Error handling task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent", 
                    "content": {"type": "text", "text": f"Task failed: {str(e)}"}
                }
            )
            return task


# Contains AI-generated edits.
