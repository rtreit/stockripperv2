"""
Planner Agent - A2A-compliant agent for trade planning using LangGraph
"""
import asyncio
from typing import Dict, Any, List
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


class PlannerAgent(BaseA2AAgent):
    """A2A-compliant Planner Agent with LangGraph"""
    
    def __init__(self):
        settings = get_settings()
        
        # MCP servers for trading tools
        mcp_servers = {
            "alpaca": {
                "url": settings.alpaca_mcp_url,
                "transport": "streamable_http"
            }
        }
        
        capabilities = {
            "trade_planning": True,
            "risk_management": True,
            "portfolio_optimization": True,
            "order_execution": True,
            "google_a2a_compatible": True
        }
        
        super().__init__(
            name="Trade Planner",
            description="Advanced trade planning and execution agent",
            url=settings.planner_url,
            version="1.0.0",
            mcp_servers=mcp_servers,
            capabilities=capabilities
        )
        
        self.settings = settings
        self.llm = self._setup_llm()
        self.planning_graph = None
    
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
        self._build_planning_graph()
    
    def _build_planning_graph(self) -> None:
        """Build LangGraph for trade planning workflow"""
        
        def plan_trade(state: MessagesState) -> Dict[str, Any]:
            """Plan trades using LLM and MCP tools"""
            messages = state["messages"]
            
            # Add system message for planning context
            system_msg = SystemMessage(content="""
            You are an expert trade planner. Create trading plans that include:
            1. Risk assessment and position sizing
            2. Entry and exit strategies
            3. Stop-loss and take-profit levels
            4. Market timing considerations
            5. Portfolio allocation recommendations
            
            Provide detailed, actionable trading plans with clear reasoning.
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
        builder.add_node("plan", plan_trade)
        
        if self.mcp_tools:
            builder.add_node("tools", ToolNode(self.mcp_tools))
            builder.add_edge(START, "plan")
            builder.add_conditional_edges(
                "plan",
                tools_condition,
            )
            builder.add_edge("tools", "plan")
        else:
            builder.add_edge(START, "plan")
        
        self.planning_graph = builder.compile()
    
    @skill(
        name="Create Trade Plan",
        description="Create comprehensive trade plan for a stock",
        tags=["trade", "plan", "strategy"]
    )
    async def create_trade_plan_skill(self, 
                                    ticker: str, 
                                    action: str = "buy",
                                    analysis: str = "") -> str:
        """Create a detailed trade plan"""
        try:
            # Get market analysis first
            market_analysis = ""
            if "market_analyst" in self.agent_clients:
                try:
                    market_analysis = await self.communicate_with_agent(
                        "market_analyst", 
                        f"Analyze stock {ticker}"
                    )
                except Exception as e:
                    self.logger.warning(f"Could not get market analysis: {e}")
            
            # Create planning context
            planning_context = f"""
            Create a trade plan for {ticker} ({action.upper()})
            
            Market Analysis: {market_analysis or analysis}
            
            Please provide a detailed plan including:
            - Position size recommendation
            - Entry strategy and price levels
            - Exit strategy (target prices)
            - Risk management (stop-loss levels)
            - Market timing considerations
            """
            
            # Use MCP tools for portfolio data if available
            if self.mcp_tools:
                try:
                    portfolio_data = await self.call_mcp_tool("get_portfolio")
                    planning_context += f"\nCurrent Portfolio: {portfolio_data}"
                except:
                    pass
            
            # Run LangGraph planning
            if self.planning_graph:
                result = await self.planning_graph.ainvoke({
                    "messages": [HumanMessage(content=planning_context)]
                })
                return result["messages"][-1].content
            else:
                # Fallback to direct LLM call
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a professional trade planner."),
                    HumanMessage(content=planning_context)
                ])
                return response.content
        
        except Exception as e:
            self.logger.error(f"Error creating trade plan for {ticker}: {e}")
            return f"Error creating trade plan: {str(e)}"
    
    @skill(
        name="Execute Trade",
        description="Execute a trade order",
        tags=["trade", "execute", "order"]
    )
    async def execute_trade_skill(self, 
                                ticker: str,
                                action: str,
                                quantity: int,
                                order_type: str = "market") -> str:
        """Execute a trade order"""
        try:
            # Use MCP tools to execute trade if available
            if self.mcp_tools:
                order_result = await self.call_mcp_tool(
                    "place_order",
                    symbol=ticker,
                    side=action.lower(),
                    qty=quantity,
                    type=order_type
                )
                return f"Trade executed: {order_result}"
            else:
                # Mock execution for demo
                return f"Mock trade executed: {action.upper()} {quantity} shares of {ticker} ({order_type} order)"
        
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return f"Error executing trade: {str(e)}"
    
    @skill(
        name="Portfolio Analysis",
        description="Analyze current portfolio and suggest optimizations",
        tags=["portfolio", "analysis", "optimization"]
    )
    async def portfolio_analysis_skill(self) -> str:
        """Analyze portfolio and suggest optimizations"""
        try:
            # Get portfolio data using MCP tools
            if self.mcp_tools:
                portfolio_data = await self.call_mcp_tool("get_portfolio")
                positions = await self.call_mcp_tool("get_positions")
                
                analysis_prompt = f"""
                Analyze this portfolio and provide optimization recommendations:
                
                Portfolio: {portfolio_data}
                Positions: {positions}
                
                Include:
                - Risk assessment
                - Diversification analysis
                - Rebalancing recommendations
                - Performance insights
                """
            else:
                analysis_prompt = "Provide general portfolio analysis best practices"
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a portfolio manager providing optimization advice."),
                HumanMessage(content=analysis_prompt)
            ])
            return response.content
        
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio: {e}")
            return f"Error analyzing portfolio: {str(e)}"
    
    async def process_task(self, task: Task) -> Task:
        """Process incoming A2A task"""
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            self.logger.info(f"Processing trade planning task: {text}")
            
            # Determine what type of planning to perform
            if "plan" in text.lower() and any(word in text.lower() for word in ["trade", "buy", "sell"]):
                # Extract ticker and action from message
                words = text.lower().split()
                ticker = None
                action = "buy"  # default
                
                for i, word in enumerate(words):
                    if word in ["buy", "sell"]:
                        action = word
                        if i + 1 < len(words):
                            ticker = words[i + 1].upper()
                    elif word in ["stock", "ticker"] and i + 1 < len(words):
                        ticker = words[i + 1].upper()
                
                if ticker:
                    result = await self.create_trade_plan_skill(ticker, action, text)
                else:
                    result = "Please specify a stock ticker and action (buy/sell)"
            
            elif "execute" in text.lower() and "trade" in text.lower():
                result = "Trade execution requires specific parameters. Please use the Execute Trade skill directly."
            
            elif "portfolio" in text.lower():
                result = await self.portfolio_analysis_skill()
            
            else:
                # General planning request
                if self.planning_graph:
                    graph_result = await self.planning_graph.ainvoke({
                        "messages": [HumanMessage(content=text)]
                    })
                    result = graph_result["messages"][-1].content
                else:
                    response = await self.llm.ainvoke([
                        SystemMessage(content="You are a helpful trade planning assistant."),
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
                    "content": {"type": "text", "text": f"Planning failed: {str(e)}"}
                }
            )
        
        return task


async def main():
    """Main entry point for the Planner agent"""
    settings = get_settings()
    setup_logging(settings)
    
    agent = PlannerAgent()
    await agent.setup()
    
    logger.info("Starting Trade Planner Agent", url=settings.planner_url)
    
    # Extract port from URL
    port = int(settings.planner_url.split(":")[-1])
    run_server(agent, host="0.0.0.0", port=port)


if __name__ == "__main__":
    asyncio.run(main())


# Contains AI-generated edits.
