"""
SlopeSniper Skill - Safe Solana Token Trading for Claude Code

A Claude Code skill that provides policy-enforced, two-step token swaps
on Solana via Jupiter aggregator.

Features:
- Price lookup and token search
- Rugcheck safety analysis
- Wallet balance viewing
- Two-step swap flow (quote → confirm)
- Policy gates for safety limits

Example:
    >>> from slopesniper_skill import solana_get_price, solana_quote
    >>> import asyncio
    >>>
    >>> async def main():
    ...     price = await solana_get_price("SOL")
    ...     print(f"SOL: ${price['price_usd']}")
    ...
    >>> asyncio.run(main())
"""

# Version is the single source of truth - update here for releases
# Follow semantic versioning: MAJOR.MINOR.PATCH
# Beta versions use 0.x.x (0.MINOR.PATCH)
__version__ = "0.2.5"

from .tools import (
    # Core trading tools
    solana_get_price,
    solana_search_token,
    solana_check_token,
    solana_resolve_token,
    solana_get_wallet,
    solana_quote,
    solana_swap_confirm,
    quick_trade,
    # Onboarding
    get_status,
    setup_wallet,
    export_wallet,
    # Strategies
    set_strategy,
    get_strategy,
    list_strategies,
    # PnL tracking
    record_trade,
    get_trade_history,
    get_portfolio_pnl,
    # Scanner
    scan_opportunities,
    watch_token,
    get_watchlist,
    remove_from_watchlist,
)

from .tools.config import PolicyConfig, get_policy_config
from .tools.policy import check_policy, PolicyResult, KNOWN_SAFE_MINTS

__all__ = [
    # Version
    "__version__",
    # Core Tools
    "solana_get_price",
    "solana_search_token",
    "solana_check_token",
    "solana_resolve_token",
    "solana_get_wallet",
    "solana_quote",
    "solana_swap_confirm",
    "quick_trade",
    # Onboarding
    "get_status",
    "setup_wallet",
    "export_wallet",
    # Strategies
    "set_strategy",
    "get_strategy",
    "list_strategies",
    # PnL tracking
    "record_trade",
    "get_trade_history",
    "get_portfolio_pnl",
    # Scanner
    "scan_opportunities",
    "watch_token",
    "get_watchlist",
    "remove_from_watchlist",
    # Config
    "PolicyConfig",
    "get_policy_config",
    # Policy
    "check_policy",
    "PolicyResult",
    "KNOWN_SAFE_MINTS",
]
