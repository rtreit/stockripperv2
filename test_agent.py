"""
Test agent to verify skill registration works
"""
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
import structlog

logger = structlog.get_logger(__name__)


@agent(
    name="Test Agent",
    description="Simple test agent",
    version="1.0.0",
    url="http://localhost:8002"
)
class TestAgent(A2AServer):
    """Test Agent"""
    
    @skill(
        name="Hello World",
        description="Say hello",
        tags=["greeting"],
        examples=["Hello", "Hi there"]
    )
    def hello_world(self) -> str:
        """Say hello"""
        return "Hello, World!"
    
    def handle_task(self, task):
        """Handle tasks"""
        try:
            result = self.hello_world()
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task


if __name__ == "__main__":
    agent = TestAgent()
    print("Starting test agent...")
    run_server(agent, host="0.0.0.0", port=8002)


