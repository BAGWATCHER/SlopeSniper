"""
Onboarding Tools - Easy wallet setup and status checks.

Helps users get started with SlopeSniper quickly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .config import get_keypair, get_wallet_address, get_rpc_url, get_secret
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


async def get_status() -> dict:
    """
    Check if SlopeSniper is ready to trade.

    Use this tool FIRST when a user wants to trade. It tells you:
    - Whether wallet is configured
    - Current SOL balance
    - Active trading strategy and limits

    Returns:
        dict with wallet_configured, wallet_address, sol_balance,
        strategy info, and ready_to_trade boolean
    """
    wallet_address = get_wallet_address()
    wallet_configured = wallet_address is not None

    sol_balance = None
    if wallet_configured:
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

    if not status.wallet_configured:
        result["setup_instructions"] = (
            "To configure your wallet, set the SOLANA_PRIVATE_KEY environment variable "
            "in Claude Desktop's extension settings. You can export your private key from "
            "Phantom (Settings → Security → Export Private Key) or Solflare."
        )

    return result


async def setup_wallet(private_key: str | None = None) -> dict:
    """
    Guide user through wallet setup.

    If private_key is provided, validates it and shows the address.
    If not provided, returns instructions for getting and setting up a key.

    IMPORTANT: For security, users should:
    1. Use a DEDICATED trading wallet, not their main wallet
    2. Fund it with only what they're willing to risk
    3. Never share their private key

    Args:
        private_key: Optional - the wallet's private key (base58 or JSON array)

    Returns:
        dict with configured status, address (if valid), and instructions
    """
    if private_key:
        # Validate the provided key
        try:
            import base58
            from solders.keypair import Keypair
            import json

            if private_key.startswith("["):
                # JSON array format
                key_bytes = bytes(json.loads(private_key))
                keypair = Keypair.from_bytes(key_bytes)
            else:
                # Base58 format
                key_bytes = base58.b58decode(private_key)
                keypair = Keypair.from_bytes(key_bytes)

            address = str(keypair.pubkey())

            return {
                "valid": True,
                "address": address,
                "instructions": (
                    f"Your wallet address is: {address}\n\n"
                    "To complete setup:\n"
                    "1. In Claude Desktop, go to Extensions → slopesniper → Configure\n"
                    "2. Add environment variable: SOLANA_PRIVATE_KEY = <your key>\n"
                    "3. Restart Claude Desktop\n\n"
                    "SECURITY: Only fund this wallet with amounts you're willing to risk!"
                ),
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid private key format: {e}",
                "instructions": (
                    "The private key should be either:\n"
                    "- Base58 encoded string (from Phantom/Solflare export)\n"
                    "- JSON array of bytes (from CLI wallet)\n\n"
                    "Make sure you copied the full key without extra spaces."
                ),
            }

    # No key provided - return setup guide
    current_address = get_wallet_address()
    if current_address:
        return {
            "configured": True,
            "address": current_address,
            "instructions": "Wallet is already configured! Use get_status to check balance.",
        }

    return {
        "configured": False,
        "instructions": (
            "## How to Set Up Your Trading Wallet\n\n"
            "### Step 1: Create or Export a Wallet\n\n"
            "**From Phantom:**\n"
            "1. Open Phantom → Settings (gear icon)\n"
            "2. Security & Privacy → Export Private Key\n"
            "3. Enter password and copy the key\n\n"
            "**From Solflare:**\n"
            "1. Open Solflare → Settings\n"
            "2. Export Private Key\n"
            "3. Copy the base58 string\n\n"
            "### Step 2: Configure in Claude Desktop\n\n"
            "1. Go to Extensions panel\n"
            "2. Find 'slopesniper' and click Configure\n"
            "3. Add: `SOLANA_PRIVATE_KEY = <paste your key>`\n"
            "4. Restart Claude Desktop\n\n"
            "### Security Tips\n"
            "- Use a DEDICATED wallet for trading (not your main holdings!)\n"
            "- Only fund it with amounts you're willing to lose\n"
            "- The key is stored locally on your machine\n\n"
            "Once configured, say 'check my status' to verify setup."
        ),
    }
