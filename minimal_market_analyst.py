"""
Minimal Market Analyst Agent based on working test agent pattern
"""
import os
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import structlog

logger = structlog.get_logger(__name__)


@agent(
    name="Market Analyst",
    description="Stock analysis and market research agent",
    version="1.0.0",
    url="http://localhost:8001"
)
class MarketAnalystAgent(A2AServer):
    """Market Analyst Agent"""
    
    @skill(
        name="Analyze Stock",
        description="Perform comprehensive stock analysis for any ticker symbol",
        tags=["stock", "analysis"],
        examples=["Analyze stock AAPL", "Analyze IBM"]
    )
    def analyze_stock(self, ticker: str = "AAPL") -> str:
        """Analyze a specific stock ticker"""
        return f"""
        **Stock Analysis for {ticker.upper()}**
        
        📈 **Current Position**: {ticker} is trading with mixed market signals.
        
        💰 **Key Metrics**: 
        - P/E Ratio: Moderate relative to sector peers
        - Revenue Growth: Stable with quarterly fluctuations
        
        📊 **Technical Analysis**: 
        - Support levels holding at recent lows
        - Volume trends suggest institutional interest
        
        💡 **Recommendation**: Hold/Monitor - Suitable for long-term investors
        
        *Sample analysis for demonstration purposes.*
        """
    
    @skill(
        name="Market Overview",
        description="Get comprehensive market overview and current trends",
        tags=["market", "overview"],
        examples=["Market overview", "Current market trends"]
    )
    def market_overview(self) -> str:
        """Get market overview"""
        return """
        **Market Overview**
        
        📊 **Current Sentiment**: Markets showing mixed signals with defensive positioning.
        
        📈 **Major Indices**:
        - S&P 500: Consolidating near key support levels
        - NASDAQ: Technology sector showing resilience
        
        🔮 **Outlook**: Cautious optimism with focus on economic data releases.
        
        *Sample overview for demonstration purposes.*
        """
    
    def handle_task(self, task):
        """Handle tasks"""
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            logger.info(f"Processing task: {text}")
            
            # Simple routing
            text_lower = text.lower()
            if "analyze" in text_lower and "stock" in text_lower:
                # Extract ticker if possible
                import re
                ticker_match = re.search(r'\b([A-Z]{1,5})\b', text.upper())
                ticker = ticker_match.group(1) if ticker_match else "AAPL"
                result = self.analyze_stock(ticker)
            elif "market" in text_lower and "overview" in text_lower:
                result = self.market_overview()
            else:
                result = "I can analyze stocks or provide market overviews. Try 'Analyze stock IBM' or 'Market overview'."
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task


if __name__ == "__main__":
    agent = MarketAnalystAgent()
    print("Starting Market Analyst Agent...")
    run_server(agent, host="0.0.0.0", port=8001)


# Contains AI-generated edits.
