"""
Debug agent to understand skill registration
"""
import os
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState

print("=== DEBUG: Starting imports ===")

@agent(
    name="Debug Agent",
    description="Debug agent to test skill registration",
    version="1.0.0",
    url="http://localhost:8001"
)
class DebugAgent(A2AServer):
    """Debug Agent to test skill registration"""
    
    def __init__(self):
        print("=== DEBUG: In __init__ ===")
        super().__init__()
        print("=== DEBUG: After super().__init__() ===")
        print(f"=== DEBUG: agent_card = {getattr(self, 'agent_card', 'NOT_FOUND')} ===")
        if hasattr(self, 'agent_card'):
            print(f"=== DEBUG: agent_card.skills = {self.agent_card.skills} ===")
        print("=== DEBUG: End of __init__ ===")
    
    @skill(
        name="Test Skill",
        description="A simple test skill",
        tags=["test"],
        examples=["test me"]
    )
    def test_skill(self) -> str:
        """Test skill"""
        print("=== DEBUG: test_skill called ===")
        return "Test successful"
    
    def handle_task(self, task):
        """Handle tasks"""
        print(f"=== DEBUG: handle_task called with task: {task} ===")
        try:
            result = self.test_skill()
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            print(f"=== DEBUG: Error in handle_task: {e} ===")
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task


if __name__ == "__main__":
    print("=== DEBUG: Creating agent ===")
    agent = DebugAgent()
    print("=== DEBUG: Agent created ===")
    print("=== DEBUG: Starting server ===")
    run_server(agent, host="0.0.0.0", port=8001)


