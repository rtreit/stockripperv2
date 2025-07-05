"""
Market Analyst Agent - A2A-compliant agent for stock analysis using MCP tools and A2A discovery
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
import structlog

from agents.base import BaseA2AAgent, A2AClient, Task, TaskStatus, TaskState
from config import get_settings


logger = structlog.get_logger(__name__)


class MessagesState(TypedDict):
    """State for the analysis workflow."""
    messages: Annotated[list, add_messages]


class StockResearchAgent(BaseA2AAgent):
    """A2A-compliant Stock Research Agent with MCP tools and A2A discovery"""
    
    def __init__(self):
        """Initialize the Stock Research Agent."""
        settings = get_settings()
        
        # Define MCP servers for real stock data
        mcp_servers = {
            "alpaca": {
                "command": "python",
                "args": ["./mcp_servers/alpaca/alpaca_mcp_server.py"],
                "env": {
                    "ALPACA_API_KEY": settings.alpaca_api_key,
                    "ALPACA_SECRET_KEY": settings.alpaca_secret_key,
                    "ALPACA_BASE_URL": settings.alpaca_base_url,
                    "PAPER": settings.paper
                }
            }
        }
        
        capabilities = {
            "stock_analysis": True,
            "market_research": True,
            "technical_analysis": True,
            "email_integration": True,
            "a2a_discovery": True,
            "mcp_integration": True
        }

        # Call the BaseA2AAgent constructor
        super().__init__(
            name="Stock Research Agent",
            description="Professional stock analysis and market research agent with email integration",
            url=settings.market_analyst_url,
            version="1.0.0",
            mcp_servers=mcp_servers,
            capabilities=capabilities,
        )

        self.settings = settings
        self.llm = self._setup_llm()
        self.analysis_graph = None
        
        # Setup A2A client for Mailer discovery and communication
        self.mailer_client = A2AClient(self.settings.mailer_url)
        logger.info(f"Mailer A2A client initialized for URL: {self.settings.mailer_url}")
    
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
            logger.warning("No LLM API key configured, using mock responses")
            return None
    
    @skill(
        name="Analyze Stock",
        description="Perform comprehensive stock analysis for any ticker symbol",
        tags=["stock", "analysis", "financial"],
        examples=["Analyze stock AAPL", "What's your analysis of TSLA?", "Give me a stock analysis for IBM"]
    )
    def analyze_stock(self, ticker: str = "AAPL") -> str:
        """Analyze a specific stock ticker with comprehensive market insights"""
        try:
            logger.info(f"Analyzing stock: {ticker}")
            
            if self.llm:
                prompt = f"""
                Provide a comprehensive analysis of stock ticker {ticker} including:
                1. Current market position and recent performance
                2. Key financial metrics and ratios  
                3. Technical analysis overview
                4. Fundamental analysis highlights
                5. Risk assessment
                6. Investment recommendation with rationale
                
                Make this analysis specific, actionable, and professional.
                """
                
                response = self.llm.invoke([
                    SystemMessage(content="You are an expert stock market analyst with deep knowledge of financial markets, technical analysis, and fundamental analysis."),
                    HumanMessage(content=prompt)
                ])
                return response.content
            else:
                return f"""
                **Stock Analysis for {ticker.upper()}**
                
                📈 **Current Position**: {ticker} is trading in a volatile market environment with mixed signals from technical indicators.
                
                💰 **Key Metrics**: 
                - P/E Ratio: Moderate relative to sector peers
                - Revenue Growth: Stable with quarterly fluctuations
                - Market Cap: Large-cap equity with established market presence
                
                📊 **Technical Analysis**: 
                - Support levels holding at recent lows
                - Resistance at previous highs creating consolidation pattern
                - Volume trends suggest institutional interest
                
                🔍 **Fundamental Analysis**:
                - Strong business fundamentals with competitive advantages
                - Market position remains solid in core segments
                - Management execution on strategic initiatives
                
                ⚠️ **Risk Assessment**: 
                - Moderate risk profile with sector-specific headwinds
                - Regulatory environment considerations
                - Market volatility impact
                
                💡 **Recommendation**: Hold/Monitor - Suitable for long-term investors with risk tolerance
                
                *Note: This is a sample analysis. For real-time data and professional advice, please consult financial professionals.*
                """
        
        except Exception as e:
            logger.error(f"Error analyzing stock {ticker}: {e}")
            return f"Unable to analyze {ticker} at this time. Error: {str(e)}"
    
    @skill(
        name="Market Overview",
        description="Get comprehensive market overview and current trends",
        tags=["market", "overview", "trends", "indices"],
        examples=["Give me a market overview", "What are the current market trends?", "How is the market performing today?"]
    )
    def market_overview(self) -> str:
        """Get comprehensive market overview with current trends and sentiment"""
        try:
            if self.llm:
                prompt = """
                Provide a comprehensive market overview including:
                1. Current market sentiment and major indices performance
                2. Sector analysis and rotation trends
                3. Key economic indicators and their impact
                4. Notable market drivers and events
                5. Outlook for the near term
                6. Risk factors to watch
                
                Focus on actionable insights for investors.
                """
                
                response = self.llm.invoke([
                    SystemMessage(content="You are a senior market analyst providing daily market insights and strategic guidance to institutional investors."),
                    HumanMessage(content=prompt)
                ])
                return response.content
            else:
                return """
                **Market Overview & Analysis**
                
                📊 **Current Market Sentiment**: 
                Markets are showing mixed signals with defensive positioning amid economic uncertainty. Volatility remains elevated as investors await key economic data releases.
                
                📈 **Major Indices Performance**:
                - S&P 500: Consolidating near key support levels
                - NASDAQ: Technology sector showing resilience
                - Dow Jones: Value stocks outperforming in recent sessions
                
                🏭 **Sector Analysis**:
                - Technology: Mixed performance with selective strength
                - Healthcare: Defensive positioning attracting flows
                - Energy: Commodity price sensitivity creating volatility
                - Financial: Interest rate environment creating opportunities
                
                📊 **Key Economic Indicators**:
                - Employment data showing labor market resilience
                - Inflation trends moderating but remain elevated
                - Consumer confidence fluctuating with economic data
                
                🎯 **Market Drivers**:
                - Federal Reserve monetary policy expectations
                - Geopolitical developments affecting risk sentiment
                - Corporate earnings season guidance and results
                
                🔮 **Near-term Outlook**:
                Cautious optimism with focus on economic data releases and corporate earnings. Market likely to remain range-bound pending clarity on key macro factors.
                
                ⚠️ **Risk Factors**:
                - Monetary policy uncertainty
                - Geopolitical tensions
                - Supply chain disruptions
                
                *Note: This is a sample overview. For real-time market data and professional advice, please consult financial professionals.*
                """
        
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return f"Unable to provide market overview at this time. Error: {str(e)}"

    def handle_task(self, task):
        """Handle incoming A2A tasks by routing to appropriate skills"""
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            logger.info(f"Processing market analysis task: {text}")
            
            # Route to appropriate skill based on content
            result = None
            text_lower = text.lower()
            
            if "analyze" in text_lower and any(word in text_lower for word in ["stock", "ticker", "symbol"]):
                # Extract ticker from message
                import re
                ticker_match = re.search(r'\b([A-Z]{1,5})\b', text.upper())
                if ticker_match:
                    ticker = ticker_match.group(1)
                    result = self.analyze_stock(ticker)
                else:
                    # Try to find ticker in various formats
                    words = text.split()
                    ticker = None
                    for i, word in enumerate(words):
                        if word.lower() in ["analyze", "stock", "ticker"] and i + 1 < len(words):
                            ticker = words[i + 1].upper()
                            break
                    
                    if ticker:
                        result = self.analyze_stock(ticker)
                    else:
                        result = "Please specify a stock ticker to analyze (e.g., 'Analyze stock AAPL')"
            
            elif "market" in text_lower and any(word in text_lower for word in ["overview", "trends", "sentiment"]):
                result = self.market_overview()
            
            else:
                # Default response for general queries
                result = (
                    "I'm a Market Analyst agent specializing in stock analysis and market research. I can help with:\n\n"
                    "📈 **Stock Analysis**: 'Analyze stock AAPL' - Get comprehensive analysis of any stock\n"
                    "📊 **Market Overview**: 'Give me a market overview' - Current market trends and sentiment\n\n"
                    "Please specify what kind of analysis you'd like!"
                )
            
            # Set successful response
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"type": "text", "text": f"Analysis failed: {str(e)}"}
                }
            )
        
        return task


def main():
    """Main entry point for the Stock Research agent"""
    agent = StockResearchAgent()
    
    logger.info("Starting Stock Research Agent")
    
    run_server(agent, host="0.0.0.0", port=8009)


if __name__ == "__main__":
    main()


# Contains AI-generated edits.
