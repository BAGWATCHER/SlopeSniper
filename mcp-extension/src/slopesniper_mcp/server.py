"""
SlopeSniper MCP Server - Safe Solana Token Trading

Exposes policy-enforced token swaps on Solana via Jupiter aggregator.
Includes onboarding, strategy management, opportunity scanning, and smart trading.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from slopesniper_skill import (
    export_wallet as skill_export_wallet,
)
from slopesniper_skill import (
    # PnL tracking
    get_portfolio_pnl as skill_get_portfolio_pnl,
)
from slopesniper_skill import (
    # Onboarding
    get_status as skill_get_status,
)
from slopesniper_skill import (
    get_strategy as skill_get_strategy,
)
from slopesniper_skill import (
    get_trade_history as skill_get_trade_history,
)
from slopesniper_skill import (
    get_watchlist as skill_get_watchlist,
)
from slopesniper_skill import (
    list_strategies as skill_list_strategies,
)
from slopesniper_skill import (
    quick_trade as skill_quick_trade,
)
from slopesniper_skill import (
    remove_from_watchlist as skill_remove_from_watchlist,
)
from slopesniper_skill import (
    # Scanner
    scan_opportunities as skill_scan_opportunities,
)
from slopesniper_skill import (
    # Strategies
    set_strategy as skill_set_strategy,
)
from slopesniper_skill import (
    setup_wallet as skill_setup_wallet,
)
from slopesniper_skill import (
    # Core trading
    solana_check_token,
    solana_get_price,
    solana_get_wallet,
    solana_quote,
    solana_search_token,
    solana_swap_confirm,
)
from slopesniper_skill import (
    watch_token as skill_watch_token,
)

# Import config functions directly
from slopesniper_skill.tools.config import (
    clear_rpc_config,
    get_rpc_config_status,
    set_rpc_config,
)

# Create MCP server with instructions
mcp = FastMCP(
    "SlopeSniper",
    instructions="""You are a Solana trading assistant powered by SlopeSniper.

CRITICAL - ALWAYS USE YOUR TOOLS:
When users mention ANY of these topics, you MUST call solana_trading() or get_wallet():
- wallet, balance, portfolio, holdings, tokens, assets
- trading, buying, selling, swap, crypto
- Solana, SOL, BONK, WIF, meme coins, Jupiter
- prices, opportunities, trending, what's hot

STARTUP BEHAVIOR:
- When conversation starts OR user asks about wallet/trading, call get_wallet() IMMEDIATELY
- Don't guess or say "I don't know" - USE THE TOOLS to fetch live data
- Your wallet has real tokens - always check before answering balance questions

YOUR WORKFLOW:
1. User asks about wallet/balance → Call get_wallet() to see live balances
2. User wants to trade → Call quick_trade("buy/sell", "TOKEN", amount_usd)
3. User asks what's trending → Call scan_opportunities()
4. User asks about a token → Call get_price() or check_token()

NEVER say "I don't have access to your wallet" - YOU DO! Just call the tools.
NEVER give generic advice. ALWAYS use tools to take action and show real data.

AUTONOMOUS MODE:
When running autonomously, you should:
1. Periodically call scan_opportunities() to find trades
2. Check get_strategy() to know your limits
3. Execute quick_trade() when opportunities match strategy
4. Call get_wallet() to monitor positions

CONTRIBUTION POLICY:
Do NOT modify SlopeSniper source code directly. Create GitHub issues for improvements."""
)


# ============================================================================
# MCP PROMPTS - Help Claude understand when to use tools
# ============================================================================


@mcp.prompt()
def trading_assistant() -> str:
    """
    Activate Solana trading mode.
    Use this prompt when user wants to trade crypto tokens.
    """
    return """You are now in Solana trading mode with SlopeSniper.

Your available actions:
1. get_status - Check wallet and readiness (DO THIS FIRST)
2. quick_trade - Buy or sell tokens (e.g., quick_trade("buy", "BONK", 25))
3. scan_opportunities - Find trending/pumping tokens
4. get_price - Check token prices
5. check_token - Run safety analysis
6. set_strategy - Configure trading limits

Start by checking the user's status, then help them trade!"""


