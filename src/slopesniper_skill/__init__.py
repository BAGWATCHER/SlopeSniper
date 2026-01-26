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

__version__ = "0.1.0"

from .tools import (
    solana_check_token,
    solana_get_price,
    solana_get_wallet,
    solana_quote,
    solana_search_token,
    solana_swap_confirm,
)
from .tools.config import PolicyConfig, get_policy_config
from .tools.policy import KNOWN_SAFE_MINTS, PolicyResult, check_policy

__all__ = [
    # Version
    "__version__",
    # Tools
    "solana_get_price",
    "solana_search_token",
    "solana_check_token",
    "solana_get_wallet",
    "solana_quote",
    "solana_swap_confirm",
    # Config
    "PolicyConfig",
    "get_policy_config",
    # Policy
    "check_policy",
    "PolicyResult",
    "KNOWN_SAFE_MINTS",
]
