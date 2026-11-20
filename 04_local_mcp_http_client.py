# Local MCP stdio client

from fastmcp import Client
import asyncio

client = Client("http://localhost:9000/mcp")

async def call_greet(name: str):
    async with client:
        response = await client.call_tool("greet", {"name": name})
        print(response)

async def call_add(x: int, y: int):
    async with client:
        response = await client.call_tool("add", {"x": x, "y": y})
        print(response)

if __name__ == "__main__":
    asyncio.run(call_greet('Tom'))
    asyncio.run(call_add(10, 40))