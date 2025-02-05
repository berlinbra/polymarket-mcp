# PolyMarket MCP Server
[![smithery badge](https://smithery.ai/badge/polymarket_mcp)](https://smithery.ai/server/polymarket_mcp)

A Model Context Protocol (MCP) server that provides access to prediction market data through the PolyMarket API. This server implements a standardized interface for retrieving market information, prices, and historical data from prediction markets.

## Features

- Real-time prediction market data with current prices and probabilities
- Detailed market information including categories, resolution dates, and descriptions
- Historical price and volume data with customizable timeframes (1d, 7d, 30d, all)
- Built-in error handling and rate limit management
- Clean data formatting for easy consumption

## Installation

#### Installing via Smithery

To install PolyMarket Predictions for Claude Desktop automatically via [Smithery](https://smithery.ai/server/polymarket_mcp):

```bash
npx -y @smithery/cli install polymarket_mcp --client claude
```

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
            "polymarket-mcp" //or src/polymarket_mcp/server.py
            ],
            "env": {
                "KEY": "<insert poly market api key>",
                "FUNDER": "<insert polymarket wallet address"
            }
        }
    }
```

### Running Locally
1. Clone the repository and install dependencies:

#### Install Libraries
```
uv pip install -e .
```

### Running 
After connecting Claude client with the MCP tool via json file and installing the packages, Claude should see the server's mcp tools:

You can run the sever yourself via:
In polymarket-mcp repo: 
```
uv run src/polymarket_mcp/server.py
```

*if you want to run the server inspector along with the server: 
```
npx @modelcontextprotocol/inspector uv --directory C:\\Users\\{INSERT_USER}\\YOUR\\PATH\\TO\\polymarket-mcp run src/polymarket_mcp/server.py
```

2. Create a `.env` file with your PolyMarket API key:
```
Key=your_api_key_here
Funder=poly market wallet address
```

After connecting Claude client with the MCP tool via json file, run the server:
In alpha-vantage-mcp repo: `uv run src/polymarket_mcp/server.py`


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
        "description": "Market ID or slug"
    }
}
```

**Example Response:**
```
Title: Example Market
Category: Politics
Status: Open
Resolution Date: 2024-12-31
Volume: $1,234,567.89
Liquidity: $98,765.43
Description: This is an example prediction market...
---
```

### list-markets

**Input Schema:**
```json
{
    "status": {
        "type": "string",
        "description": "Filter by market status",
        "enum": ["open", "closed", "resolved"]
    },
    "limit": {
        "type": "integer",
        "description": "Number of markets to return",
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
}
```

**Example Response:**
```
Available Markets:

ID: market-123
Title: US Presidential Election 2024
Status: Open
Volume: $1,234,567.89
---

ID: market-124
Title: Oscar Best Picture 2024
Status: Open
Volume: $234,567.89
---
```

### get-market-prices

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Market ID or slug"
    }
}
```

**Example Response:**
```
Current Market Prices for US Presidential Election 2024

Outcome: Democratic
Price: $0.6500
Probability: 65.0%
---

Outcome: Republican
Price: $0.3500
Probability: 35.0%
---
```

### get-market-history

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Market ID or slug"
    },
    "timeframe": {
        "type": "string",
        "description": "Time period for historical data",
        "enum": ["1d", "7d", "30d", "all"],
        "default": "7d"
    }
}
```

**Example Response:**
```
Historical Data for US Presidential Election 2024
Time Period: 7d

Time: 2024-01-20T12:00:00Z
Price: $0.6500
Volume: $123,456.78
---

Time: 2024-01-19T12:00:00Z
Price: $0.6300
Volume: $98,765.43
---
```

## Error Handling

The server includes comprehensive error handling for various scenarios:

- Rate limiting (429 errors)
- Invalid API keys (403 errors)
- Invalid market IDs (404 errors)
- Network connectivity issues
- API timeout conditions (30-second timeout)
- Malformed responses

Error messages are returned in a clear, human-readable format.

## Prerequisites

- Python 3.9 or higher
- httpx>=0.24.0
- mcp-core
- python-dotenv>=1.0.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.
