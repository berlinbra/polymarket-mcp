
# PolyMarket MCP Server
[![smithery badge](https://smithery.ai/badge/polymarket_mcp)](https://smithery.ai/server/polymarket_mcp)

A Model Context Protocol (MCP) server that provides access to prediction market data through the PolyMarket Gamma API. This server implements a standardized interface for retrieving market information, prices, and historical data from prediction markets.

<a href="https://glama.ai/mcp/servers/c255m147fd">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/c255m147fd/badge" alt="PolyMarket Server MCP server" />
</a>

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/berlinbra-polymarket-mcp-badge.png)](https://mseep.ai/app/berlinbra-polymarket-mcp)

## Features

- Real-time prediction market data with current prices and probabilities
- Direct integration with Polymarket's Gamma API for latest market listings
- Detailed market information including categories, resolution dates, and descriptions
- Market filtering by status (active/closed) and sorting by volume, liquidity, etc.
- Built-in error handling and async HTTP client for better performance
- Clean data formatting for easy consumption

## Recent Updates (v0.2.0)

- **Fixed issue with fetching new market listings** - Now uses Gamma API directly instead of CLOB client
- Added support for market sorting (by volume, liquidity, startDate, etc.)
- Improved async handling for better performance
- Enhanced error messages and debugging

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
                "FUNDER": "<insert polymarket wallet address>"
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
Market ID: 0x123...
Title: Will BTC reach $100k by end of 2025?
Status: Active
End Date: 2025-12-31
Volume: $1,234,567.89
Liquidity: $98,765.43
Outcomes:
  - Yes: $0.65 (65.0%)
  - No: $0.35 (35.0%)
---
```

### list-markets

**Input Schema:**
```json
{
    "active": {
        "type": "boolean",
        "description": "Filter by active markets",
        "default": true
    },
    "closed": {
        "type": "boolean",
        "description": "Filter by closed markets",
        "default": false
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
    },
    "order_by": {
        "type": "string",
        "description": "Sort markets by field",
        "enum": ["volume", "liquidity", "startDate", "endDate", "createdAt"],
        "default": "volume"
    }
}
```

**Example Response:**
```
Available Markets:

ID: 0x123...
Title: US Presidential Election 2024
Status: Active
Volume: $1,234,567.89
End Date: 2024-11-05
---

ID: 0x124...
Title: Oscar Best Picture 2024
Status: Active
Volume: $234,567.89
End Date: 2024-03-10
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
Current Market Prices for: US Presidential Election 2024

Democratic: $0.65 (65.0%)
Republican: $0.35 (35.0%)

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
Historical Data for: US Presidential Election 2024

Note: Detailed historical data requires additional API access
Current Volume: $1,234,567.89
Created: 2024-01-01T00:00:00Z
---
```

## API Changes

### Version 0.2.0
- Migrated from CLOB client's `get_markets()` to direct Gamma API calls
- Added async HTTP client for better performance
- Updated response parsing to match Gamma API structure
- Added sorting and filtering parameters for market listings

## Error Handling

The server includes comprehensive error handling for various scenarios:

- API connection errors
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
- py-clob-client (for trading operations, not used for market data)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Changelog

### v0.2.0 (2025-06-05)
- Fixed issue with fetching new market listings
- Migrated to Gamma API for market data
- Added market sorting options
- Improved async performance

### v0.1.0
- Initial release with CLOB client integration
