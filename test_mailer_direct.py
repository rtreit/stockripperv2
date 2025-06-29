#!/usr/bin/env python3
"""Direct test of the Mailer service."""

import asyncio
import httpx
import json

async def test_mailer():
    """Test the Mailer service directly."""
    payload = {
        "ticker": "AAPL",
        "analysis": "Test analysis from direct test",
        "plan": "Test trading plan from direct test",
        "notification_type": "test"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                "http://localhost:8003/send_notification",
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_mailer())
    print(f"Test {'PASSED' if success else 'FAILED'}")
