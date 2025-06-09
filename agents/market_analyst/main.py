"""
Market Analyst Agent - A2A-compliant agent for stock analysis using LangGraph
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from python_a2a import skill, run_server
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
        settings = get_settings()
        
        # MCP servers for market data and tools
        mcp_servers = {
            "alpaca": {
                "url": settings.alpaca_mcp_url,
                "transport": "streamable_http"
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
        if self.settings.openai_api_key:
            return ChatOpenAI(
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
            
            # Bind MCP tools if available
            if self.mcp_tools:
                llm_with_tools = self.llm.bind_tools(self.mcp_tools)
            else:
                llm_with_tools = self.llm
            
            response = llm_with_tools.invoke([system_msg] + messages)
            return {"messages": [response]}
        
        # Build the graph
        builder = StateGraph(MessagesState)
        builder.add_node("analyze", analyze_stock)
        
        if self.mcp_tools:
            builder.add_node("tools", ToolNode(self.mcp_tools))
            builder.add_edge(START, "analyze")
            builder.add_conditional_edges(
                "analyze",
                tools_condition,
            )
            builder.add_edge("tools", "analyze")
        else:
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
            if self.mcp_tools:
                stock_data = await self.call_mcp_tool("get_stock_data", symbol=ticker)
                analysis_context = f"Analyzing {ticker} with data: {stock_data}"
            else:
                analysis_context = f"Analyzing {ticker} (using general knowledge)"
            
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
            if self.mcp_tools:
                market_data = await self.call_mcp_tool("get_market_overview")
                analysis_prompt = f"Provide market analysis based on: {market_data}"
            else:
                analysis_prompt = "Provide current market overview and trends analysis"
            
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


async def main():
    """Main entry point for the Market Analyst agent"""
    settings = get_settings()
    setup_logging(settings)
    
    agent = MarketAnalystAgent()
    await agent.setup()
    
    logger.info("Starting Market Analyst Agent", url=settings.market_analyst_url)
    
    # Extract port from URL
    port = int(settings.market_analyst_url.split(":")[-1])
    run_server(agent, host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())


# Contains AI-generated edits.