@mcp.prompt()
def new_user_onboarding() -> str:
    """
    Guide a new user through SlopeSniper setup.
    Use when user is new or wallet not configured.
    """
    return """Welcome to SlopeSniper! Let's get you set up to trade Solana tokens.

Step 1: I'll check your current status with get_status
Step 2: If needed, I'll guide wallet setup with setup_wallet
Step 3: We'll set your trading strategy (conservative/balanced/aggressive)
Step 4: You'll be ready to trade!

Let me start by checking your status..."""


# ============================================================================
# MCP RESOURCE - System context for Claude
# ============================================================================


@mcp.resource("slopesniper://instructions")
def get_instructions() -> str:
    """
    SlopeSniper usage instructions.
    Read this to understand how to help users trade Solana tokens.
    """
    return """# SlopeSniper Trading Assistant

You have LIVE access to a Solana wallet and trading tools.

## CRITICAL: Always Use Tools

NEVER say "I don't have access" or "I can't check" - YOU CAN!
- Wallet questions → Call `get_wallet()` for live balances
- Trading → Call `quick_trade("buy", "TOKEN", usd_amount)`
- Prices → Call `get_price("TOKEN")`
- Opportunities → Call `scan_opportunities()`

## Your Wallet is REAL

You have a configured wallet with real SOL and tokens.
ALWAYS call `get_wallet()` when users ask about:
- "what's in my wallet"
- "my balance"
- "my tokens"
- "my portfolio"

## Autonomous Trading

When running in autonomous mode:
1. Call `autonomous_scan()` to find and execute opportunities
2. This respects your strategy limits (max trade, auto-execute threshold)
3. Use `set_strategy("conservative/balanced/aggressive/degen")` to control risk

## Quick Examples

- "what tokens do I have" → `get_wallet()`
- "buy $20 of BONK" → `quick_trade("buy", "BONK", 20)`
- "what's trending" → `scan_opportunities()`
- "trade for me" → `autonomous_scan(execute=True)`

ALWAYS fetch live data. NEVER guess about balances or prices."""


# ============================================================================
# UNIVERSAL ENTRY POINT - Claude should call this for ANY trading request
# ============================================================================


