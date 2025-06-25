from tavily import TavilyClient
from mcp.server.fastmcp import FastMCP
import os
import dotenv

dotenv.load_dotenv()

mcp = FastMCP(
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8006,  # Port number for the server
    )

@mcp.tool()
async def get_result(query: str):
    """
    当你遇到不知道一些不知道的问题时（比如一些实时问题），使用搜索工具并返回结果
    """
    tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = tavily_client.search(query=query)
    print(response)
    return response

if __name__ == "__main__":
    mcp.run(transport="streamable-http")