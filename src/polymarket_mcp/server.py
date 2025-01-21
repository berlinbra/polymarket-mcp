from typing import Any
import asyncio
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.objects import GetMarketRequest
from eth_utils import to_checksum_address

# Load environment variables
load_dotenv()

API_KEY = os.getenv('POLYMARKET_API_KEY')
if not API_KEY:
    raise ValueError("POLYMARKET_API_KEY environment variable is required")

# Initialize CLOB client
NETWORK = os.getenv('NETWORK', 'mainnet')  # Default to mainnet if not specified
clob_client = ClobClient(network=NETWORK, api_key=API_KEY)

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
                        "description": "Market ID (condition ID) or market address",
                    },
                },
                "required": ["market_id"],
            },
        ),
    ]

def format_market_info(market_data: dict) -> str:
    """Format market information into a concise string."""
    try:
        if not market_data:
            return "No market information available"
            
        # Convert Wei to ETH/USDC for amounts
        volume = float(market_data.get('volume', 0)) / 1e6  # Assuming USDC decimals
        liquidity = float(market_data.get('liquidity', 0)) / 1e6
        
        # Format the response
        response = [
            f"Title: {market_data.get('question', 'N/A')}",
            f"Category: {market_data.get('category', 'N/A')}",
            f"Status: {market_data.get('status', 'N/A')}",
            f"Resolution Time: {market_data.get('resolutionTime', 'N/A')}",
            f"Volume: ${volume:,.2f}",
            f"Liquidity: ${liquidity:,.2f}",
            "\nOutcomes:"
        ]
        
        # Add outcomes information
        for outcome in market_data.get('outcomes', []):
            prob = float(outcome.get('prob', 0)) * 100
            response.append(f"- {outcome.get('title', 'N/A')}: {prob:.1f}%")
            
        return "\n".join(response)
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
    
    if name == "get-market-info":
        market_id = arguments.get("market_id")
        if not market_id:
            return [types.TextContent(type="text", text="Missing market_id parameter")]
        
        try:
            # Try to format as an address first
            try:
                market_address = to_checksum_address(market_id)
                request = GetMarketRequest(market_address=market_address)
            except ValueError:
                # If not a valid address, treat as a condition ID
                request = GetMarketRequest(condition_id=market_id)
            
            market_data = await clob_client.get_market(request)
            
            if not market_data:
                return [types.TextContent(type="text", text="Market not found")]
            
            formatted_info = format_market_info(market_data)
            return [types.TextContent(type="text", text=formatted_info)]
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return [types.TextContent(type="text", text="Market not found")]
            return [types.TextContent(type="text", text=f"Error fetching market data: {error_msg}")]
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