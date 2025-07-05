"""
Exact copy of test agent structure with market analyst methods
"""
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import structlog

logger = structlog.get_logger(__name__)


@agent(
    name="Market Analyst",
    description="Stock analysis agent",
    version="1.0.0",
    url="http://localhost:8001"
)
class MarketAnalystAgent(A2AServer):
    """Market Analyst Agent"""
    
    @skill(
        name="Analyze Stock",
        description="Analyze a stock ticker",
        tags=["stock"],
        examples=["Analyze AAPL", "Stock analysis"]
    )
    def analyze_stock(self) -> str:
        """Analyze stock"""
        return "Stock analysis result"
    
    def handle_task(self, task):
        """Handle tasks"""
        try:
            result = self.analyze_stock()
            
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
    print("Starting market analyst agent...")
    run_server(agent, host="0.0.0.0", port=8001)


