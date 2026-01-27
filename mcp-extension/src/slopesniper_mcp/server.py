"""
SlopeSniper MCP Server - Safe Solana Token Trading

Exposes policy-enforced, two-step token swaps on Solana via Jupiter aggregator.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from slopesniper_skill import (
    solana_check_token,
    solana_get_price,
    solana_get_wallet,
    solana_quote,
    solana_search_token,
    solana_swap_confirm,
)

# Create MCP server
mcp = FastMCP("SlopeSniper")


@mcp.tool()
async def get_price(token: str) -> dict:
    """
    Get current USD price for a Solana token.

    Args:
        token: Token mint address OR symbol (e.g., "SOL", "BONK", or mint address)

    Returns:
        Price info with mint, symbol, price_usd, and optional market_cap
    """
    return await solana_get_price(token)


@mcp.tool()
async def search_token(query: str) -> list[dict]:
    """
    Search for Solana tokens by name or symbol.

    Args:
        query: Search term (e.g., "bonk", "pepe", "jupiter")

    Returns:
        List of matching tokens with symbol, name, mint, verified status, and liquidity
    """
    return await solana_search_token(query)


@mcp.tool()
async def check_token(mint_address: str) -> dict:
    """
    Run rugcheck safety analysis on a token.

    Args:
        mint_address: Token mint address (NOT symbol - must be a Solana address)

    Returns:
        Safety analysis with is_safe, score, risk_factors, and reason
    """
    return await solana_check_token(mint_address)


@mcp.tool()
async def get_wallet(address: str | None = None) -> dict:
    """
    Get wallet balances and token holdings.

    Args:
        address: Wallet address (optional - defaults to configured wallet)

    Returns:
        Wallet info with address, sol_balance, sol_value_usd, and tokens list
    """
    return await solana_get_wallet(address)


@mcp.tool()
async def quote(
    from_mint: str,
    to_mint: str,
    amount: str,
    slippage_bps: int = 50,
) -> dict:
    """
    Get a swap quote with policy checks (does NOT execute the trade).

    This is step 1 of 2. After getting a quote, use swap_confirm() to execute.
    Policy checks run here - trade will be blocked if it fails safety checks.

    Args:
        from_mint: Token to sell (MUST be mint address, not symbol)
        to_mint: Token to buy (MUST be mint address, not symbol)
        amount: Amount to swap in token units (e.g., "1.5" for 1.5 SOL)
        slippage_bps: Slippage tolerance in basis points (default 50 = 0.5%)

    Returns:
        Quote with intent_id, amounts, price_impact, route, expiry, and policy checks
    """
    return await solana_quote(from_mint, to_mint, amount, slippage_bps)


@mcp.tool()
async def swap_confirm(intent_id: str) -> dict:
    """
    Execute a previously quoted swap.

    This is step 2 of 2. Use quote() first to get an intent_id.
    Each intent can only be used once and expires after 2 minutes.

    Args:
        intent_id: UUID from a previous quote() call

    Returns:
        Execution result with success, signature, amounts, and explorer_url
    """
    return await solana_swap_confirm(intent_id)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
