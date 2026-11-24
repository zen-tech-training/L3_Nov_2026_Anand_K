from fastmcp import Client
import asyncio
from langchain.mcp import MCPAdapter

client = Client("http://localhost:8000/mcp")

async def get_all_mcp_tools():
    mcp_adapter = MCPAdapter(client)
    async with mcp_adapter:
        tools = await mcp_adapter.list_tools()
        return tools
    
async def print_tools_resources_prompts():
    async with client:
        prompts = await client.list_prompts()
        tools = await client.list_tools()
        resources = await client.list_resources()
        print(f'Prompts ', prompts)
        print(f'Resources ', resources)

if __name__ == "__main__":
    #asyncio.run(call_add_expense(5000, "Food", "Poha Tea", "2026-11-21"))
    #asyncio.run(call_search_expenses("Food"))
    #asyncio.run(call_get_monthly_summary("2026-11"))
    asyncio.run(print_tools_resources_prompts())