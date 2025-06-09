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
from langchain_mcp_adapters.client import MultiServerMCPClient
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
        
        # MCP client for tool access
        self.mcp_client = None
        if mcp_servers:
            self.mcp_client = MultiServerMCPClient(mcp_servers)
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
    
    @abstractmethod
    def get_agent_card(self) -> Dict[str, Any]:
        """Return detailed agent card for discovery - to be implemented by subclasses"""
        pass
    
    async def setup_routes(self) -> None:
        """Setup additional FastAPI routes - to be implemented by subclasses"""
        pass
    
    async def run(self) -> None:
        """Run the agent with both A2A and HTTP servers"""
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
    
    async def setup(self) -> None:
        """Setup the agent (initialize MCP, etc.)"""
        if self.mcp_client:
            try:
                # Initialize MCP tools
                self.mcp_tools = await self.mcp_client.get_tools()
                self.logger.info(f"Loaded {len(self.mcp_tools)} MCP tools")
            except Exception as e:
                self.logger.error(f"Failed to setup MCP client: {e}")
                self.mcp_tools = []
        
        # Setup agent clients for cross-agent communication
        self._setup_agent_clients()
    
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
    
    async def call_mcp_tool(self, tool_name: str, **kwargs) -> Any:
        """Call an MCP tool if available"""
        if not self.mcp_tools:
            raise ValueError("No MCP tools available")
          # Find the tool
        tool = next((t for t in self.mcp_tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            result = await tool.ainvoke(kwargs)
            self.logger.info(f"Called MCP tool {tool_name}", result=result)
            return result
        except Exception as e:
            self.logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise
    
    async def get_mcp_tools(self, server_name: Optional[str] = None) -> List[Any]:
        """Get MCP tools, optionally filtered by server name"""
        if not self.mcp_tools:
            return []
        
        if server_name:
            # Filter by server name (this would require server metadata in real implementation)
            return [tool for tool in self.mcp_tools if hasattr(tool, 'server') and tool.server == server_name]
        
        return self.mcp_tools
    
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
