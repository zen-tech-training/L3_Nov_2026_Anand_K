# Local stdio MCP Server

from fastmcp import FastMCP

mcp = FastMCP("My Local http MCP server")

@mcp.tool
def greet(name: str):
    return f"Hello {name}!!"

@mcp.tool
def add(x: int, y: int):
    return x + y

if __name__ == "__main__":
    mcp.run(transport="http", port=9000) # default protocol is stdio
