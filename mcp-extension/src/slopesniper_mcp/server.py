"""
SlopeSniper MCP Server - Safe Solana Token Trading

Exposes policy-enforced token swaps on Solana via Jupiter aggregator.
Includes onboarding, strategy management, opportunity scanning, and smart trading.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from slopesniper_skill import (
    # Core trading
    solana_check_token,
    solana_get_price,
    solana_get_wallet,
    solana_quote,
    solana_search_token,
    solana_swap_confirm,
    quick_trade as skill_quick_trade,
    # Onboarding
    get_status as skill_get_status,
    setup_wallet as skill_setup_wallet,
    # Strategies
    set_strategy as skill_set_strategy,
    get_strategy as skill_get_strategy,
    list_strategies as skill_list_strategies,
    # Scanner
    scan_opportunities as skill_scan_opportunities,
    watch_token as skill_watch_token,
    get_watchlist as skill_get_watchlist,
    remove_from_watchlist as skill_remove_from_watchlist,
)

# Create MCP server
mcp = FastMCP("SlopeSniper")


# ============================================================================
# ONBOARDING TOOLS - Start here!
# ============================================================================


@mcp.tool()
async def get_status() -> dict:
    """
    Check if SlopeSniper is ready to trade.

    USE THIS FIRST when a user wants to trade. Shows:
    - Wallet configuration status
    - Current SOL balance
    - Active trading strategy and limits

    Returns:
        Status with wallet_configured, sol_balance, strategy info, ready_to_trade
    """
    return await skill_get_status()


@mcp.tool()
async def setup_wallet(private_key: str | None = None) -> dict:
    """
    Guide user through wallet setup.

    If private_key provided: Validates it and shows the address.
    If not provided: Returns step-by-step setup instructions.

    SECURITY TIPS for users:
    - Use a DEDICATED trading wallet, not main holdings
    - Only fund with amounts willing to risk
    - Key is stored locally on their machine

    Args:
        private_key: Optional wallet private key (base58 or JSON array)

    Returns:
        Setup status and instructions
    """
    return await skill_setup_wallet(private_key)


# ============================================================================
# STRATEGY TOOLS - Configure trading style
# ============================================================================


@mcp.tool()
async def set_strategy(
    strategy: str | None = None,
    max_trade_usd: float | None = None,
    auto_execute_under_usd: float | None = None,
    max_loss_pct: float | None = None,
    slippage_bps: int | None = None,
    require_rugcheck: bool | None = None,
) -> dict:
    """
    Set trading strategy - presets or custom.

    PRESETS:
    - "conservative": $25 max, $10 auto, rugcheck ON (beginners)
    - "balanced": $100 max, $25 auto, rugcheck ON (most users)
    - "aggressive": $500 max, $50 auto, rugcheck OFF (experienced)
    - "degen": $1000 max, $100 auto, rugcheck OFF (YOLO)

    Or customize individual parameters to override preset values.

    Args:
        strategy: Preset name or None for custom
        max_trade_usd: Maximum USD per trade
        auto_execute_under_usd: Auto-trade threshold (no confirmation needed)
        max_loss_pct: Stop-loss percentage
        slippage_bps: Slippage tolerance (100 = 1%)
        require_rugcheck: Run safety check before trading

    Returns:
        Active strategy configuration
    """
    return await skill_set_strategy(
        strategy=strategy,
        max_trade_usd=max_trade_usd,
        auto_execute_under_usd=auto_execute_under_usd,
        max_loss_pct=max_loss_pct,
        slippage_bps=slippage_bps,
        require_rugcheck=require_rugcheck,
    )


@mcp.tool()
async def get_strategy() -> dict:
    """
    Get current trading strategy and all limits.

    Shows active strategy, thresholds, and available presets.
    """
    return await skill_get_strategy()


@mcp.tool()
async def list_strategies() -> dict:
    """
    List all available strategy presets.

    Shows all presets with their configurations and which is active.
    """
    return await skill_list_strategies()


# ============================================================================
# SCANNER TOOLS - Find opportunities
# ============================================================================


@mcp.tool()
async def scan_opportunities(
    filter: str = "all",
    min_liquidity_usd: float = 50000,
    min_volume_usd: float = 10000,
    limit: int = 10,
) -> list[dict]:
    """
    Scan for trading opportunities.

    Finds tokens based on filter:
    - "trending": High volume tokens with activity
    - "pumping": Tokens with >10% price increase
    - "all": Combination of signals

    Each result includes recommendation (buy/watch/avoid) and reason.

    Args:
        filter: "all", "trending", "pumping", "new_listings"
        min_liquidity_usd: Minimum liquidity (safety filter)
        min_volume_usd: Minimum 24h volume
        limit: Max results to return

    Returns:
        List of opportunities with recommendations
    """
    return await skill_scan_opportunities(
        filter=filter,
        min_liquidity_usd=min_liquidity_usd,
        min_volume_usd=min_volume_usd,
        limit=limit,
    )


@mcp.tool()
async def watch_token(mint: str, alert_on: str = "10% change") -> dict:
    """
    Add token to watchlist.

    Args:
        mint: Token mint address
        alert_on: Alert condition (e.g., "10% change", "price above $1")

    Returns:
        Confirmation of watchlist addition
    """
    return await skill_watch_token(mint, alert_on)


@mcp.tool()
async def get_watchlist() -> list[dict]:
    """
    Get all watched tokens with current prices.

    Returns:
        List of watched tokens with status
    """
    return await skill_get_watchlist()


@mcp.tool()
async def remove_from_watchlist(mint: str) -> dict:
    """
    Remove token from watchlist.

    Args:
        mint: Token mint address

    Returns:
        Confirmation
    """
    return await skill_remove_from_watchlist(mint)


# ============================================================================
# TRADING TOOLS - Execute trades
# ============================================================================


@mcp.tool()
async def quick_trade(
    action: str,
    token: str,
    amount_usd: float,
) -> dict:
    """
    One-step trade with smart defaults - THE EASIEST WAY TO TRADE.

    Just specify buy/sell, token, and USD amount. Handles everything else.
    Auto-executes if under strategy threshold, otherwise returns quote.

    Args:
        action: "buy" or "sell"
        token: Token symbol ("BONK") or mint address
        amount_usd: USD amount to trade

    Returns:
        If auto-executed: Result with signature and explorer link
        If manual needed: Quote with intent_id to confirm

    Examples:
        quick_trade("buy", "BONK", 20)  -> Buy $20 of BONK
        quick_trade("sell", "WIF", 50)  -> Sell $50 of WIF
    """
    return await skill_quick_trade(action, token, amount_usd)


@mcp.tool()
async def get_price(token: str) -> dict:
    """
    Get current USD price for a Solana token.

    Args:
        token: Token mint address OR symbol (e.g., "SOL", "BONK")

    Returns:
        Price info with mint, symbol, price_usd, and market_cap
    """
    return await solana_get_price(token)


@mcp.tool()
async def search_token(query: str) -> list[dict]:
    """
    Search for Solana tokens by name or symbol.

    Args:
        query: Search term (e.g., "bonk", "pepe", "jupiter")

    Returns:
        List of matching tokens with symbol, name, mint, verified, liquidity
    """
    return await solana_search_token(query)


@mcp.tool()
async def check_token(mint_address: str) -> dict:
    """
    Run rugcheck safety analysis on a token.

    Args:
        mint_address: Token mint address (NOT symbol)

    Returns:
        Safety analysis with is_safe, score, risk_factors, reason
    """
    return await solana_check_token(mint_address)


@mcp.tool()
async def get_wallet(address: str | None = None) -> dict:
    """
    Get wallet balances and token holdings.

    Args:
        address: Wallet address (optional - defaults to configured wallet)

    Returns:
        Wallet info with address, sol_balance, sol_value_usd, tokens list
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
    Get swap quote with policy checks (does NOT execute).

    Step 1 of manual two-step flow. Use swap_confirm() to execute.
    Policy checks run here - blocks if trade fails safety checks.

    For easier trading, use quick_trade() instead.

    Args:
        from_mint: Token to sell (MUST be mint address)
        to_mint: Token to buy (MUST be mint address)
        amount: Amount in token units (e.g., "1.5" for 1.5 SOL)
        slippage_bps: Slippage tolerance (default 50 = 0.5%)

    Returns:
        Quote with intent_id, amounts, price_impact, expiry
    """
    return await solana_quote(from_mint, to_mint, amount, slippage_bps)


@mcp.tool()
async def swap_confirm(intent_id: str) -> dict:
    """
    Execute a previously quoted swap.

    Step 2 of manual flow. Use quote() first to get intent_id.
    Each intent is one-time use and expires after 2 minutes.

    Args:
        intent_id: UUID from a previous quote() call

    Returns:
        Execution result with success, signature, amounts, explorer_url
    """
    return await solana_swap_confirm(intent_id)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
