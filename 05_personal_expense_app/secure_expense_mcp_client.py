
import asyncio
import os

import httpx2
from dotenv import load_dotenv

from mcp import Client
from mcp.client.streamable_http import streamable_http_client


load_dotenv()

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://localhost:8000/mcp",
)

API_KEY = os.getenv("MCP_API_KEY")

if not API_KEY:
    raise RuntimeError("MCP_API_KEY is not configured")


async def main():

    # Configure HTTP authentication
    async with httpx2.AsyncClient(
        headers={
            "Authorization": f"Bearer {API_KEY}"
        },
        timeout=httpx2.Timeout(
            30.0,
            read=300.0,
        ),
    ) as http_client:
        
        print(f'http_client = {http_client}')

        # Create Streamable HTTP transport
        transport = streamable_http_client(
            url=MCP_SERVER_URL,
            http_client=http_client,
        )

        print(f'Transport: {transport}')

        # Connect using MCP 2.x Client API
        async with Client(transport) as client:

            print("Connected to MCP server successfully!")

            # Discover available tools
            tools = await client.list_tools()

            print("\nAvailable MCP tools:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")



if __name__ == "__main__":
    asyncio.run(main())
