from typing import Any
import asyncio
import httpx
import json
import sys
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

# Initialize CLOB client (still needed for trading operations)
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
                    "active": {
                        "type": "boolean",
                        "description": "Filter by active markets",
                        "default": True,
                    },
                    "closed": {
                        "type": "boolean",
                        "description": "Filter by closed markets",
                        "default": False,
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
                    "order_by": {
                        "type": "string",
                        "description": "Sort markets by field",
                        "enum": ["volume", "liquidity", "startDate", "endDate", "createdAt"],
                        "default": "volume"
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
            
        condition_id = market_data.get('conditionId', 'N/A')
        title = market_data.get('title', market_data.get('question', 'N/A'))
        status = "Active" if market_data.get('active', False) else "Closed" if market_data.get('closed', False) else "Unknown"
        end_date = market_data.get('endDate', market_data.get('endDateIso', 'N/A'))
        volume = market_data.get('volume', 0)
        liquidity = market_data.get('liquidity', 0)
        
        # Format outcomes with current prices
        outcomes_str = ""
        outcomes = market_data.get('outcomes', [])
        outcome_prices = market_data.get('outcomePrices', [])
        
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []
                
        if outcomes and outcome_prices and len(outcomes) == len(outcome_prices):
            outcomes_str = "\nOutcomes:\n"
            for i, outcome in enumerate(outcomes):
                price = float(outcome_prices[i]) if i < len(outcome_prices) else 0
                outcomes_str += f"  - {outcome}: ${price:.2f} ({price*100:.1f}%)\n"
        
        return (
            f"Market ID: {condition_id}\n"
            f"Title: {title}\n"
            f"Status: {status}\n"
            f"End Date: {end_date}\n"
            f"Volume: ${volume:,.2f}\n"
            f"Liquidity: ${liquidity:,.2f}"
            f"{outcomes_str}\n"
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
                
            status = "Active" if market.get('active', False) else "Closed" if market.get('closed', False) else "Unknown"
            
            formatted_markets.append(
                f"ID: {market.get('conditionId', 'N/A')}\n"
                f"Title: {market.get('title', market.get('question', 'N/A'))}\n"
                f"Status: {status}\n"
                f"Volume: {volume_str}\n"
                f"End Date: {market.get('endDate', market.get('endDateIso', 'N/A'))}\n"
                "---\n"
            )
        
        return "\n".join(formatted_markets)
    except Exception as e:
        return f"Error formatting markets list: {str(e)}"

def format_market_prices(market_data: dict) -> str:
    """Format market prices into a concise string."""
    try:
        if not market_data or not isinstance(market_data, dict):
            return "No price information available"
            
        title = market_data.get('title', market_data.get('question', 'Unknown Market'))
        formatted_prices = [f"Current Market Prices for: {title}\n"]
        
        # Extract outcomes and prices
        outcomes = market_data.get('outcomes', [])
        outcome_prices = market_data.get('outcomePrices', [])
        
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []
        
        if outcomes and outcome_prices:
            for i, outcome in enumerate(outcomes):
                if i < len(outcome_prices):
                    price = float(outcome_prices[i])
                    formatted_prices.append(
                        f"{outcome}: ${price:.2f} ({price*100:.1f}%)"
                    )
        
        formatted_prices.append("\n---")
        return "\n".join(formatted_prices)
    except Exception as e:
        return f"Error formatting price data: {str(e)}"

def format_market_history(history_data: dict) -> str:
    """Format market history data into a concise string."""
    try:
        if not history_data or not isinstance(history_data, dict):
            return "No historical data available"
            
        title = history_data.get('title', history_data.get('question', 'Unknown Market'))
        formatted_history = [f"Historical Data for: {title}\n"]
        
        # Note: Gamma API doesn't provide detailed historical data
        # This would need to be fetched from a different endpoint or service
        formatted_history.append("Note: Detailed historical data requires additional API access")
        formatted_history.append(f"Current Volume: ${history_data.get('volume', 0):,.2f}")
        formatted_history.append(f"Created: {history_data.get('createdAt', 'N/A')}")
        formatted_history.append("---")
        
        return "\n".join(formatted_history)
    except Exception as e:
        return f"Error formatting historical data: {str(e)}"

async def fetch_gamma_markets(params: dict) -> list:
    """Fetch markets from Gamma API with enhanced debugging"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"{GAMMA_API_URL}/markets"
            print(f"[DEBUG] Fetching from: {url}", file=sys.stderr)
            print(f"[DEBUG] Request params: {json.dumps(params, indent=2)}", file=sys.stderr)
            
            # Add headers that might be required
            headers = {
                "Accept": "application/json",
                "User-Agent": "polymarket-mcp/0.2.0"
            }
            
            response = await client.get(url, params=params, headers=headers)
            print(f"[DEBUG] Response status: {response.status_code}", file=sys.stderr)
            print(f"[DEBUG] Response headers: {dict(response.headers)}", file=sys.stderr)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[DEBUG] Response data type: {type(data)}", file=sys.stderr)
                    
                    # Handle different response formats
                    if isinstance(data, dict):
                        # Check if data is wrapped in an object
                        if 'data' in data:
                            markets = data['data']
                            print(f"[DEBUG] Found 'data' key, extracting markets", file=sys.stderr)
                        elif 'markets' in data:
                            markets = data['markets']
                            print(f"[DEBUG] Found 'markets' key, extracting markets", file=sys.stderr)
                        else:
                            # Try to use the dict directly as a single market
                            markets = [data]
                            print(f"[DEBUG] Using response as single market", file=sys.stderr)
                    elif isinstance(data, list):
                        markets = data
                        print(f"[DEBUG] Response is already a list", file=sys.stderr)
                    else:
                        print(f"[DEBUG] Unexpected data type: {type(data)}", file=sys.stderr)
                        markets = []
                    
                    print(f"[DEBUG] Number of markets: {len(markets)}", file=sys.stderr)
                    if markets and len(markets) > 0:
                        print(f"[DEBUG] First market sample: {json.dumps(markets[0], indent=2)[:500]}...", file=sys.stderr)
                    
                    return markets
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON decode error: {e}", file=sys.stderr)
                    print(f"[DEBUG] Raw response: {response.text[:500]}...", file=sys.stderr)
                    return []
            else:
                print(f"[DEBUG] Error response: {response.text[:500]}...", file=sys.stderr)
                return []
        except httpx.TimeoutException:
            print(f"[DEBUG] Request timed out after 30 seconds", file=sys.stderr)
            return []
        except httpx.NetworkError as e:
            print(f"[DEBUG] Network error: {type(e).__name__}: {str(e)}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[DEBUG] Unexpected error in fetch_gamma_markets: {type(e).__name__}: {str(e)}", file=sys.stderr)
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}", file=sys.stderr)
            return []

async def fetch_gamma_market(market_id: str) -> dict:
    """Fetch single market from Gamma API with enhanced debugging"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            url = f"{GAMMA_API_URL}/markets/{market_id}"
            print(f"[DEBUG] Fetching single market from: {url}", file=sys.stderr)
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "polymarket-mcp/0.2.0"
            }
            
            response = await client.get(url, headers=headers)
            print(f"[DEBUG] Response status: {response.status_code}", file=sys.stderr)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[DEBUG] Market data received: {json.dumps(data, indent=2)[:500]}...", file=sys.stderr)
                return data
            else:
                print(f"[DEBUG] Error fetching market: {response.text[:500]}...", file=sys.stderr)
                return {}
        except Exception as e:
            print(f"[DEBUG] Error fetching market: {type(e).__name__}: {str(e)}", file=sys.stderr)
            return {}

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
    
    try:
        if name == "get-market-info":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            market_data = await fetch_gamma_market(market_id)
            formatted_info = format_market_info(market_data)
            return [types.TextContent(type="text", text=formatted_info)]

        elif name == "list-markets":
            # Try multiple parameter combinations to debug
            print(f"[DEBUG] list-markets called with arguments: {arguments}", file=sys.stderr)
            
            # First try with minimal parameters
            simple_params = {"limit": 5}
            print(f"[DEBUG] Trying simple request first", file=sys.stderr)
            markets_data = await fetch_gamma_markets(simple_params)
            
            if not markets_data:
                # Try without any parameters
                print(f"[DEBUG] Simple request failed, trying without parameters", file=sys.stderr)
                markets_data = await fetch_gamma_markets({})
            
            if not markets_data:
                # Try with the original parameters
                print(f"[DEBUG] Trying with original parameters", file=sys.stderr)
                params = {
                    "active": arguments.get("active", True),
                    "closed": arguments.get("closed", False),
                    "limit": arguments.get("limit", 10),
                    "offset": arguments.get("offset", 0),
                }
                
                # Add optional sorting
                order_by = arguments.get("order_by", "volume")
                if order_by:
                    params["order"] = "desc"
                    params["orderBy"] = order_by
                
                markets_data = await fetch_gamma_markets(params)
            
            if not markets_data:
                return [types.TextContent(
                    type="text", 
                    text="Unable to fetch markets. Check the server logs for debugging information.\n\n"
                         "Possible issues:\n"
                         "- Network connectivity to gamma-api.polymarket.com\n"
                         "- API endpoint changes\n"
                         "- Rate limiting\n"
                         "- Geographic restrictions"
                )]
            
            formatted_list = format_market_list(markets_data)
            return [types.TextContent(type="text", text=formatted_list)]

        elif name == "get-market-prices":
            market_id = arguments.get("market_id")
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            market_data = await fetch_gamma_market(market_id)
            formatted_prices = format_market_prices(market_data)
            return [types.TextContent(type="text", text=formatted_prices)]

        elif name == "get-market-history":
            market_id = arguments.get("market_id")
            timeframe = arguments.get("timeframe", "7d")
            
            if not market_id:
                return [types.TextContent(type="text", text="Missing market_id parameter")]
            
            # For now, return basic market data since Gamma API doesn't provide detailed history
            market_data = await fetch_gamma_market(market_id)
            formatted_history = format_market_history(market_data)
            return [types.TextContent(type="text", text=formatted_history)]
            
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        print(f"[DEBUG] Error in handle_call_tool: {type(e).__name__}: {str(e)}", file=sys.stderr)
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()}", file=sys.stderr)
        return [types.TextContent(type="text", text=f"Error executing tool: {str(e)}")]

async def main():
    """Main entry point for the MCP server."""
    print("[DEBUG] Starting polymarket-mcp server v0.2.0", file=sys.stderr)
    print(f"[DEBUG] Gamma API URL: {GAMMA_API_URL}", file=sys.stderr)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="polymarket_predictions",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
