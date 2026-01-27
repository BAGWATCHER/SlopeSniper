"""
Configuration and Secret Management.

Handles secure retrieval of secrets with gateway -> env fallback.
Supports auto-generation and local storage of wallet keys.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import base58
from solders.keypair import Keypair


# Local wallet storage
SLOPESNIPER_DIR = Path.home() / ".slopesniper"
WALLET_FILE = SLOPESNIPER_DIR / "wallet.json"


@dataclass
class PolicyConfig:
    """Policy configuration with safe defaults."""

    MAX_SLIPPAGE_BPS: int = 100  # 1% max slippage
    MAX_TRADE_USD: float = 50.0  # $50 max per trade
    MIN_RUGCHECK_SCORE: int = 2000  # Block if score > this
    REQUIRE_MINT_DISABLED: bool = True  # Block if mint authority active
    REQUIRE_FREEZE_DISABLED: bool = True  # Block if freeze authority active
    DENY_MINTS: list[str] = field(default_factory=list)  # Blocked token mints
    ALLOW_MINTS: list[str] = field(default_factory=list)  # If set, ONLY these allowed


def _ensure_wallet_dir() -> None:
    """Create wallet directory if it doesn't exist."""
    SLOPESNIPER_DIR.mkdir(parents=True, exist_ok=True)


def generate_wallet() -> tuple[str, str]:
    """
    Generate a new Solana wallet.

    Returns:
        Tuple of (private_key_base58, public_address)
    """
    keypair = Keypair()
    private_key = base58.b58encode(bytes(keypair)).decode()
    address = str(keypair.pubkey())
    return private_key, address


def save_wallet(private_key: str, address: str) -> None:
    """Save wallet to local storage."""
    _ensure_wallet_dir()
    wallet_data = {
        "private_key": private_key,
        "address": address,
        "version": 1,
    }
    WALLET_FILE.write_text(json.dumps(wallet_data, indent=2))
    # Secure the file
    os.chmod(WALLET_FILE, 0o600)


def load_local_wallet() -> Optional[dict]:
    """
    Load wallet from local storage.

    Returns:
        dict with private_key and address, or None if not found
    """
    if not WALLET_FILE.exists():
        return None
    try:
        data = json.loads(WALLET_FILE.read_text())
        if "private_key" in data and "address" in data:
            return data
    except Exception:
        pass
    return None


def get_or_create_wallet() -> tuple[str, str, bool]:
    """
    Get existing wallet or create a new one.

    Returns:
        Tuple of (private_key, address, is_new)
        is_new is True if wallet was just generated
    """
    # Check environment variable first (override)
    env_key = os.environ.get("SOLANA_PRIVATE_KEY")
    if env_key:
        keypair = _parse_private_key(env_key)
        if keypair:
            return env_key, str(keypair.pubkey()), False

    # Check local storage
    local_wallet = load_local_wallet()
    if local_wallet:
        return local_wallet["private_key"], local_wallet["address"], False

    # Generate new wallet
    private_key, address = generate_wallet()
    save_wallet(private_key, address)
    return private_key, address, True


def _parse_private_key(private_key: str) -> Optional[Keypair]:
    """Parse private key in various formats."""
    try:
        if private_key.startswith("["):
            key_bytes = bytes(json.loads(private_key))
            return Keypair.from_bytes(key_bytes)
        else:
            key_bytes = base58.b58decode(private_key)
            return Keypair.from_bytes(key_bytes)
    except Exception:
        return None


def get_secret(name: str) -> Optional[str]:
    """
    Get a secret value with gateway -> env fallback.

    Args:
        name: Secret name (e.g., 'SOLANA_PRIVATE_KEY')

    Returns:
        Secret value or None if not found

    Priority:
    1. Clawdbot gateway secret API (if available)
    2. Environment variable
    3. None
    """
    # Try clawdbot gateway first (future integration point)
    gateway_url = os.environ.get("CLAWDBOT_GATEWAY_URL")
    if gateway_url:
        try:
            # Future: implement gateway secret fetch
            pass
        except Exception:
            pass

    # Fallback to environment variable
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    return None


def get_keypair() -> Optional[Keypair]:
    """
    Load Solana keypair from local storage or environment.

    Priority:
    1. SOLANA_PRIVATE_KEY environment variable
    2. Local wallet file (~/.slopesniper/wallet.json)
    3. None (caller should use get_or_create_wallet to generate)

    Returns:
        Keypair or None if not configured

    Raises:
        ValueError: If key format is invalid
    """
    # Check env var first
    private_key = get_secret("SOLANA_PRIVATE_KEY")
    if private_key:
        keypair = _parse_private_key(private_key)
        if keypair:
            return keypair
        raise ValueError("Invalid SOLANA_PRIVATE_KEY format")

    # Check local wallet
    local_wallet = load_local_wallet()
    if local_wallet:
        keypair = _parse_private_key(local_wallet["private_key"])
        if keypair:
            return keypair

    return None


def get_wallet_address() -> Optional[str]:
    """
    Get the wallet address from the configured keypair.

    Returns:
        Wallet address string or None if not configured
    """
    keypair = get_keypair()
    if keypair:
        return str(keypair.pubkey())
    return None


def get_rpc_url() -> str:
    """
    Get Solana RPC URL.

    Returns:
        RPC URL (defaults to mainnet-beta)
    """
    return get_secret("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"


def get_jupiter_api_key() -> Optional[str]:
    """
    Get Jupiter API key for higher rate limits.

    Returns:
        API key or None (free tier)
    """
    return get_secret("JUPITER_API_KEY")


def get_policy_config() -> PolicyConfig:
    """
    Load policy configuration from environment.

    Environment variables:
    - POLICY_MAX_SLIPPAGE_BPS: Max slippage in basis points
    - POLICY_MAX_TRADE_USD: Max trade size in USD
    - POLICY_MIN_RUGCHECK_SCORE: Max acceptable rugcheck score
    - POLICY_REQUIRE_MINT_DISABLED: Require mint authority disabled
    - POLICY_REQUIRE_FREEZE_DISABLED: Require freeze authority disabled
    - POLICY_DENY_MINTS: Comma-separated list of blocked mints
    - POLICY_ALLOW_MINTS: Comma-separated list of allowed mints (whitelist)

    Returns:
        PolicyConfig with values from env or defaults
    """
    config = PolicyConfig()

    # Parse numeric values
    if max_slippage := os.environ.get("POLICY_MAX_SLIPPAGE_BPS"):
        config.MAX_SLIPPAGE_BPS = int(max_slippage)

    if max_trade := os.environ.get("POLICY_MAX_TRADE_USD"):
        config.MAX_TRADE_USD = float(max_trade)

    if min_score := os.environ.get("POLICY_MIN_RUGCHECK_SCORE"):
        config.MIN_RUGCHECK_SCORE = int(min_score)

    # Parse boolean values
    if require_mint := os.environ.get("POLICY_REQUIRE_MINT_DISABLED"):
        config.REQUIRE_MINT_DISABLED = require_mint.lower() in ("true", "1", "yes")

    if require_freeze := os.environ.get("POLICY_REQUIRE_FREEZE_DISABLED"):
        config.REQUIRE_FREEZE_DISABLED = require_freeze.lower() in ("true", "1", "yes")

    # Parse list values
    if deny_mints := os.environ.get("POLICY_DENY_MINTS"):
        config.DENY_MINTS = [m.strip() for m in deny_mints.split(",") if m.strip()]

    if allow_mints := os.environ.get("POLICY_ALLOW_MINTS"):
        config.ALLOW_MINTS = [m.strip() for m in allow_mints.split(",") if m.strip()]

    return config
