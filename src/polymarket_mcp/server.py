from typing import Any
import asyncio
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLYMARKET_BASE = "https://strapi-matic.poly.market/api"
API_KEY = os.getenv('POLYMARKET_API_KEY')

server = Server("polymarket_predictions")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools for interacting with the PolyMarket API.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get-market-info",
            description="Get detailed information about a specific prediction market",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "string",
                        "description": "Market ID or slug",
                    },
                },
                "required": ["market_id"],
            },
        ),
    ]

async def make_polymarket_request(
    client: httpx.AsyncClient,
    endpoint: str,
    params: dict = None,
    method: str = "GET"
) -> dict[str, Any] | str:
    """Make a request to the PolyMarket API with proper error handling."""
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    try:
        if method == "GET":
            response = await client.get(
                f"{POLYMARKET_BASE}/{endpoint}",
                params=params,
                headers=headers,
                timeout=30.0
            )
        else:
            response = await client.post(
                f"{POLYMARKET_BASE}/{endpoint}",
                json=params,
                headers=headers,
                timeout=30.0
            )
        
        # Check for specific error responses
        if response.status_code == 429:
            return "Rate limit exceeded. Please try again later."
        elif response.status_code == 403:
            return "API key invalid or expired."
        elif response.status_code == 404:
            return "Market or resource not found."
        
        response.raise_for_status()
        return response.json()
        
    except httpx.TimeoutException:
        return "Request timed out after 30 seconds. The PolyMarket API may be experiencing delays."
    except httpx.ConnectError:
        return "Failed to connect to PolyMarket API. Please check your internet connection."
    except httpx.HTTPStatusError as e:
        return f"HTTP error occurred: {str(e)} - Response: {e.response.text}"
    except Exception as e:
        return f"Unexpected error occurred: {str(e)}"

def format_market_info(market_data: dict) -> str:
    """Format market information into a concise string."""
    try:
        if not market_data or "data" not in market_data:
            return "No market information available"
            
        market = market_data["data"]
        return (
            f"Title: {market.get('title', 'N/A')}\n"
            f"Category: {market.get('category', 'N/A')}\n"
            f"Status: {market.get('status', 'N/A')}\n"
            f"Resolution Date: {market.get('resolutionDate', 'N/A')}\n"
            f"Volume: ${market.get('volume', 0):,.2f}\n"
            f"Liquidity: ${market.get('liquidity', 0):,.2f}\n"
            f"Description: {market.get('description', 'N/A')}\n"
            "---"
        )
    except Exception as e:
        return f"Error formatting market data: {str(e)}"

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can fetch prediction market data and notify clients of changes.
    """
    if not arguments:
        return [types.TextContent(type="text", text="Missing arguments for the request")]
    
    async with httpx.AsyncClient() as client:
        if name == "get-market-info":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            market_data = await make_polymarket_request(
                client,
                f"markets/{market_id}"
            )

            if isinstance(market_data, str):
                return [types.TextContent(type="text", text=f"Error: {market_data}")]

            formatted_info = format_market_info(market_data)
            return [types.TextContent(type="text", text=formatted_info)]
            
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Main entry point for the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="polymarket_predictions",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())