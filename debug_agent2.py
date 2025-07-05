"""
Debug skill registration step by step
"""
import os
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState

print("=== DEBUG: Starting imports ===")

# Create a class without decorators first to debug
class DebugAgentRaw(A2AServer):
    """Debug Agent to test skill registration"""
    
    def __init__(self):
        print("=== DEBUG: In __init__ ===")
        super().__init__()
        print("=== DEBUG: After super().__init__() ===")
        
        # Manually check what methods have _skill_info
        print("=== DEBUG: Checking methods for _skill_info ===")
        for attr_name in dir(self):
            if not attr_name.startswith('__'):
                attr = getattr(self, attr_name)
                if callable(attr) and hasattr(attr, '_skill_info'):
                    print(f"=== DEBUG: Found skill method: {attr_name} with info: {attr._skill_info} ===")
                elif callable(attr):
                    print(f"=== DEBUG: Method {attr_name} has no _skill_info ===")
        
        print("=== DEBUG: End of manual skill check ===")
    
    def test_skill(self) -> str:
        """Test skill"""
        print("=== DEBUG: test_skill called ===")
        return "Test successful"
    
    def handle_task(self, task):
        """Handle tasks"""
        return task

# Apply skill decorator manually
print("=== DEBUG: Applying skill decorator ===")
skill_decorator = skill(
    name="Test Skill",
    description="A simple test skill",
    tags=["test"],
    examples=["test me"]
)
DebugAgentRaw.test_skill = skill_decorator(DebugAgentRaw.test_skill)
print(f"=== DEBUG: After applying skill decorator, _skill_info = {getattr(DebugAgentRaw.test_skill, '_skill_info', 'NOT_FOUND')} ===")

# Now apply agent decorator
print("=== DEBUG: Applying agent decorator ===")
agent_decorator = agent(
    name="Debug Agent",
    description="Debug agent to test skill registration",
    version="1.0.0",
    url="http://localhost:8001"
)
DebugAgent = agent_decorator(DebugAgentRaw)

if __name__ == "__main__":
    print("=== DEBUG: Creating agent ===")
    agent_instance = DebugAgent()
    print("=== DEBUG: Agent created ===")
    print(f"=== DEBUG: Final agent_card.skills = {agent_instance.agent_card.skills} ===")
    print("=== DEBUG: Starting server ===")
    run_server(agent_instance, host="0.0.0.0", port=8001)


# Contains AI-generated edits.
