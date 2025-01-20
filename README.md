# PolyMarket MCP Server

A Model Context Protocol (MCP) server that provides access to prediction market data through the PolyMarket API. This server implements a standardized interface for retrieving market information, prices, and historical data from prediction markets.

## Features

- Real-time prediction market data with current prices and trading volume
- Detailed market information including categories, resolution dates, and descriptions
- Historical price and volume data with customizable timeframes
- Built-in error handling and rate limit management
- Clean data formatting for easy consumption

## Installation

#### Claude Desktop
- On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
- On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<summary>Development/Unpublished Servers Configuration</summary>

```json
    "mcpServers": {
        "polymarket-mcp": {
            "command": "uv",
            "args": [
            "--directory",
            "/Users/{INSERT_USER}/YOUR/PATH/TO/polymarket-mcp",
            "run",
            "polymarket-mcp"
            ],
            "env": {
                "POLYMARKET_API_KEY": "<insert api key>"
            }
        }
    }
```

### Running Locally
After connecting Claude client with the MCP tool via json file, run the server:
In polymarket-mcp repo: `uv run src/polymarket_mcp/server.py`

## Available Tools

The server implements four tools:
- `get-market-info`: Get detailed information about a specific prediction market
- `list-markets`: List available prediction markets with filtering options
- `get-market-prices`: Get current prices and trading information
- `get-market-history`: Get historical price and volume data

### get-market-info

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Unique identifier for the prediction market"
    }
}
```

**Example Response:**
```
Market Information:

Title: US Presidential Election 2024
Category: Politics
Status: Open
Resolution Date: 2024-11-05
Volume: $1,234,567.89
Liquidity: $98,765.43
Description: Which party's nominee will win the 2024 US Presidential Election?
```

### list-markets

**Input Schema:**
```json
{
    "status": {
        "type": "string",
        "description": "Market status filter (open, closed, resolved)",
        "optional": true
    },
    "limit": {
        "type": "integer",
        "description": "Number of markets to return (1-100)",
        "default": 10
    },
    "offset": {
        "type": "integer",
        "description": "Pagination offset",
        "default": 0
    }
}
```

### get-market-prices

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Unique identifier for the prediction market"
    }
}
```

**Example Response:**
```
Current Market Prices:

Market: US Presidential Election 2024
Time: 2024-01-20 19:45:00 UTC
Outcome A: $0.65 (Democratic)
Outcome B: $0.35 (Republican)
24h Volume: $234,567.89
Liquidity: $98,765.43
```

### get-market-history

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Unique identifier for the prediction market"
    },
    "timeframe": {
        "type": "string",
        "description": "Time period for historical data (1d, 7d, 30d, all)",
        "default": "7d"
    }
}
```

## Error Handling

The server includes comprehensive error handling for various scenarios:

- Invalid API keys
- Rate limiting
- Network connectivity issues
- Invalid market IDs
- Malformed requests
- API timeout conditions

Error messages are returned in a clear, human-readable format.

## Prerequisites

- Python 3.12 or higher
- httpx
- mcp

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.