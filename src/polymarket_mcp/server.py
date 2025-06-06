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

# Gamma API endpoint
GAMMA_API_URL = "https://gamma-api.polymarket.com"
TIMEOUT_SECONDS = 30

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

async def fetch_gamma_markets(params: dict):
    """Fetch markets from the Gamma API"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT_SECONDS)) as client:
        try:
            response = await client.get(f"{GAMMA_API_URL}/markets", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[DEBUG] Gamma API returned {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"[DEBUG] Error fetching from Gamma API: {str(e)}")
            return None

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
                        "description": "Market ID (numeric ID or slug, e.g. '12' or 'will-bitcoin-reach-100k')",
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
                    "active": {
                        "type": "boolean",
                        "description": "Filter by active markets",
                        "default": True
                    },
                    "closed": {
                        "type": "boolean",
                        "description": "Filter by closed markets",
                        "default": False
                    },
                    "archived": {
                        "type": "boolean",
                        "description": "Filter by archived markets (set to false to exclude old markets)",
                        "default": False
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
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order",
                        "enum": ["asc", "desc"],
                        "default": "desc"
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
                        "description": "Market ID (numeric ID or slug)",
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
                        "description": "Market ID (numeric ID or slug)",
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
        title = market_data.get('title', market_data.get('question', 'N/A'))
        status = 'Active' if market_data.get('active') else 'Closed' if market_data.get('closed') else 'Unknown'
        end_date = market_data.get('end_date_iso', 'N/A')
        volume = market_data.get('volume', 0)
        
        try:
            volume_str = f"${float(volume):,.2f}"
        except (ValueError, TypeError):
            volume_str = f"${volume}"
            
        return (
            f"Condition ID: {condition_id}\n"
            f"Title: {title}\n"
            f"Status: {status}\n"
            f"End Date: {end_date}\n"
            f"Volume: {volume_str}\n"
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
                
            title = market.get('title', market.get('question', 'N/A'))
            status = 'Active' if market.get('active') else 'Closed' if market.get('closed') else 'Unknown'
                
            formatted_markets.append(
                f"Condition ID: {market.get('condition_id', 'N/A')}\n"
                f"Title: {title}\n"
                f"Status: {status}\n"
                f"Category: {market.get('category', 'N/A')}\n"
                f"Volume: {volume_str}\n"
                f"End Date: {market.get('end_date_iso', 'N/A')}\n"
                f"Slug: {market.get('market_slug', 'N/A')}\n"
                "---\n"
            )
        
        return "\n".join(formatted_markets)
    except Exception as e:
        return f"Error formatting markets list: {str(e)}"

def format_market_prices(market_data: dict) -> str:
    """Format market prices into a concise string."""
    try:
        if not market_data or not isinstance(market_data, dict):
            return "No price data available"
            
        title = market_data.get('title', market_data.get('question', 'Unknown Market'))
        formatted_prices = [
            f"Current Market Prices for {title}\n"
        ]
        
        # If tokens are available, show their current prices
        tokens = market_data.get('tokens', [])
        if tokens:
            for token in tokens:
                outcome = token.get('outcome', 'Unknown')
                price = token.get('price', 0)
                try:
                    price_float = float(price)
                    formatted_prices.append(
                        f"Outcome: {outcome}\n"
                        f"Price: ${price_float:.4f}\n"
                        f"Probability: {price_float * 100:.1f}%\n"
                        "---\n"
                    )
                except (ValueError, TypeError):
                    formatted_prices.append(
                        f"Outcome: {outcome}\n"
                        f"Price: {price}\n"
                        "---\n"
                    )
        else:
            # Fallback for markets without token data
            formatted_prices.append("No price data available for this market\n")
        
        return "\n".join(formatted_prices)
    except Exception as e:
        return f"Error formatting price data: {str(e)}"

def format_market_history(history_data: dict) -> str:
    """Format market history data into a concise string."""
    try:
        if not history_data or not isinstance(history_data, dict):
            return "No historical data available"
            
        title = history_data.get('title', history_data.get('question', 'Unknown Market'))
        formatted_history = [
            f"Historical Data for {title}\n"
        ]
        
        # Note: This is a placeholder as the Gamma API might not provide historical data
        # You may need to use a different endpoint or the CLOB client for this
        formatted_history.append("Historical data retrieval not yet implemented for Gamma API\n")
        
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
        arguments = {}
    
    client = get_clob_client()
    
    try:
        if name == "get-market-info":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            # Try to get from Gamma API first
            params = {"id": market_id} if market_id.isdigit() else {"slug": market_id}
            market_data = await fetch_gamma_markets(params)
            
            if market_data and isinstance(market_data, list) and len(market_data) > 0:
                formatted_info = format_market_info(market_data[0])
            else:
                # Fallback to CLOB client
                market_data = client.get_market(market_id)
                formatted_info = format_market_info(market_data)
                
            return [types.TextContent(type="text", text=formatted_info)]

        elif name == "list-markets":
            # Build parameters for Gamma API
            params = {}
            
            # Handle active/closed/archived filters
            if arguments.get("active") is not None:
                params["active"] = str(arguments.get("active")).lower()
            else:
                # Default to active markets if not specified
                params["active"] = "true"
                
            if arguments.get("closed") is not None:
                params["closed"] = str(arguments.get("closed")).lower()
                
            if arguments.get("archived") is not None:
                params["archived"] = str(arguments.get("archived")).lower()
            else:
                # Default to excluding archived markets
                params["archived"] = "false"
            
            # Add pagination and ordering
            params["limit"] = arguments.get("limit", 10)
            params["offset"] = arguments.get("offset", 0)
            params["order"] = arguments.get("order", "desc")
            
            # Debug logging
            print(f"[DEBUG] Final API params: {params}")
            
            # Fetch from Gamma API
            markets_data = await fetch_gamma_markets(params)
            
            if markets_data is None:
                # Fallback: try with minimal parameters
                print("[DEBUG] Trying fallback with minimal parameters")
                fallback_params = {
                    "active": "true",
                    "archived": "false",
                    "limit": params["limit"]
                }
                markets_data = await fetch_gamma_markets(fallback_params)
            
            if markets_data is None:
                # Final fallback to CLOB client
                print("[DEBUG] Falling back to CLOB client")
                markets_data = client.get_markets()
                
                # Handle string response
                if isinstance(markets_data, str):
                    try:
                        markets_data = json.loads(markets_data)
                    except json.JSONDecodeError:
                        return [types.TextContent(type="text", text="Error: Invalid response format from API")]
                
                # Ensure we have a list
                if not isinstance(markets_data, list):
                    if isinstance(markets_data, dict) and 'data' in markets_data:
                        markets_data = markets_data['data']
                    else:
                        return [types.TextContent(type="text", text="Error: Unexpected response format from API")]
                
                # Apply manual filtering for CLOB response
                if arguments.get("active", True):
                    markets_data = [m for m in markets_data if m.get('active', False)]
                
                # Apply pagination
                offset = arguments.get("offset", 0)
                limit = arguments.get("limit", 10)
                markets_data = markets_data[offset:offset + limit]
            
            formatted_list = format_market_list(markets_data if isinstance(markets_data, list) else [])
            return [types.TextContent(type="text", text=formatted_list)]

        elif name == "get-market-prices":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            # Try to get from Gamma API first
            params = {"id": market_id} if market_id.isdigit() else {"slug": market_id}
            market_data = await fetch_gamma_markets(params)
            
            if market_data and isinstance(market_data, list) and len(market_data) > 0:
                formatted_prices = format_market_prices(market_data[0])
            else:
                # Fallback to CLOB client
                market_data = client.get_market(market_id)
                formatted_prices = format_market_prices(market_data)
                
            return [types.TextContent(type="text", text=formatted_prices)]

        elif name == "get-market-history":
            market_id = arguments.get("market_id")
            timeframe = arguments.get("timeframe", "7d")
            
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            # Note: Historical data might require a different endpoint
            # For now, we'll use the market data as a placeholder
            params = {"id": market_id} if market_id.isdigit() else {"slug": market_id}
            market_data = await fetch_gamma_markets(params)
            
            if market_data and isinstance(market_data, list) and len(market_data) > 0:
                formatted_history = format_market_history(market_data[0])
            else:
                # Fallback to CLOB client
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
