
# PolyMarket MCP Server
[![smithery badge](https://smithery.ai/badge/polymarket_mcp)](https://smithery.ai/server/polymarket_mcp)

A Model Context Protocol (MCP) server that provides access to prediction market data through the PolyMarket API. This server implements a standardized interface for retrieving market information, prices, and historical data from prediction markets.

<a href="https://glama.ai/mcp/servers/c255m147fd">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/c255m147fd/badge" alt="PolyMarket Server MCP server" />
</a>

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/berlinbra-polymarket-mcp-badge.png)](https://mseep.ai/app/berlinbra-polymarket-mcp)

## Features

- Real-time prediction market data with current prices and probabilities
- Integration with PolyMarket's Gamma API for up-to-date market listings
- Proper filtering to exclude outdated/archived markets
- Detailed market information including categories, resolution dates, and descriptions
- Historical price and volume data with customizable timeframes (1d, 7d, 30d, all)
- Built-in error handling and rate limit management
- Clean data formatting for easy consumption
- Automatic fallback to CLOB API when Gamma API is unavailable

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
        "description": "Market ID (numeric ID or slug, e.g. '12' or 'will-bitcoin-reach-100k')"
    }
}
```

**Example Response:**
```
Condition ID: 0x123...
Title: Will Bitcoin reach $100,000 by December 2025?
Status: Active
End Date: 2025-12-31T23:59:59Z
Volume: $1,234,567.89
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
    "archived": {
        "type": "boolean",
        "description": "Filter by archived markets (set to false to exclude old markets)",
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
    "order": {
        "type": "string",
        "description": "Sort order",
        "enum": ["asc", "desc"],
        "default": "desc"
    }
}
```

**Example Response:**
```
Available Markets:

Condition ID: 0x456...
Title: US Presidential Election 2024
Status: Active
Category: Politics
Volume: $1,234,567.89
End Date: 2024-11-05T23:59:59Z
Slug: us-presidential-election-2024
---

Condition ID: 0x789...
Title: Will AI achieve AGI by 2030?
Status: Active
Category: Technology
Volume: $234,567.89
End Date: 2030-12-31T23:59:59Z
Slug: will-ai-achieve-agi-by-2030
---
```

### get-market-prices

**Input Schema:**
```json
{
    "market_id": {
        "type": "string",
        "description": "Market ID (numeric ID or slug)"
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
        "description": "Market ID (numeric ID or slug)"
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

Historical data retrieval not yet implemented for Gamma API
```

## API Integration

This server now uses two PolyMarket APIs:
1. **Gamma API** (`https://gamma-api.polymarket.com`) - Primary API for fetching current market listings
2. **CLOB API** (`https://clob.polymarket.com`) - Fallback API and for authenticated operations

The server automatically excludes archived markets by default to ensure you only see current, relevant prediction markets.

## Error Handling

The server includes comprehensive error handling for various scenarios:

- Rate limiting (429 errors)
- Invalid API keys (403 errors)
- Invalid market IDs (404 errors)
- Network connectivity issues
- API timeout conditions (30-second timeout)
- Malformed responses
- Automatic fallback to CLOB API when Gamma API is unavailable

Error messages are returned in a clear, human-readable format.

## Prerequisites

- Python 3.9 or higher
- httpx>=0.24.0
- mcp-core
- python-dotenv>=1.0.0
- py-clob-client

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.
