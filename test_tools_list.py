import asyncio
import json
import subprocess
import os

async def test_tools():
    # Start Alpaca MCP server
    env = os.environ.copy()
    env.update({
        'ALPACA_API_KEY': os.getenv('ALPACA_API_KEY', ''),
        'ALPACA_SECRET_KEY': os.getenv('ALPACA_SECRET_KEY', ''),
        'ALPACA_BASE_URL': 'https://paper-api.alpaca.markets',
        'PAPER': 'True'
    })
    
    process = await asyncio.create_subprocess_exec(
        '.venv\\Scripts\\python.exe', './mcp_servers/alpaca/alpaca_mcp_server.py',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    await asyncio.sleep(2)
    
    # Initialize
    init_msg = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'test', 'version': '1.0.0'}
        }
    }
    
    process.stdin.write((json.dumps(init_msg) + '\n').encode())
    await process.stdin.drain()
    
    init_response = await process.stdout.readline()
    print('Init response:', init_response.decode().strip())
    
    # Get tools list
    tools_msg = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'tools/list',
        'params': {}
    }
    
    process.stdin.write((json.dumps(tools_msg) + '\n').encode())
    await process.stdin.drain()
    
    tools_response = await process.stdout.readline()
    print('Tools response:', tools_response.decode().strip())
    
    # Parse and show tools
    try:
        tools_data = json.loads(tools_response.decode().strip())
        if 'result' in tools_data and 'tools' in tools_data['result']:
            tools = tools_data['result']['tools']
            print(f'Found {len(tools)} tools:')
            for i, tool in enumerate(tools[:3]):
                name = tool.get('name', 'unknown')
                desc = tool.get('description', 'no desc')
                print(f'  {i+1}. {name} - {desc}')
        else:
            print('No tools found in response')
            print('Response keys:', list(tools_data.keys()))
    except Exception as e:
        print(f'Error parsing tools: {e}')
    
    process.terminate()
    await process.wait()

if __name__ == '__main__':
    asyncio.run(test_tools())
