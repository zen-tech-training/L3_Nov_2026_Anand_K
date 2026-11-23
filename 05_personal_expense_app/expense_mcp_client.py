from fastmcp import Client
import asyncio

client = Client("http://localhost:8000/mcp")

async def call_add_expense(amount: float, category: str, description: str, expense_date: str = ""):
    async with client:
        response = await client.call_tool("add_expense", 
            { "amount": amount, "category": category, "description": description, "expense_date": expense_date })
        print(response)

async def call_search_expenses(category: str = "", start_date: str = "", end_date: str = ""):
    async with client:
        response = await client.call_tool("search_expenses", 
            { "category": category, "start_date": start_date, "end_date": end_date })
        print(response)
    
async def call_get_monthly_summary(month: str):
    async with client:
        response = await client.call_tool("get_monthly_summary", 
            { "month": month })
        print(response)


if __name__ == "__main__":
    #asyncio.run(call_add_expense(5000, "Food", "Poha Tea", "2026-11-21"))
    #asyncio.run(call_search_expenses("Food"))
    #asyncio.run(call_get_monthly_summary("2026-11"))