"""
Fresh Financial Agent on different port 
"""
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import structlog

logger = structlog.get_logger(__name__)


@agent(
    name="Financial Agent",
    description="Financial analysis and research",
    version="1.0.0",
    url="http://localhost:8010"
)
class FinancialAgent(A2AServer):
    """Financial Agent"""
    
    @skill(
        name="Stock Analysis",
        description="Analyze stock performance",
        tags=["finance"],
        examples=["Analyze AAPL", "Stock analysis"]
    )
    def stock_analysis(self) -> str:
        """Stock analysis"""
        return "Financial analysis complete"
    
    def handle_task(self, task):
        """Handle tasks"""
        try:
            result = self.stock_analysis()
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task


if __name__ == "__main__":
    agent = FinancialAgent()
    print("Starting financial agent...")
    run_server(agent, host="0.0.0.0", port=8010)