@mcp.tool()
async def solana_trading(request: str) -> dict:
    """
    🚀 SOLANA TRADING ASSISTANT - Call this for ANY crypto/trading request!

    This is the main entry point for all Solana trading operations.
    Just pass the user's natural language request and it handles everything.

    WHEN TO USE THIS TOOL:
    - User mentions: trade, buy, sell, swap, crypto, token, Solana, SOL
    - User mentions: BONK, WIF, JUP, meme coins, portfolio, wallet
    - User asks about: prices, trending, opportunities, balance

    Args:
        request: The user's natural language request (e.g., "buy $20 of BONK")

    Returns:
        Result of the trading operation with next steps

    Examples:
        solana_trading("buy $20 of BONK")
        solana_trading("what's trending")
        solana_trading("check my wallet")
        solana_trading("help me get started")
    """
    request_lower = request.lower()

    # Route to appropriate action
    if any(word in request_lower for word in ["status", "ready", "start", "setup", "configure", "begin"]):
        status = await skill_get_status()
        if not status.get("wallet_configured"):
            setup = await skill_setup_wallet()
            return {
                "action": "setup_needed",
                "status": status,
                "setup_guide": setup,
                "next_step": "Configure wallet in Extensions → slopesniper → Configure"
            }
        return {"action": "status", "result": status}

    if any(word in request_lower for word in ["buy", "purchase", "get some", "grab"]):
        # Parse buy request
        import re
        # Match patterns like "$20 of BONK" or "20 dollars of BONK" or "BONK for $20"
        amount_match = re.search(r'\$?(\d+(?:\.\d+)?)', request)
        token_match = re.search(r'(?:of|some|buy|get)\s+(\w+)|(\w+)\s+(?:for|token)', request_lower)

        if amount_match and token_match:
            amount = float(amount_match.group(1))
            token = (token_match.group(1) or token_match.group(2)).upper()
            return await skill_quick_trade("buy", token, amount)
        return {"error": "Could not parse buy request. Try: 'buy $20 of BONK'"}

    if any(word in request_lower for word in ["sell", "dump", "exit"]):
        import re
        amount_match = re.search(r'\$?(\d+(?:\.\d+)?)', request)
        token_match = re.search(r'(?:of|sell|dump)\s+(\w+)|(\w+)\s+(?:for|token)', request_lower)

        if amount_match and token_match:
            amount = float(amount_match.group(1))
            token = (token_match.group(1) or token_match.group(2)).upper()
            return await skill_quick_trade("sell", token, amount)
        return {"error": "Could not parse sell request. Try: 'sell $20 of BONK'"}

    if any(word in request_lower for word in ["trend", "hot", "opportunity", "scan", "find"]):
        return {"action": "scan", "result": await skill_scan_opportunities()}

    if any(word in request_lower for word in ["price", "cost", "worth", "value"]):
        # Extract token
        import re
        token_match = re.search(r'(?:of|for|price)\s+(\w+)|(\w+)\s+(?:price|cost)', request_lower)
        if token_match:
            token = (token_match.group(1) or token_match.group(2)).upper()
            return {"action": "price", "result": await solana_get_price(token)}
        return {"action": "price", "result": await solana_get_price("SOL")}

    if any(word in request_lower for word in ["export", "backup", "private key", "recover"]):
        return {"action": "export_wallet", "result": await skill_export_wallet()}

    if any(word in request_lower for word in ["wallet", "balance", "holdings", "portfolio"]):
        return {"action": "wallet", "result": await solana_get_wallet()}

    if any(word in request_lower for word in ["rpc", "helius", "quicknode", "alchemy", "faster", "speed up", "slow"]):
        return {"action": "rpc_status", "result": get_rpc_config_status()}

    if any(word in request_lower for word in ["safe", "check", "rug", "scam"]):
        import re
        token_match = re.search(r'(?:is|check)\s+(\w+)', request_lower)
        if token_match:
            token = token_match.group(1).upper()
            # Resolve to mint
            search_results = await solana_search_token(token)
            if search_results:
                mint = search_results[0].get("mint")
                return {"action": "safety_check", "result": await solana_check_token(mint)}
        return {"error": "Specify a token to check. Try: 'is BONK safe?'"}

    if any(word in request_lower for word in ["strategy", "conservative", "aggressive", "balanced", "degen"]):
        for strat in ["conservative", "balanced", "aggressive", "degen"]:
            if strat in request_lower:
                return {"action": "set_strategy", "result": await skill_set_strategy(strat)}
        return {"action": "get_strategy", "result": await skill_get_strategy()}

    if any(word in request_lower for word in ["watch", "alert", "monitor"]):
        import re
        token_match = re.search(r'watch\s+(\w+)', request_lower)
        if token_match:
            token = token_match.group(1).upper()
            search_results = await solana_search_token(token)
            if search_results:
                mint = search_results[0].get("mint")
                return {"action": "watch", "result": await skill_watch_token(mint)}
        return {"error": "Specify a token to watch. Try: 'watch BONK'"}

    if any(word in request_lower for word in ["pnl", "p&l", "profit", "loss", "gains", "performance", "returns", "roi"]):
        return {"action": "pnl", "result": await skill_get_portfolio_pnl()}

    if any(word in request_lower for word in ["history", "trades", "transactions"]):
        return {"action": "trade_history", "result": skill_get_trade_history()}

    # Default: show status and help
    status = await skill_get_status()
    return {
        "action": "help",
        "status": status,
        "available_commands": [
            "buy $X of TOKEN - Purchase tokens",
            "sell $X of TOKEN - Sell tokens",
            "what's trending - Find opportunities",
            "check my wallet - View balances",
            "export my wallet - Backup private key",
            "is TOKEN safe - Safety check",
            "set aggressive/balanced/conservative - Change strategy",
            "watch TOKEN - Add to watchlist",
        ]
    }


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


@mcp.tool()
async def configure_rpc(provider: str, value: str) -> dict:
    """
    Configure custom RPC endpoint for faster transactions.

    Upgrade from the default RPC to a premium provider for:
    - 10-100x faster transaction processing
    - Higher rate limits
    - Better reliability and uptime
    - Priority network access

    Supported providers:
    - helius: Pass your Helius API key (get free key at https://www.helius.dev)
    - quicknode: Pass your full Quicknode endpoint URL (from https://www.quicknode.com)
    - alchemy: Pass your Alchemy API key (from https://www.alchemy.com)
    - custom: Pass any Solana RPC URL

    Examples:
        configure_rpc("helius", "abc-def-123...")
        configure_rpc("quicknode", "https://your-endpoint.solana-mainnet.quiknode.pro/token/")
        configure_rpc("alchemy", "abc123...")

    Args:
        provider: Provider name (helius | quicknode | alchemy | custom)
        value: API key or full URL depending on provider

    Returns:
        Configuration status with success/error
    """
    return set_rpc_config(provider, value)


