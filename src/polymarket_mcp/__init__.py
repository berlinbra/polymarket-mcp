"""
PolyMarket MCP Server
An MCP server implementation for interacting with the PolyMarket API.
"""

import asyncio
from .server import main as async_main

__version__ = "0.2.0"

def main():
    """Entry point wrapper that runs the async main function."""
    asyncio.run(async_main())

__all__ = ["main", "async_main"]
