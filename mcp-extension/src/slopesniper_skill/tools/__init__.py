"""
SlopeSniper Trading Tools.

Safe two-step token swaps with policy enforcement.
"""

from .solana_tools import (
    solana_get_price,
    solana_search_token,
    solana_check_token,
    solana_get_wallet,
    solana_quote,
    solana_swap_confirm,
    quick_trade,
    resolve_token,
    SYMBOL_TO_MINT,
)

from .onboarding import (
    get_status,
    setup_wallet,
)

from .strategies import (
    set_strategy,
    get_strategy,
    list_strategies,
    get_active_strategy,
    TradingStrategy,
    STRATEGY_PRESETS,
)

from .scanner import (
    scan_opportunities,
    watch_token,
    get_watchlist,
    remove_from_watchlist,
)

from .config import (
    get_secret,
    get_keypair,
    get_wallet_address,
    get_rpc_url,
    get_jupiter_api_key,
    get_policy_config,
    PolicyConfig,
)

from .policy import (
    check_policy,
    is_known_safe_mint,
    PolicyResult,
    format_policy_result,
    KNOWN_SAFE_MINTS,
)

from .intents import (
    create_intent,
    get_intent,
    mark_executed,
    list_pending_intents,
    get_intent_time_remaining,
    Intent,
    INTENT_TTL_SECONDS,
)

__all__ = [
    # Core Tools
    "solana_get_price",
    "solana_search_token",
    "solana_check_token",
    "solana_get_wallet",
    "solana_quote",
    "solana_swap_confirm",
    "quick_trade",
    "resolve_token",
    "SYMBOL_TO_MINT",
    # Onboarding
    "get_status",
    "setup_wallet",
    # Strategies
    "set_strategy",
    "get_strategy",
    "list_strategies",
    "get_active_strategy",
    "TradingStrategy",
    "STRATEGY_PRESETS",
    # Scanner
    "scan_opportunities",
    "watch_token",
    "get_watchlist",
    "remove_from_watchlist",
    # Config
    "get_secret",
    "get_keypair",
    "get_wallet_address",
    "get_rpc_url",
    "get_jupiter_api_key",
    "get_policy_config",
    "PolicyConfig",
    # Policy
    "check_policy",
    "is_known_safe_mint",
    "PolicyResult",
    "format_policy_result",
    "KNOWN_SAFE_MINTS",
    # Intents
    "create_intent",
    "get_intent",
    "mark_executed",
    "list_pending_intents",
    "get_intent_time_remaining",
    "Intent",
    "INTENT_TTL_SECONDS",
]
