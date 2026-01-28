"""
SlopeSniper Trading Tools.

Safe two-step token swaps with policy enforcement.
"""

from .config import (
    PolicyConfig,
    clear_jupiter_api_key,
    clear_rpc_config,
    get_jupiter_api_key,
    get_keypair,
    get_policy_config,
    get_rpc_config_status,
    get_rpc_url,
    get_secret,
    get_wallet_address,
    get_wallet_fingerprint,
    get_wallet_integrity_status,
    get_wallet_sync_status,
    restore_backup_wallet,
    set_rpc_config,
)
from .intents import (
    INTENT_TTL_SECONDS,
    Intent,
    create_intent,
    get_intent,
    get_intent_time_remaining,
    list_pending_intents,
    mark_executed,
)
from .onboarding import (
    export_backup,
    export_wallet,
    get_status,
    list_backup_wallets,
    setup_wallet,
)
from .policy import (
    KNOWN_SAFE_MINTS,
    PolicyResult,
    check_policy,
    format_policy_result,
    is_known_safe_mint,
)
from .scanner import (
    get_watchlist,
    remove_from_watchlist,
    scan_opportunities,
    watch_token,
)
from .solana_tools import (
    SYMBOL_TO_MINT,
    quick_trade,
    resolve_token,
    solana_check_token,
    solana_get_price,
    solana_get_wallet,
    solana_quote,
    solana_resolve_token,
    solana_search_token,
    solana_swap_confirm,
)
from .strategies import (
    STRATEGY_PRESETS,
    TradingStrategy,
    calculate_pnl_for_token,
    get_active_strategy,
    get_portfolio_pnl,
    get_strategy,
    get_trade_history,
    list_strategies,
    # PnL tracking
    record_trade,
    set_strategy,
)

__all__ = [
    # Core Tools
    "solana_get_price",
    "solana_search_token",
    "solana_check_token",
    "solana_resolve_token",
    "solana_get_wallet",
    "solana_quote",
    "solana_swap_confirm",
    "quick_trade",
    "resolve_token",
    "SYMBOL_TO_MINT",
    # Onboarding
    "get_status",
    "setup_wallet",
    "export_wallet",
    "list_backup_wallets",
    "export_backup",
    # Strategies
    "set_strategy",
    "get_strategy",
    "list_strategies",
    "get_active_strategy",
    "TradingStrategy",
    "STRATEGY_PRESETS",
    # PnL tracking
    "record_trade",
    "get_trade_history",
    "calculate_pnl_for_token",
    "get_portfolio_pnl",
    # Scanner
    "scan_opportunities",
    "watch_token",
    "get_watchlist",
    "remove_from_watchlist",
    # Config
    "get_secret",
    "get_keypair",
    "get_wallet_address",
    "get_wallet_sync_status",
    "get_wallet_integrity_status",
    "get_wallet_fingerprint",
    "restore_backup_wallet",
    "get_rpc_url",
    "get_jupiter_api_key",
    "get_policy_config",
    "PolicyConfig",
    "set_rpc_config",
    "clear_rpc_config",
    "clear_jupiter_api_key",
    "get_rpc_config_status",
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
