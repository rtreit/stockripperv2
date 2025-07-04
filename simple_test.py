#!/usr/bin/env python3
import asyncio
import httpx
from config import get_settings

async def test():
    settings = get_settings()
    print(f'Testing {settings.planner_url}')
    async with httpx.AsyncClient() as client:
        response = await client.get(f'{settings.planner_url}/.well-known/agent.json')
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'Service: {result.get("name", "unknown")}')
            return True
    return False

if __name__ == "__main__":
    result = asyncio.run(test())
    print(f'Result: {result}')
