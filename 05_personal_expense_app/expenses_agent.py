
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from expense_mcp_client import get_all_mcp_tools
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

class PersonalExpensesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

model_with_tools = []
personal_expenses_graph = None

def personal_expenses_node(state: PersonalExpensesState) -> dict:
    """Manages different operations related to the personal expenses"""
    response = model_with_tools.invoke(state['messages'])
    return {"messages": [response]}

def route_after_personal_expenses_node(state: PersonalExpensesState) -> str:
    """One graph node: route to the next node based on the model response"""
    last_message = state['messages'][-1]
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    else:
        return "end"

async def initialize_graph():
    all_mcp_tools = await get_all_mcp_tools()
    print(f'All MCP Tools {all_mcp_tools}')

    model = ChatOllama(model="llama3.2")
    print('Model is ready to use!')

    global model_with_tools
    model_with_tools = model.bind_tools(all_mcp_tools)

    personal_expenses_graph_builder = StateGraph(PersonalExpensesState)

    # Node registration
    personal_expenses_graph_builder.add_node("personal_expenses_node", personal_expenses_node)
    personal_expenses_graph_builder.add_node("tools", ToolNode(all_mcp_tools))

    # Add edges
    personal_expenses_graph_builder.add_edge(START, "personal_expenses_node")
    personal_expenses_graph_builder.add_conditional_edges(
    "personal_expenses_node",
    route_after_personal_expenses_node,
    {
        "tools": "tools",
        "end": END
    }
    )
    personal_expenses_graph_builder.add_edge("tools", "personal_expenses_node")
    
    global personal_expenses_graph
    personal_expenses_graph = personal_expenses_graph_builder.compile()
    print('Graph is ready...')

async def invoke(message):
    result = await personal_expenses_graph.ainvoke({
        "messages": [
            {"role": "user", "content": message}
        ]
    })
    print('FINAL ANSWER\n')
    print(result['messages'][-1].content)
    return result['messages'][-1].content