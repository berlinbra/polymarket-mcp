from typing import Any
import asyncio
import httpx
import json
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.constants import POLYGON

# Load environment variables
load_dotenv()

server = Server("polymarket_predictions")

# Initialize CLOB client
def get_clob_client() -> ClobClient:
    host = os.getenv("CLOB_HOST", "https://clob.polymarket.com")
    key = os.getenv("KEY")  # Private key exported from polymarket UI
    funder = os.getenv("FUNDER")  # Funder address from polymarket UI
    chain_id = POLYGON
    
    client = ClobClient(
        host,
        key=key,
        chain_id=POLYGON,
        funder=funder,
        signature_type=1,
    )
    client.set_api_creds(client.create_or_derive_api_creds())
    return client

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
            description="Get a list of prediction markets with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by market status (e.g., open, closed, resolved)",
                        "enum": ["active", "resolved"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of markets to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of markets to skip (for pagination)",
                        "default": 0,
                        "minimum": 0
                    }
                },
            },
        ),
        types.Tool(
            name="get-market-prices",
            description="Get current prices and trading information for a market",
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
            description="Get historical price and volume data for a market",
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
                        "default": "7d"
                    }
                },
                "required": ["market_id"],
            },
        )
    ]

def format_market_info(market_data: dict) -> str:
    """Format market information into a concise string."""
    try:
        if not market_data or not isinstance(market_data, dict):
            return "No market information available"
            
        condition_id = market_data.get('condition_id', 'N/A')
        title = market_data.get('title', 'N/A')
        status = market_data.get('status', 'N/A')
        resolution_date = market_data.get('resolution_date', 'N/A')
            
        return (
            f"Condition ID: {condition_id}\n"
            f"Title: {title}\n"
            f"Status: {status}\n"
            f"Resolution Date: {resolution_date}\n"
            "---"
        )
    except Exception as e:
        return f"Error formatting market data: {str(e)}"

def format_market_list(markets_data: list) -> str:
    """Format list of markets into a concise string."""
    try:
        if not markets_data:
            return "No markets available"
            
        formatted_markets = ["Available Markets:\n"]
        
        for market in markets_data:
            try:
                volume = float(market.get('volume', 0))
                volume_str = f"${volume:,.2f}"
            except (ValueError, TypeError):
                volume_str = f"${market.get('volume', 0)}"
                
            formatted_markets.append(
                f"Condition ID: {market.get('condition_id', 'N/A')}\n"
                f"Description: {market.get('description', 'N/A')}\n"
                f"Category: {market.get('category', 'N/A')}\n"
                f"Tokens: {market.get('question', 'N/A')}\n"
                f"Question: {market.get('active', 'N/A')}\n"
                f"Rewards: {market.get('rewards', 'N/A')}\n"
                f"Active: {market.get('active', 'N/A')}\n"
                f"Closed: {market.get('closed', 'N/A')}\n"
                f"Slug: {market.get('market_slug', 'N/A')}\n"
                f"Min Incentive size: {market.get('min_incentive_size', 'N/A')}\n"
                f"Max Incentive size: {market.get('max_incentive_spread', 'N/A')}\n"
                f"End date: {market.get('end_date_iso', 'N/A')}\n"
                f"Start time: {market.get('game_start_time', 'N/A')}\n"
                f"Min order size: {market.get('minimum_order_size', 'N/A')}\n"
                f"Max tick size: {market.get('minimum_tick_size', 'N/A')}\n"
                f"Volume: {volume_str}\n"
                "---\n"
            )
        
        return "\n".join(formatted_markets)
    except Exception as e:
        return f"Error formatting markets list: {str(e)}"

def format_market_prices(market_data: dict) -> str:
    """Format market prices into a concise string."""
    try:
        if not market_data or not isinstance(market_data, dict):
            return market_data
            
        formatted_prices = [
            f"Current Market Prices for {market_data.get('title', 'Unknown Market')}\n"
        ]
        
        # Extract price information from market data
        # Note: Adjust this based on actual CLOB client response structure
        current_price = market_data.get('current_price', 'N/A')
        formatted_prices.append(
            f"Current Price: {current_price}\n"
            "---\n"
        )
        
        return "\n".join(formatted_prices)
    except Exception as e:
        return f"Error formatting price data: {str(e)}"

def format_market_history(history_data: dict) -> str:
    """Format market history data into a concise string."""
    try:
        if not history_data or not isinstance(history_data, dict):
            return "No historical data available"
            
        formatted_history = [
            f"Historical Data for {history_data.get('title', 'Unknown Market')}\n"
        ]
        
        # Format historical data points
        # Note: Adjust this based on actual CLOB client response structure
        for point in history_data.get('history', [])[-5:]:
            formatted_history.append(
                f"Time: {point.get('timestamp', 'N/A')}\n"
                f"Price: {point.get('price', 'N/A')}\n"
                "---\n"
            )
        
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
    
    client = get_clob_client()
    
    try:
        if name == "get-market-info":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            market_data = client.get_market(market_id)
            formatted_info = format_market_info(market_data)
            return [types.TextContent(type="text", text=formatted_info)]

        elif name == "list-markets":
            status = arguments.get("status")
            
            # Get markets using CLOB client
            markets_data = client.get_markets()

            # Handle string response (if the response is a JSON string)
            if isinstance(markets_data, str):
                try:
                    markets_data = json.loads(markets_data)
                except json.JSONDecodeError:
                    return [types.TextContent(type="text", text="Error: Invalid response format from API")]
            
            # Ensure we have a list of markets
            if not isinstance(markets_data, list):
                if isinstance(markets_data, dict) and 'data' in markets_data:
                    markets_data = markets_data['data']
                else:
                    return [types.TextContent(type="text", text="Error: Unexpected response format from API")]
            
            # Filter by status if specified
            if status:
                markets_data = [
                    market for market in markets_data 
                    if isinstance(market, dict) and market.get('status', '').lower() == status.lower()
                ]
            
            # Apply pagination
            offset = arguments.get("offset", 0)
            limit = arguments.get("limit", 10)
            markets_data = markets_data[offset:offset + limit]
            
            formatted_list = format_market_list(markets_data)
            return [types.TextContent(type="text", text=formatted_list)]

        elif name == "get-market-prices":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            market_data = client.get_market(market_id)
            formatted_prices = format_market_prices(market_data)
            return [types.TextContent(type="text", text=formatted_prices)]

        elif name == "get-market-history":
            market_id = arguments.get("market_id")
            timeframe = arguments.get("timeframe", "7d")
            
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            # Note: Adjust this based on actual CLOB client capabilities
            market_data = client.get_market(market_id)
            formatted_history = format_market_history(market_data)
            return [types.TextContent(type="text", text=formatted_history)]
            
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing tool: {str(e)}")]

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