import os
import sys
import asyncio
import pytest
import pytest_asyncio
import httpx
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import get_settings


class A2ATestClient:
    """Test client for A2A HTTP endpoints."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient()
        self.responses = {}  # Store mock responses

    async def post(self, agent_url: str, path: str, json: dict) -> Dict[str, Any]:
        """Post to an A2A agent endpoint."""
        url = f"{agent_url}{path}"
        
        # Mock the HTTP calls for testing based on task type
        task_type = json.get("task_type", "")
        
        if task_type == "analyze_market":
            return {"status": "received", "correlation_id": "test-123"}
        elif task_type == "create_trade_plan":
            return {"status": "READY", "plan": "Buy AAPL", "correlation_id": "test-123"}
        elif task_type == "send_notification":
            return {"sent": True, "message_id": "email-123", "correlation_id": "test-123"}
        
        return {"status": "success"}

    async def get(self, agent_url: str, path: str) -> Dict[str, Any]:
        """Get from an A2A agent endpoint."""
        url = f"{agent_url}{path}"
        
        # Mock discovery endpoint
        if path == "/.well-known/agent.json":
            return {
                "name": "Test Agent",
                "version": "1.0.0",
                "capabilities": {"test": True},
                "endpoints": ["/a2a/tasks", "/health"]
            }
        
        return {"status": "success"}

    async def wait_for_task_completion(self, agent_url: str, task_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for a task to complete by polling."""
        # Mock task completion for testing
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {"success": True}
        }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


@pytest_asyncio.fixture
async def a2a_client():
    """Provide an A2A test client."""
    client = A2ATestClient()
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    return get_settings()


