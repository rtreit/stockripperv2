"""
Fresh Stock Agent with different name and port
"""
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import structlog

logger = structlog.get_logger(__name__)


@agent(
    name="Stock Agent",
    description="Simple stock agent",
    version="1.0.0",
    url="http://localhost:8005"
)
class StockAgent(A2AServer):
    """Stock Agent"""
    
    @skill(
        name="Stock Analysis",
        description="Analyze stocks",
        tags=["stocks"],
        examples=["Analyze stock", "Stock info"]
    )
    def stock_analysis(self) -> str:
        """Stock analysis"""
        return "Stock analysis complete"
    
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
    agent = StockAgent()
    print("Starting stock agent...")
    run_server(agent, host="0.0.0.0", port=8005)


