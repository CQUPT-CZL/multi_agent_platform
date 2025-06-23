# math_server.py

# weather_server.py
from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather",
    instructions="You are a weather assistant that can answer questions about the weather in a given location.",  # Instructions for the LLM on how to use this tool
    host="0.0.0.0",  # Host address (0.0.0.0 allows connections from any IP)
    port=8005,  # Port number for the server
    )

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in {}.".format(location)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")