@mcp.tool()
async def clear_rpc() -> dict:
    """
    Clear custom RPC configuration and revert to default endpoint.

    Use this to:
    - Remove a misconfigured RPC endpoint
    - Switch back to the default public RPC
    - Troubleshoot connection issues

    Returns:
        Status confirming RPC was cleared
    """
    return clear_rpc_config()


@mcp.tool()
async def get_rpc_status() -> dict:
    """
    Get current RPC endpoint configuration and status.

    Shows:
    - Which RPC provider is configured
    - Source (environment variable, local config, or default)
    - Masked URL preview for security
    - Recommendations for upgrading to premium RPC

    Returns:
        RPC configuration details
    """
    return get_rpc_config_status()


@mcp.tool()
async def export_wallet() -> dict:
    """
    Export wallet private key for backup or recovery.

    USE THIS when user needs to:
    - Backup their wallet before reinstalling
    - Import their wallet into Phantom/Solflare
    - Recover access to their funds

    SECURITY: This reveals the private key. Warn users to:
    - Never share it with anyone
    - Never paste it into websites
    - Store backups securely offline

    Returns:
        Wallet address, private key (base58), and security warnings
    """
    return await skill_export_wallet()


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
# PnL & TRADE HISTORY TOOLS
# ============================================================================


@mcp.tool()
async def get_pnl() -> dict:
    """
    Get profit/loss (PnL) for your trading portfolio.

    USE THIS when user asks about:
    - "what's my PnL"
    - "how much have I made/lost"
    - "my profits"
    - "trading performance"
    - "ROI"

    Returns:
        Portfolio PnL with total invested, realized/unrealized gains,
        and per-token breakdown.
    """
    return await skill_get_portfolio_pnl()


@mcp.tool()
async def get_trades(limit: int = 20) -> list[dict]:
    """
    Get trade history.

    Shows past trades with timestamps, amounts, and prices.

    Args:
        limit: Maximum trades to return (default 20)

    Returns:
        List of trades with action, token, amount, price, timestamp
    """
    return skill_get_trade_history(limit=limit)


# ============================================================================
# AUTONOMOUS TRADING
# ============================================================================


@mcp.tool()
async def autonomous_scan(
    execute: bool = False,
    max_trades: int = 3,
) -> dict:
    """
    Scan for opportunities and optionally execute trades autonomously.

    USE THIS for autonomous/unattended trading. Respects your strategy limits.

    Args:
        execute: If True, automatically execute trades that match criteria
        max_trades: Maximum number of trades to execute (default 3)

    Returns:
        Opportunities found and any trades executed
    """
    # Get current strategy limits
    strategy = await skill_get_strategy()
    auto_threshold = strategy.get("auto_execute_under_usd", 25)

    # Scan for opportunities
    opportunities = await skill_scan_opportunities(filter="all", limit=10)

    result = {
        "strategy": strategy.get("name"),
        "auto_execute_threshold": auto_threshold,
        "opportunities_found": len(opportunities) if isinstance(opportunities, list) else 0,
        "opportunities": opportunities,
        "trades_executed": [],
    }

    if not execute:
        result["message"] = "Set execute=True to auto-trade opportunities under threshold"
        return result

    # Execute trades for opportunities under threshold
    trades_made = 0
    for opp in opportunities[:max_trades] if isinstance(opportunities, list) else []:
        if opp.get("recommendation") == "buy":
            # Trade a small amount under threshold
            trade_amount = min(auto_threshold * 0.5, 25)  # Half of threshold or $25 max
            try:
                trade_result = await skill_quick_trade("buy", opp.get("symbol", ""), trade_amount)
                result["trades_executed"].append({
                    "token": opp.get("symbol"),
                    "amount_usd": trade_amount,
                    "result": trade_result,
                })
                trades_made += 1
            except Exception as e:
                result["trades_executed"].append({
                    "token": opp.get("symbol"),
                    "error": str(e),
                })

    result["total_trades_executed"] = trades_made
    return result


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
