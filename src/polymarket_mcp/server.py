from typing import Any
import asyncio
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
        types.Tool(
            name="list-markets",
            description="List available prediction markets with filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by market status",
                        "enum": ["open", "closed", "resolved"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of markets to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of markets to skip (for pagination)",
                        "default": 0,
                        "minimum": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="get-market-prices",
            description="Get current prices and trading information",
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
        types.Tool(
            name="get-market-history",
            description="Get historical price and volume data",
            inputSchema={
                "type": "object",
                "properties": {
                    "market_id": {
                        "type": "string",
                        "description": "Market ID or slug",
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Time period for historical data",
                        "enum": ["1d", "7d", "30d", "all"],
                        "default": "7d",
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

def format_markets_list(markets_data: dict) -> str:
    """Format a list of markets into a concise string."""
    try:
        if not markets_data or "data" not in markets_data:
            return "No markets available"

        markets = markets_data["data"]
        formatted_markets = ["Available Markets:\n"]

        for market in markets:
            market_info = (
                f"ID: {market.get('id', 'N/A')}\n"
                f"Title: {market.get('title', 'N/A')}\n"
                f"Status: {market.get('status', 'N/A')}\n"
                f"Volume: ${market.get('volume', 0):,.2f}\n"
                "---\n"
            )
            formatted_markets.append(market_info)

        return "\n".join(formatted_markets)
    except Exception as e:
        return f"Error formatting markets list: {str(e)}"

def format_market_prices(prices_data: dict, market_title: str) -> str:
    """Format current market prices into a concise string."""
    try:
        if not prices_data or "data" not in prices_data:
            return "No price information available"

        prices = prices_data["data"]
        formatted_prices = [f"Current Market Prices for {market_title}\n"]

        for outcome in prices.get("outcomes", []):
            price_info = (
                f"Outcome: {outcome.get('name', 'N/A')}\n"
                f"Price: ${outcome.get('price', 0):,.4f}\n"
                f"Probability: {outcome.get('probability', 0) * 100:.1f}%\n"
                "---\n"
            )
            formatted_prices.append(price_info)

        return "\n".join(formatted_prices)
    except Exception as e:
        return f"Error formatting price data: {str(e)}"

def format_market_history(history_data: dict, timeframe: str) -> str:
    """Format historical market data into a concise string."""
    try:
        if not history_data or "data" not in history_data:
            return "No historical data available"

        history = history_data["data"]
        formatted_history = [
            f"Historical Data for {history.get('market_title', 'Unknown Market')}\n"
            f"Time Period: {timeframe}\n"
        ]

        for point in history.get("price_history", []):
            history_point = (
                f"Time: {point.get('timestamp', 'N/A')}\n"
                f"Price: ${point.get('price', 0):,.4f}\n"
                f"Volume: ${point.get('volume', 0):,.2f}\n"
                "---\n"
            )
            formatted_history.append(history_point)

        return "\n".join(formatted_history)
    except Exception as e:
        return f"Error formatting historical data: {str(e)}"

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

        elif name == "list-markets":
            status = arguments.get("status")
            limit = arguments.get("limit", 10)
            offset = arguments.get("offset", 0)
            
            params = {
                "limit": limit,
                "offset": offset
            }
            if status:
                params["status"] = status
            
            markets_data = await make_polymarket_request(
                client,
                "markets",
                params=params
            )

            if isinstance(markets_data, str):
                return [types.TextContent(type="text", text=f"Error: {markets_data}")]

            formatted_markets = format_markets_list(markets_data)
            return [types.TextContent(type="text", text=formatted_markets)]

        elif name == "get-market-prices":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            prices_data = await make_polymarket_request(
                client,
                f"markets/{market_id}/prices"
            )

            if isinstance(prices_data, str):
                return [types.TextContent(type="text", text=f"Error: {prices_data}")]

            # Get market title for better context
            market_data = await make_polymarket_request(
                client,
                f"markets/{market_id}"
            )
            market_title = market_data["data"]["title"] if isinstance(market_data, dict) else "Unknown Market"

            formatted_prices = format_market_prices(prices_data, market_title)
            return [types.TextContent(type="text", text=formatted_prices)]

        elif name == "get-market-history":
            market_id = arguments.get("market_id")
            timeframe = arguments.get("timeframe", "7d")
            
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            history_data = await make_polymarket_request(
                client,
                f"markets/{market_id}/history",
                params={"timeframe": timeframe}
            )

            if isinstance(history_data, str):
                return [types.TextContent(type="text", text=f"Error: {history_data}")]

            formatted_history = format_market_history(history_data, timeframe)
            return [types.TextContent(type="text", text=formatted_history)]
            
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