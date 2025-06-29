"""
Base A2A Agent implementation using the latest python-a2a SDK
"""
import asyncio
import uuid
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from fastapi import FastAPI
import uvicorn
from python_a2a import A2AServer, skill, agent, AgentCard, A2AClient
from python_a2a.models import Task, TaskStatus, TaskState, Message, MessageRole
from fastmcp import Client
from fastmcp.exceptions import ClientError, McpError
import structlog

from config import get_settings


logger = structlog.get_logger(__name__)


class BaseA2AAgent(A2AServer, ABC):
    """
    Base class for A2A-compliant agents with MCP integration
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

        super().__init__(agent_card=agent_card)

        # MCP configuration and clients
        self.mcp_servers_config = mcp_servers or {}
        self.mcp_clients: Dict[str, Client] = {}
        self.mcp_tools: Dict[str, List[Any]] = {}

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
            for server_name in self.mcp_servers_config:
                # A good indicator of a successful connection is if we have loaded tools.
                tools_loaded = server_name in self.mcp_tools
                tools_count = len(self.mcp_tools.get(server_name, []))
                status[server_name] = {
                    "initialized_successfully": tools_loaded,
                    "tools_count": tools_count,
                }
            return {"mcp_servers": status}

    @abstractmethod
    def get_agent_card(self) -> Dict[str, Any]:
        """Return detailed agent card for discovery - to be implemented by subclasses"""
        pass

    async def setup_routes(self) -> None:
        """Setup additional FastAPI routes - to be implemented by subclasses"""
        pass

    async def setup(self) -> None:
        """Setup the agent (initialize MCP servers, etc.)"""
        # Connect to external MCP servers
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
        """Connect to an MCP server using the fastmcp.Client to list tools."""
        self.logger.info(f"[{server_name}] Initializing MCP client...")

        # The FastMCP client expects a specific config format.
        client_config = {"mcpServers": {server_name: config}}
        client = Client(client_config)
        self.mcp_clients[server_name] = client

        try:
            # The `async with` block handles connection and initialization.
            # For stdio, the client's subprocess is kept alive by default,
            # allowing subsequent connections without restarting the process.
            async with client:
                self.logger.info(f"[{server_name}] Client session started, listing tools...")

                # The client automatically lists tools on connection.
                tools = await client.list_tools()

                if tools:
                    self.mcp_tools[server_name] = tools
                    self.logger.info(f"[{server_name}] Found {len(tools)} tools.")
                    for tool in tools[:3]:  # Log first 3 tools
                        self.logger.info(f"[{server_name}]   - Tool: {tool.name}")
                else:
                    self.mcp_tools[server_name] = []
                    self.logger.warning(f"[{server_name}] Connected, but no tools found.")

        except (ClientError, McpError, asyncio.TimeoutError) as e:
            self.logger.error(f"[{server_name}] Failed to connect or list tools: {e}")
            self.mcp_tools[server_name] = []
        except Exception as e:
            self.logger.error(f"[{server_name}] An unexpected error occurred: {e}", exc_info=True)
            self.mcp_tools[server_name] = []

    async def cleanup(self) -> None:
        """Cleanup MCP processes and sessions"""
        self.logger.info("Closing all MCP client connections...")
        tasks = []
        for server_name, client in self.mcp_clients.items():
            task = asyncio.create_task(self._close_client(server_name, client))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _close_client(self, server_name: str, client: Client):
        try:
            await client.close()
            self.logger.info(f"Closed MCP client connection: {server_name}")
        except Exception as e:
            self.logger.error(f"Error closing MCP client {server_name}: {e}")

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
            "mailer": self.settings.mailer_url,
        }

        for agent_name, url in agent_urls.items():
            if url != self.agent_card.url:  # Don't create client for self
                self.agent_clients[agent_name] = A2AClient(url)

    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool from a specific server using fastmcp.Client"""
        if server_name not in self.mcp_clients:
            raise ValueError(f"MCP server '{server_name}' not available")

        client = self.mcp_clients[server_name]
        self.logger.info(f"Calling tool '{tool_name}' on server '{server_name}' with args: {kwargs}")

        try:
            # Re-establish connection for the tool call.
            # The underlying subprocess is reused for stdio transports.
            async with client:
                result = await client.call_tool(tool_name, arguments=kwargs)

            self.logger.info(f"Called MCP tool {tool_name} on {server_name} successfully")
            
            # The result from call_tool is a list of content objects.
            # For simplicity, we can extract text from the first content object if it exists.
            if result and hasattr(result[0], 'text'):
                return result[0].text
            return result

        except (ClientError, McpError) as e:
            self.logger.error(f"Error calling MCP tool {tool_name} on {server_name}: {e}")
            raise Exception(f"MCP tool error: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error calling MCP tool {tool_name} on {server_name}: {e}")
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
        return list(self.mcp_clients.keys())

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

    async def get_langchain_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """Get MCP tools converted to LangChain-compatible format"""
        from langchain_core.tools import BaseTool
        from typing import Type
        from pydantic import BaseModel, Field
        
        mcp_tools = await self.get_mcp_tools(server_name)
        langchain_tools = []
        
        for mcp_tool in mcp_tools:
            # Create a closure to capture the tool reference
            def make_tool_func(tool_ref):
                async def tool_func(**kwargs):
                    """Execute the MCP tool"""
                    try:
                        result = await self.call_mcp_tool(tool_ref.name, **kwargs)
                        return str(result)
                    except Exception as e:
                        return f"Error calling tool {tool_ref.name}: {e}"
                
                # Set the function metadata
                tool_func.__name__ = tool_ref.name
                tool_func.__doc__ = tool_ref.description or f"MCP tool: {tool_ref.name}"
                return tool_func
            
            # Create the tool function with proper closure
            tool_function = make_tool_func(mcp_tool)
            
            # Create LangChain tool using the function
            from langchain_core.tools import tool
            langchain_tool = tool(tool_function)
            langchain_tools.append(langchain_tool)
        
        return langchain_tools
