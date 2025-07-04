#!/usr/bin/env python3
import asyncio
import httpx
from config import get_settings
from datetime import datetime

async def test_mailer():
    settings = get_settings()
    print(f'Testing {settings.mailer_url}')
    
    trade_plan = {
        "symbol": "AAPL",
        "action": "BUY", 
        "price": "$175.50",
        "analysis": "Strong bullish breakout with high volume confirmation",
        "timestamp": datetime.now().isoformat(),
        "recommendation": "STRONG BUY",
        "target_price": "$195.00",
        "stop_loss": "$162.00"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'{settings.mailer_url}/trade-notification',
            json={"trade_plan": trade_plan}
        )
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Response: {result}')
            return True
        else:
            print(f'Error: {response.text}')
    return False

if __name__ == "__main__":
    result = asyncio.run(test_mailer())
    print(f'Result: {result}')
