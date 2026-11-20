# Local MCP stdio client

from fastmcp import Client
import asyncio
import os
from dotenv import find_dotenv, load_dotenv

env_path = find_dotenv()
load_dotenv(env_path)

tavilyApiKey = os.getenv('TAVILY_API_KEY')

client = Client(f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavilyApiKey}")

async def list_tools():
    async with client:
        tavily_mcp_tools = await client.list_tools()
        for tool in tavily_mcp_tools:
            print(tool)


if __name__ == "__main__":
    asyncio.run(list_tools())
