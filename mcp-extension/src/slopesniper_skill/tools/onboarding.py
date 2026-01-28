"""
Onboarding Tools - Easy wallet setup and status checks.

Helps users get started with SlopeSniper quickly.
Auto-generates wallet on first run.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import (
    SLOPESNIPER_DIR,
    export_backup_wallet,
    generate_wallet,
    get_backup_status,
    get_jupiter_api_key,
    get_or_create_wallet,
    get_rpc_url,
    list_wallet_backups,
    load_local_wallet,
    record_wallet_created,
    save_wallet,
)
from .strategies import get_active_strategy


@dataclass
class Status:
    """Current SlopeSniper status."""

    wallet_configured: bool
    wallet_address: str | None
    sol_balance: float | None
    strategy_name: str
    auto_execute_under_usd: float
    max_trade_usd: float
    ready_to_trade: bool
    is_new_wallet: bool = False
    private_key: str | None = None


async def create_wallet_explicit() -> dict:
    """
    Create wallet explicitly (called after user confirmation in CLI).

    This is used by the interactive `slopesniper setup` command.
    Unlike get_status(), this doesn't auto-create - it's called only
    after the user has confirmed they want a new wallet.

    Returns:
        dict with address, private_key, and instructions
    """
    private_key, address = generate_wallet()
    save_wallet(private_key, address)
    record_wallet_created()

    return {
        "success": True,
        "address": address,
        "private_key": private_key,
        "IMPORTANT": "SAVE THIS PRIVATE KEY NOW - it will NOT be shown again!",
    }


async def get_status() -> dict:
    """
    Check if SlopeSniper is ready to trade.

    On FIRST RUN: Auto-generates a new wallet and displays the private key.
    IMPORTANT: User must save the private key and fund the wallet with SOL!

    Use this tool FIRST when a user wants to trade. It tells you:
    - Whether wallet is configured
    - Current SOL balance
    - Active trading strategy and limits

    Returns:
        dict with wallet info, balance, strategy, and setup instructions
    """
    # Get or create wallet (auto-generates on first run)
    private_key, wallet_address, is_new_wallet = get_or_create_wallet()
    wallet_configured = True

    sol_balance = None
    # Get balance from Solana RPC (no API key needed)
    try:
        import aiohttp

        rpc_url = get_rpc_url()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [wallet_address],
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    lamports = data.get("result", {}).get("value", 0)
                    sol_balance = lamports / 1_000_000_000  # Convert lamports to SOL
    except Exception:
        sol_balance = None

    strategy = get_active_strategy()

    status = Status(
        wallet_configured=wallet_configured,
        wallet_address=wallet_address,
        sol_balance=sol_balance,
        strategy_name=strategy.name,
        auto_execute_under_usd=strategy.auto_execute_under_usd,
        max_trade_usd=strategy.max_trade_usd,
        ready_to_trade=wallet_configured and (sol_balance or 0) > 0.01,
        is_new_wallet=is_new_wallet,
        private_key=private_key if is_new_wallet else None,
    )

    result = {
        "wallet_configured": status.wallet_configured,
        "wallet_address": status.wallet_address,
        "sol_balance": status.sol_balance,
        "strategy": {
            "name": status.strategy_name,
            "auto_execute_under_usd": status.auto_execute_under_usd,
            "max_trade_usd": status.max_trade_usd,
        },
        "ready_to_trade": status.ready_to_trade,
    }

    # Show private key ONLY on first run (new wallet generation)
    if is_new_wallet:
        result["NEW_WALLET_CREATED"] = True
        result["private_key"] = private_key
        result["IMPORTANT"] = (
            "A NEW WALLET HAS BEEN CREATED! You MUST:\n"
            "1. SAVE THE PRIVATE KEY ABOVE - it will NOT be shown again!\n"
            "2. Send SOL to your wallet address to start trading\n"
            "3. Keep your private key secure - anyone with it can access your funds\n\n"
            f"Wallet stored (encrypted) at: {SLOPESNIPER_DIR}\n"
            "The wallet is encrypted with a machine-specific key for security."
        )
        result["tip"] = "For a guided setup experience, use 'slopesniper setup' next time."
        # Record wallet creation for backup tracking
        record_wallet_created()
    elif (sol_balance or 0) < 0.01:
        result["needs_funding"] = True
        result["funding_instructions"] = (
            f"Send SOL to your wallet address: {wallet_address}\n"
            "You need at least 0.01 SOL to start trading."
        )
    else:
        # Existing wallet with balance - check if backup reminder needed
        backup_status = get_backup_status()
        if backup_status.get("needs_reminder"):
            result["backup_reminder"] = {
                "message": f"Wallet has {sol_balance:.4f} SOL. Consider backing up your private key.",
                "last_export": backup_status.get("last_backup_export"),
                "action": "Run 'slopesniper export' to backup your private key",
            }

    # Check if user has their own Jupiter API key
    has_custom_key = get_jupiter_api_key() is not None
    result["jupiter_api_key"] = "custom" if has_custom_key else "shared"

    if not has_custom_key:
        result["performance_tip"] = {
            "message": "Using shared API key. Set your own for 10x better performance!",
            "command": "slopesniper config --set-jupiter-key YOUR_KEY",
            "get_key": "https://station.jup.ag/docs/apis/ultra-api",
        }

    return result


async def setup_wallet(private_key: str | None = None) -> dict:
    """
    Set up or import a trading wallet.

    If no private_key provided: Uses existing wallet or creates new one.
    If private_key provided: Imports that wallet (overrides existing).

    Args:
        private_key: Optional - import an existing wallet's private key

    Returns:
        dict with wallet address, private key (if new), and instructions
    """
    from .config import _parse_private_key, save_wallet

    if private_key:
        # Import provided key
        keypair = _parse_private_key(private_key)
        if not keypair:
            return {
                "success": False,
                "error": "Invalid private key format",
                "hint": "Key should be base58 encoded (from Phantom/Solflare export)",
            }

        address = str(keypair.pubkey())
        save_wallet(private_key, address)

        return {
            "success": True,
            "wallet_address": address,
            "message": f"Wallet imported! Address: {address}",
            "next_step": "Send SOL to this address to start trading.",
        }

    # Get or create wallet
    pk, address, is_new = get_or_create_wallet()

    result = {
        "success": True,
        "wallet_address": address,
        "is_new_wallet": is_new,
    }

    if is_new:
        result["private_key"] = pk
        result["IMPORTANT"] = (
            "NEW WALLET CREATED!\n\n"
            f"Address: {address}\n"
            f"Private Key: {pk}\n\n"
            "SAVE THIS PRIVATE KEY NOW - it will NOT be shown again!\n"
            "Send SOL to your address to start trading."
        )
    else:
        result["message"] = f"Using existing wallet: {address}"
        result["next_step"] = "Check balance with 'slopesniper status'"

    return result


async def export_wallet(include_backups: bool = False) -> dict:
    """
    Export wallet private key for backup purposes.

    SECURITY: This reveals the private key. Only use for:
    - Creating a backup
    - Importing into another wallet (Phantom, Solflare, etc.)
    - Disaster recovery

    Args:
        include_backups: If True, also list available backup wallets

    Returns:
        dict with private_key, address, and security warnings
    """
    wallet = load_local_wallet()

    if not wallet:
        # Check if there are backups even without current wallet
        backups = list_wallet_backups()
        if backups:
            return {
                "success": False,
                "error": "No active wallet found, but backups exist",
                "backups": backups,
                "hint": "Use 'slopesniper export --backup TIMESTAMP' to recover a backed up wallet.",
            }
        return {
            "success": False,
            "error": "No wallet found",
            "hint": "Run 'slopesniper status' to create a wallet first.",
        }

    result = {
        "success": True,
        "address": wallet["address"],
        "private_key": wallet["private_key"],
        "format": "base58",
        "WARNING": (
            "YOUR PRIVATE KEY IS SHOWN ABOVE.\n\n"
            "- Anyone with this key can STEAL ALL YOUR FUNDS\n"
            "- Never share it with anyone\n"
            "- Never paste it into websites\n"
            "- Store backups in secure, offline locations\n\n"
            "Compatible with: Phantom, Solflare, Backpack, and other Solana wallets."
        ),
    }

    # Include backup info if requested
    if include_backups:
        backups = list_wallet_backups()
        if backups:
            result["backups"] = backups
            result["backup_hint"] = (
                "Use 'slopesniper export --backup TIMESTAMP' to export a specific backup."
            )

    return result


async def list_backup_wallets() -> dict:
    """
    List all backed up wallets.

    Returns:
        dict with list of backups and their addresses
    """
    backups = list_wallet_backups()

    if not backups:
        return {
            "success": True,
            "backups": [],
            "message": "No wallet backups found.",
            "hint": "Backups are created automatically when importing/generating a new wallet.",
        }

    return {
        "success": True,
        "backups": backups,
        "count": len(backups),
        "hint": "Use 'slopesniper export --backup TIMESTAMP' to export a specific backup.",
    }


async def export_backup(timestamp: str) -> dict:
    """
    Export a specific wallet backup by timestamp.

    Args:
        timestamp: Backup timestamp (YYYYMMDD_HHMMSS format)

    Returns:
        dict with private_key, address, or error
    """
    backup = export_backup_wallet(timestamp)

    if not backup:
        backups = list_wallet_backups()
        available = [b["timestamp"] for b in backups]
        return {
            "success": False,
            "error": f"Backup not found: {timestamp}",
            "available_backups": available,
            "hint": "Use 'slopesniper export --list-backups' to see all available backups.",
        }

    if "error" in backup:
        return {
            "success": False,
            "error": backup["error"],
            "timestamp": timestamp,
        }

    return {
        "success": True,
        "address": backup["address"],
        "private_key": backup["private_key"],
        "timestamp": timestamp,
        "source": backup.get("source"),
        "WARNING": (
            "BACKUP WALLET PRIVATE KEY IS SHOWN ABOVE.\n\n"
            "- Anyone with this key can STEAL ALL YOUR FUNDS\n"
            "- Never share it with anyone\n"
            "- Never paste it into websites\n"
            "- Store backups in secure, offline locations\n\n"
            "To restore this wallet as your active wallet:\n"
            "  slopesniper setup --import-key <PRIVATE_KEY>"
        ),
    }
