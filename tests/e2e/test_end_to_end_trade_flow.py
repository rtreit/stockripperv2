import pytest
import asyncio
from config import get_settings

sample_insight = {
    "symbol": "AAPL", 
    "price": 150.0,
    "confidence": 0.85,
    "analysis": "Strong buy signal based on technical indicators"
}


@pytest.mark.asyncio
async def test_end_to_end_trade_flow_a2a(a2a_client, mock_settings):
    """End-to-end test for A2A agent communication flow."""
    settings = mock_settings
    
    # Step 1: Send market insight to Market Analyst 
    # In real scenario, this would trigger the workflow
    insight_response = await a2a_client.post(
        settings.market_analyst_url,
        "/a2a/tasks",
        {
            "task_type": "analyze_market",
            "data": sample_insight
        }
    )
    
    assert insight_response["status"] == "received"
    correlation_id = insight_response["correlation_id"]
    
    # Step 2: Market Analyst should send task to Planner
    # Mock the planner receiving a trade planning task
    plan_response = await a2a_client.post(
        settings.planner_url,
        "/a2a/tasks",
        {
            "task_type": "create_trade_plan",
            "data": sample_insight,
            "correlation_id": correlation_id
        }
    )
    
    assert plan_response["status"] == "READY"
    assert "plan" in plan_response
    
    # Step 3: Planner should notify Mailer to send email
    email_response = await a2a_client.post(
        settings.mailer_url,
        "/a2a/tasks",
        {
            "task_type": "send_notification",
            "data": {
                "trade_plan": plan_response["plan"],
                "symbol": sample_insight["symbol"],
                "recipient": settings.default_email_recipient
            },
            "correlation_id": correlation_id
        }
    )
    
    assert email_response["sent"] is True
    assert "message_id" in email_response


@pytest.mark.asyncio
async def test_agent_discovery(a2a_client, mock_settings):
    """Test A2A agent discovery endpoints."""
    settings = mock_settings
    
    # Test discovery for each agent
    agents = [
        (settings.market_analyst_url, "Market Analyst"),
        (settings.planner_url, "Planner"),
        (settings.mailer_url, "Mailer")
    ]
    
    for agent_url, expected_name in agents:
        discovery = await a2a_client.get(agent_url, "/.well-known/agent.json")
        
        assert "name" in discovery
        assert "version" in discovery
        assert "capabilities" in discovery
        assert "endpoints" in discovery


@pytest.mark.asyncio 
async def test_agent_health_checks(a2a_client, mock_settings):
    """Test agent health check endpoints."""
    settings = mock_settings
    
    agents = [
        settings.market_analyst_url,
        settings.planner_url, 
        settings.mailer_url
    ]
    
    for agent_url in agents:
        health = await a2a_client.get(agent_url, "/health")
        assert health["status"] == "success"


# Contains AI-generated edits.
