import pytest

sample_insight = {"symbol": "AAPL", "price": 150.0}


def test_end_to_end_trade_flow(client):
    """Canonical failing integration test for the MVP."""
    # GIVEN all three agents running in the cluster
    insight = client.post("/a2a/publish", json=sample_insight)
    # WHEN MarketAnalyst publishes an insight on `market-insight`
    plan = client.wait_for("trade-plan", timeout=30)
    email = client.wait_for("email-notify", timeout=30)
    # THEN Planner emits a `trade-plan` and Mailer sends an email via Gmail MCP
    assert plan["status"] == "READY"
    assert email["sent"] is True
