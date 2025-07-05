"""
Market Analyst Agent - A2A-compliant agent for stock analysis using LangGraph
"""
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime

from python_a2a import skill
from python_a2a.models import Task, TaskStatus, TaskState
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage
import structlog

from agents.base import BaseA2AAgent
from config import get_settings, setup_logging


logger = structlog.get_logger(__name__)


class MarketAnalystAgent(BaseA2AAgent):
    """A2A-compliant Market Analyst Agent with LangGraph"""
    
    def __init__(self):
        settings = get_settings()        # MCP servers configuration (stdio commands like test_mcp_servers.py)
        mcp_servers = {
            "alpaca": {
                "command": ".venv\\Scripts\\python.exe",
                "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
                "env": {
                    "ALPACA_API_KEY": os.getenv("ALPACA_API_KEY", ""),
                    "ALPACA_SECRET_KEY": os.getenv("ALPACA_SECRET_KEY", ""),
                    "ALPACA_BASE_URL": os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
                    "PAPER": "True"
                }
            }
        }
        
        capabilities = {
            "stock_analysis": True,
            "market_research": True,
            "technical_analysis": True,
            "google_a2a_compatible": True
        }
        
        super().__init__(
            name="Market Analyst",
            description="Advanced stock market analysis and research agent",
            url=settings.market_analyst_url,
            version="1.0.0",
            mcp_servers=mcp_servers,
            capabilities=capabilities
        )
        
        self.settings = settings
        self.llm = self._setup_llm()
        self.analysis_graph = None
    
    def _setup_llm(self) -> Any:
        """Setup the LLM (OpenAI or Anthropic)"""
        if self.settings.openai_api_key:            return ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=self.settings.openai_api_key
            )
        elif self.settings.anthropic_api_key:
            return ChatAnthropic(
                model="claude-3-opus-20240229",
                temperature=0.1,
                api_key=self.settings.anthropic_api_key
            )
        else:
            raise ValueError("No LLM API key configured")
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Return detailed agent card for discovery"""
        return {
            "name": self.agent_card.name,
            "description": self.agent_card.description,
            "version": self.agent_card.version,
            "url": self.agent_card.url,
            "capabilities": self.agent_card.capabilities,
            "endpoints": {
                "health": f"{self.agent_card.url}/health",
                "discovery": f"{self.agent_card.url}/.well-known/agent.json",
                "analyze": f"{self.agent_card.url}/analyze"
            },
            "mcp_servers": list(self.mcp_servers_config.keys()),
            "status": "active"
        }
    
    async def setup(self) -> None:
        """Setup the agent and build the LangGraph"""
        await super().setup()
        self._build_analysis_graph()

    def _build_analysis_graph(self) -> None:
        """Build LangGraph for market analysis workflow"""
        
        def analyze_stock(state: MessagesState) -> Dict[str, Any]:
            """Analyze stock using LLM and MCP tools"""
            messages = state["messages"]
            
            # Add system message for analysis context
            system_msg = SystemMessage(content="""
            You are an expert stock market analyst. Analyze the given stock using:
            1. Technical indicators
            2. Fundamental analysis
            3. Market sentiment
            4. Risk assessment
            
            Provide specific, actionable insights and recommendations.
            """)
            
            # For now, use LLM without tools binding due to complexity of MCP integration
            # We can call MCP tools explicitly in the analysis if needed
            response = self.llm.invoke([system_msg] + messages)
            return {"messages": [response]}
        
        # Build the graph - simplified version without tool nodes for now
        builder = StateGraph(MessagesState)
        builder.add_node("analyze", analyze_stock)
        builder.add_edge(START, "analyze")
        
        self.analysis_graph = builder.compile()


    
    @skill(
        name="Analyze Stock",
        description="Perform comprehensive stock analysis",
        tags=["stock", "analysis", "market"]
    )
    async def analyze_stock_skill(self, ticker: str) -> str:
        """Analyze a specific stock ticker"""
        try:
            # Use MCP tools for data if available
            analysis_context = f"Analyzing {ticker}"
            
            if "alpaca" in self.mcp_clients:
                # Try to get stock data from Alpaca MCP server
                try:
                    # Get available tools first
                    alpaca_tools = await self.get_mcp_tools("alpaca")
                    self.logger.info(f"Available Alpaca tools: {[t.name for t in alpaca_tools]}")
                    
                    # Try to find a suitable tool for getting stock data
                    data_tool = None
                    for tool in alpaca_tools:
                        if any(keyword in tool.name.lower() for keyword in ['quote', 'price', 'stock', 'bars']):
                            data_tool = tool
                            break
                    
                    if data_tool:
                        self.logger.info(f"Using tool: {data_tool.name}")
                        stock_data = await self.call_mcp_tool("alpaca", data_tool.name, symbol=ticker)
                        analysis_context = f"Analyzing {ticker} with data: {stock_data}"
                    else:
                        self.logger.info("No suitable stock data tool found, using general analysis")
                        
                except Exception as e:
                    self.logger.warning(f"Error calling MCP tool: {e}")
            
            # Run LangGraph analysis
            if self.analysis_graph:
                result = await self.analysis_graph.ainvoke({
                    "messages": [HumanMessage(content=analysis_context)]
                })
                return result["messages"][-1].content
            else:
                # Fallback to direct LLM call
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a stock market analyst."),
                    HumanMessage(content=f"Analyze stock ticker {ticker}")
                ])
                return response.content
        
        except Exception as e:
            self.logger.error(f"Error analyzing stock {ticker}: {e}")
            return f"Error analyzing {ticker}: {str(e)}"
    
    @skill(
        name="Market Overview", 
        description="Get general market overview and trends",
        tags=["market", "overview", "trends"]
    )
    async def market_overview_skill(self) -> str:
        """Get market overview"""
        try:
            # Use MCP tools for market data if available
            analysis_prompt = "Provide current market overview and trends analysis"
            
            if "alpaca" in self.mcp_clients:
                try:
                    # Try to get market data from Alpaca
                    alpaca_tools = await self.get_mcp_tools("alpaca")
                    
                    # Look for market overview tools
                    market_tool = None
                    for tool in alpaca_tools:
                        if any(keyword in tool.name.lower() for keyword in ['market', 'overview', 'snapshot']):
                            market_tool = tool
                            break
                    
                    if market_tool:
                        market_data = await self.call_mcp_tool("alpaca", market_tool.name)
                        analysis_prompt = f"Provide market analysis based on: {market_data}"
                        
                except Exception as e:
                    self.logger.warning(f"Error getting market data from MCP: {e}")
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a market analyst providing daily market insights."),
                HumanMessage(content=analysis_prompt)
            ])
            return response.content
        
        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return f"Error getting market overview: {str(e)}"

    async def process_task(self, task: Task) -> Task:
        """Process incoming A2A task"""
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            self.logger.info(f"Processing market analysis task: {text}")
            
            # Determine what type of analysis to perform
            if "analyze" in text.lower() and any(word in text.lower() for word in ["stock", "ticker", "symbol"]):
                # Extract ticker from message
                words = text.split()
                ticker = None
                for i, word in enumerate(words):
                    if word.lower() in ["analyze", "stock", "ticker"] and i + 1 < len(words):
                        ticker = words[i + 1].upper()
                        break
                
                if ticker:
                    result = await self.analyze_stock_skill(ticker)
                else:
                    result = "Please specify a stock ticker to analyze"
            
            elif "market" in text.lower() and "overview" in text.lower():
                result = await self.market_overview_skill()
            
            else:
                # General market analysis
                if self.analysis_graph:
                    graph_result = await self.analysis_graph.ainvoke({
                        "messages": [HumanMessage(content=text)]
                    })
                    result = graph_result["messages"][-1].content
                else:
                    response = await self.llm.ainvoke([
                        SystemMessage(content="You are a helpful stock market analyst."),
                        HumanMessage(content=text)
                    ])
                    result = response.content
            
            # Set successful response
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"type": "text", "text": f"Analysis failed: {str(e)}"}
                }
            )
        
        return task

    async def setup_routes(self) -> None:
        """Setup additional FastAPI routes for testing"""
        
        @self.app.post("/analyze")
        async def analyze_endpoint(request: Dict[str, Any]):
            """Analyze endpoint for HTTP testing"""
            ticker = request.get("ticker", "AAPL")
            try:
                result = await self.analyze_stock_skill(ticker)
                return {"status": "success", "analysis": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @self.app.get("/market-overview")
        async def market_overview_endpoint():
            """Market overview endpoint for HTTP testing"""
            try:
                result = await self.market_overview_skill()
                return {"status": "success", "overview": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @self.app.get("/mcp-status")
        async def mcp_status_endpoint():
            """Check MCP server connection status"""
            return {
                "mcp_clients": {k: {"connected": bool(v)} for k, v in self.mcp_clients.items()},
                "mcp_tools": {k: len(v) if v else 0 for k, v in self.mcp_tools.items()},
                "available_servers": list(self.mcp_clients.keys())
            }


async def main():
    """Main entry point for the Market Analyst agent"""
    agent = MarketAnalystAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())


