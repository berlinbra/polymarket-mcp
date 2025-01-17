# PolyMarket MCP Server

An MCP server implementation for interacting with the PolyMarket API. This server provides tools for fetching prediction market data, including market information, prices, and historical data.

## Features

- Get detailed information about specific prediction markets
- List available prediction markets with filtering options
- Get current prices and trading information
- Fetch historical price and volume data
- Proper error handling and rate limit management
- Clean data formatting for easy consumption

## Installation

1. Clone the repository:
```bash
git clone https://github.com/berlinbra/polymarket-mcp.git
cd polymarket-mcp
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -e .
```

3. Set up your environment variables:
Create a `.env` file in the root directory with your PolyMarket API key:
```
POLYMARKET_API_KEY=your_api_key_here
```

## Usage

The server provides the following tools:

### get-market-info
Get detailed information about a specific prediction market:
```json
{
    "market_id": "your-market-id"
}
```

### list-markets
List prediction markets with optional filters:
```json
{
    "status": "open",  // optional: "open", "closed", or "resolved"
    "limit": 10,       // optional: number of markets to return (1-100)
    "offset": 0        // optional: pagination offset
}
```

### get-market-prices
Get current prices and trading information for a market:
```json
{
    "market_id": "your-market-id"
}
```

### get-market-history
Get historical price and volume data for a market:
```json
{
    "market_id": "your-market-id",
    "timeframe": "7d"  // optional: "1d", "7d", "30d", or "all"
}
```

## Running the Server

The server can be run directly using Python:

```bash
python -m polymarket_mcp.server
```

Or through the MCP client:

```bash
mcp run polymarket_predictions
```

## Response Formats

All responses are formatted as clear text with relevant information. Here's an example of a market info response:

```
Title: Example Market
Category: Politics
Status: Open
Resolution Date: 2025-12-31
Volume: $1,234,567.89
Liquidity: $98,765.43
Description: This is an example prediction market...
---
```

## Error Handling

The server includes comprehensive error handling for various scenarios:

- Invalid API keys
- Rate limiting
- Network connectivity issues
- Invalid market IDs
- Malformed requests
- API timeout conditions

Each error is returned with a clear explanation of what went wrong and, where applicable, suggestions for resolution.

## Development

For local development:

1. Fork the repository
2. Create a new branch for your feature
3. Install development dependencies:
```bash
pip install -e ".[dev]"
```
4. Make your changes
5. Submit a pull request

## License

MIT License. See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgments

- Built using the MCP (Machine Conversation Protocol) framework
- Inspired by the Alpha Vantage MCP server architecture