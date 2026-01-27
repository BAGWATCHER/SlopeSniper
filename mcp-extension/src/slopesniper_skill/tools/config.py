"""
Configuration and Secret Management.

Handles secure retrieval of secrets with gateway -> env fallback.
Supports auto-generation and encrypted local storage of wallet keys.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import base58
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from solders.keypair import Keypair


# Local storage paths
SLOPESNIPER_DIR = Path.home() / ".slopesniper"
WALLET_FILE = SLOPESNIPER_DIR / "wallet.json"
WALLET_FILE_ENCRYPTED = SLOPESNIPER_DIR / "wallet.enc"
MACHINE_KEY_FILE = SLOPESNIPER_DIR / ".machine_key"
USER_CONFIG_FILE = SLOPESNIPER_DIR / "config.enc"


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
    # Set restrictive permissions on the directory
    os.chmod(SLOPESNIPER_DIR, 0o700)


def _get_machine_id() -> str:
    """
    Get a machine-specific identifier for encryption key derivation.

    Combines multiple sources to create a stable machine fingerprint.
    """
    components = []

    # Platform info
    components.append(platform.node())
    components.append(platform.machine())
    components.append(platform.system())

    # Try to get hardware UUID (macOS)
    try:
        import subprocess
        result = subprocess.run(
            ["ioreg", "-d2", "-c", "IOPlatformExpertDevice"],
            capture_output=True, text=True, timeout=5
        )
        if "IOPlatformUUID" in result.stdout:
            for line in result.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    uuid_part = line.split('"')[-2]
                    components.append(uuid_part)
                    break
    except Exception:
        pass

    # Try to get machine-id (Linux)
    try:
        machine_id_path = Path("/etc/machine-id")
        if machine_id_path.exists():
            components.append(machine_id_path.read_text().strip())
    except Exception:
        pass

    # Combine all components
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()


def _get_or_create_machine_key() -> bytes:
    """
    Get or create a machine-specific encryption key.

    The key is derived from:
    1. Machine-specific identifier (hardware/OS fingerprint)
    2. A random salt stored locally

    This ensures:
    - Wallet files are encrypted at rest
    - Wallet files are tied to this machine
    - Key survives updates (salt is persistent)
    """
    _ensure_wallet_dir()

    # Load or generate salt
    if MACHINE_KEY_FILE.exists():
        try:
            key_data = json.loads(MACHINE_KEY_FILE.read_text())
            salt = bytes.fromhex(key_data["salt"])
        except Exception:
            # Corrupted key file, regenerate
            salt = secrets.token_bytes(32)
            key_data = {"salt": salt.hex(), "version": 1}
            MACHINE_KEY_FILE.write_text(json.dumps(key_data))
            os.chmod(MACHINE_KEY_FILE, 0o600)
    else:
        salt = secrets.token_bytes(32)
        key_data = {"salt": salt.hex(), "version": 1}
        MACHINE_KEY_FILE.write_text(json.dumps(key_data))
        os.chmod(MACHINE_KEY_FILE, 0o600)

    # Derive key from machine ID + salt
    machine_id = _get_machine_id()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    key = kdf.derive(machine_id.encode())

    # Fernet requires URL-safe base64 encoded key
    import base64
    return base64.urlsafe_b64encode(key)


def _encrypt_data(data: str) -> bytes:
    """Encrypt data using machine-specific key."""
    key = _get_or_create_machine_key()
    f = Fernet(key)
    return f.encrypt(data.encode())


def _decrypt_data(encrypted: bytes) -> str:
    """Decrypt data using machine-specific key."""
    key = _get_or_create_machine_key()
    f = Fernet(key)
    return f.decrypt(encrypted).decode()


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
    """
    Save wallet to encrypted local storage.

    The wallet is encrypted with a machine-specific key,
    meaning it can only be decrypted on this machine.
    """
    _ensure_wallet_dir()

    wallet_data = {
        "private_key": private_key,
        "address": address,
        "version": 2,  # v2 = encrypted
    }

    # Encrypt the wallet data
    encrypted = _encrypt_data(json.dumps(wallet_data))

    # Save encrypted wallet
    WALLET_FILE_ENCRYPTED.write_bytes(encrypted)
    os.chmod(WALLET_FILE_ENCRYPTED, 0o600)

    # Remove old plaintext wallet if it exists
    if WALLET_FILE.exists():
        WALLET_FILE.unlink()


def _migrate_plaintext_wallet() -> Optional[dict]:
    """
    Migrate old plaintext wallet to encrypted format.

    Returns the wallet data if migration was successful.
    """
    if not WALLET_FILE.exists():
        return None

    try:
        data = json.loads(WALLET_FILE.read_text())
        if "private_key" in data and "address" in data:
            # Migrate to encrypted format
            save_wallet(data["private_key"], data["address"])
            return data
    except Exception:
        pass

    return None


def load_local_wallet() -> Optional[dict]:
    """
    Load wallet from encrypted local storage.

    Returns:
        dict with private_key and address, or None if not found
    """
    # Check for encrypted wallet first
    if WALLET_FILE_ENCRYPTED.exists():
        try:
            encrypted = WALLET_FILE_ENCRYPTED.read_bytes()
            decrypted = _decrypt_data(encrypted)
            data = json.loads(decrypted)
            if "private_key" in data and "address" in data:
                return data
        except InvalidToken:
            # Key mismatch - wallet from different machine or corrupted
            return None
        except Exception:
            pass

    # Try to migrate old plaintext wallet
    migrated = _migrate_plaintext_wallet()
    if migrated:
        return migrated

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


def save_user_config(config: dict) -> None:
    """
    Save user configuration (encrypted).

    Args:
        config: Dict with user settings (e.g., jupiter_api_key, rpc_url)
    """
    _ensure_wallet_dir()

    # Merge with existing config
    existing = load_user_config() or {}
    existing.update(config)

    encrypted = _encrypt_data(json.dumps(existing))
    USER_CONFIG_FILE.write_bytes(encrypted)
    os.chmod(USER_CONFIG_FILE, 0o600)


def load_user_config() -> Optional[dict]:
    """
    Load user configuration (encrypted).

    Returns:
        Dict with user settings or None if not found
    """
    if not USER_CONFIG_FILE.exists():
        return None

    try:
        encrypted = USER_CONFIG_FILE.read_bytes()
        decrypted = _decrypt_data(encrypted)
        return json.loads(decrypted)
    except Exception:
        return None


def set_jupiter_api_key(api_key: str) -> dict:
    """
    Save user's Jupiter API key for improved performance.

    Args:
        api_key: Jupiter Ultra API key

    Returns:
        Status dict
    """
    if not api_key or len(api_key) < 10:
        return {"success": False, "error": "Invalid API key format"}

    save_user_config({"jupiter_api_key": api_key})

    return {
        "success": True,
        "message": "Jupiter API key saved (encrypted)",
        "benefits": [
            "Higher rate limits",
            "Faster quote responses",
            "Priority routing",
        ],
    }


def get_jupiter_api_key() -> Optional[str]:
    """
    Get Jupiter API key with priority: env var > local config > None.

    Priority:
    1. JUPITER_API_KEY environment variable
    2. User's saved config (~/.slopesniper/config.enc)
    3. None (will use bundled key from GitHub)

    Returns:
        API key or None
    """
    # Check env var first
    env_key = get_secret("JUPITER_API_KEY")
    if env_key:
        return env_key

    # Check user's saved config
    config = load_user_config()
    if config and config.get("jupiter_api_key"):
        return config["jupiter_api_key"]

    return None


def get_config_status() -> dict:
    """
    Get current configuration status.

    Returns:
        Dict with config status and recommendations
    """
    config = load_user_config() or {}
    env_key = os.environ.get("JUPITER_API_KEY")

    has_custom_key = bool(env_key or config.get("jupiter_api_key"))
    key_source = None
    if env_key:
        key_source = "environment"
    elif config.get("jupiter_api_key"):
        key_source = "local_config"

    result = {
        "jupiter_api_key": {
            "configured": has_custom_key,
            "source": key_source,
        },
        "rpc_url": get_rpc_url(),
        "wallet_configured": WALLET_FILE_ENCRYPTED.exists(),
        "config_dir": str(SLOPESNIPER_DIR),
    }

    if not has_custom_key:
        result["recommendation"] = {
            "message": "Using shared API key. For better performance, set your own Jupiter API key.",
            "benefits": [
                "10x higher rate limits",
                "Faster quote responses",
                "Priority transaction routing",
            ],
            "how_to": "Run: slopesniper config --set-jupiter-key YOUR_KEY",
            "get_key": "Get a free key at: https://station.jup.ag/docs/apis/ultra-api",
        }

    return result


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
