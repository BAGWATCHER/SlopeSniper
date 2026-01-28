"""
Auto-sell Targets - Price/mcap target management and execution.

Provides functionality to set sell targets that automatically execute
when conditions are met (market cap, price, percentage gain, trailing stop).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .config import SLOPESNIPER_DIR, get_jupiter_api_key
from .strategies import _get_config_db_path


class TargetType(Enum):
    """Types of sell targets."""

    MCAP = "mcap"
    PRICE = "price"
    PCT_GAIN = "pct_gain"
    TRAILING_STOP = "trailing_stop"


class TargetStatus(Enum):
    """Status of a sell target."""

    PENDING = "pending"
    TRIGGERED = "triggered"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


@dataclass
class SellTarget:
    """A sell target with all execution details."""

    id: int
    mint: str
    symbol: str | None
    target_type: TargetType
    target_value: float
    sell_amount: str  # 'all', '50%', 'USD:100'
    status: TargetStatus
    entry_price: float | None
    entry_mcap: float | None
    peak_value: float | None
    trigger_price: float | None
    trigger_time: datetime | None
    execution_signature: str | None
    created_at: datetime
    notes: str | None


def _init_targets_db() -> None:
    """Initialize targets table in config.db."""
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mint TEXT NOT NULL,
            symbol TEXT,
            target_type TEXT NOT NULL,
            target_value REAL NOT NULL,
            sell_amount TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            entry_price REAL,
            entry_mcap REAL,
            peak_value REAL,
            trigger_price REAL,
            trigger_time TIMESTAMP,
            execution_signature TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def _row_to_target(row: sqlite3.Row | tuple) -> SellTarget:
    """Convert a database row to a SellTarget object."""
    # Handle both Row objects and tuples
    if hasattr(row, "keys"):
        # sqlite3.Row
        data = dict(row)
    else:
        # Tuple from fetchall
        keys = [
            "id",
            "mint",
            "symbol",
            "target_type",
            "target_value",
            "sell_amount",
            "status",
            "entry_price",
            "entry_mcap",
            "peak_value",
            "trigger_price",
            "trigger_time",
            "execution_signature",
            "created_at",
            "updated_at",
            "notes",
        ]
        data = dict(zip(keys, row))

    # Parse trigger_time and created_at
    trigger_time = None
    if data.get("trigger_time"):
        try:
            trigger_time = datetime.fromisoformat(data["trigger_time"])
        except (ValueError, TypeError):
            pass

    created_at = datetime.now(timezone.utc)
    if data.get("created_at"):
        try:
            created_at = datetime.fromisoformat(data["created_at"])
        except (ValueError, TypeError):
            pass

    return SellTarget(
        id=data["id"],
        mint=data["mint"],
        symbol=data.get("symbol"),
        target_type=TargetType(data["target_type"]),
        target_value=data["target_value"],
        sell_amount=data["sell_amount"],
        status=TargetStatus(data["status"]),
        entry_price=data.get("entry_price"),
        entry_mcap=data.get("entry_mcap"),
        peak_value=data.get("peak_value"),
        trigger_price=data.get("trigger_price"),
        trigger_time=trigger_time,
        execution_signature=data.get("execution_signature"),
        created_at=created_at,
        notes=data.get("notes"),
    )


async def add_target(
    mint: str,
    target_type: str,
    target_value: float,
    sell_amount: str = "all",
    symbol: str | None = None,
    entry_price: float | None = None,
    entry_mcap: float | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Add a new sell target.

    Args:
        mint: Token mint address
        target_type: One of 'mcap', 'price', 'pct_gain', 'trailing_stop'
        target_value: Target value (market cap, price, percentage, or trail %)
        sell_amount: Amount to sell - 'all', '50%', 'USD:100', etc.
        symbol: Token symbol (optional, will be resolved if not provided)
        entry_price: Current price when target is created (for pct_gain)
        entry_mcap: Current market cap when target is created
        notes: Optional notes

    Returns:
        Dict with success status and target details
    """
    _init_targets_db()

    # Validate target type
    try:
        tt = TargetType(target_type.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid target type: {target_type}",
            "valid_types": [t.value for t in TargetType],
        }

    # Validate sell amount format
    sell_amount = sell_amount.strip().lower()
    if not _validate_sell_amount(sell_amount):
        return {
            "success": False,
            "error": f"Invalid sell amount: {sell_amount}",
            "valid_formats": ["all", "50%", "USD:100", "100"],
        }

    # If symbol not provided, try to resolve it
    if not symbol:
        try:
            from ..sdk import JupiterDataClient

            client = JupiterDataClient(api_key=get_jupiter_api_key())
            info = await client.get_token_info(mint)
            symbol = info.get("symbol", "???")

            # Also get current price/mcap if not provided
            if entry_price is None:
                entry_price = info.get("price")
            if entry_mcap is None:
                entry_mcap = info.get("mcap")
        except Exception:
            symbol = None

    # For trailing stop, set peak_value to entry_price
    peak_value = entry_price if tt == TargetType.TRAILING_STOP else None

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO targets (
            mint, symbol, target_type, target_value, sell_amount,
            status, entry_price, entry_mcap, peak_value, notes
        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """,
        (
            mint,
            symbol,
            tt.value,
            target_value,
            sell_amount,
            entry_price,
            entry_mcap,
            peak_value,
            notes,
        ),
    )

    target_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Build human-readable description
    type_desc = {
        "mcap": f"market cap >= ${target_value:,.0f}",
        "price": f"price >= ${target_value:.8g}",
        "pct_gain": f"{target_value:.1f}% gain",
        "trailing_stop": f"{target_value:.1f}% drop from peak",
    }

    return {
        "success": True,
        "target_id": target_id,
        "mint": mint,
        "symbol": symbol,
        "target_type": tt.value,
        "target_value": target_value,
        "sell_amount": sell_amount,
        "condition": type_desc.get(tt.value, str(target_value)),
        "entry_price": entry_price,
        "entry_mcap": entry_mcap,
        "message": f"Target #{target_id} created: Sell {sell_amount} of {symbol or mint} when {type_desc.get(tt.value)}",
    }


def _validate_sell_amount(sell_amount: str) -> bool:
    """Validate sell amount format."""
    sell_amount = sell_amount.strip().lower()

    if sell_amount == "all":
        return True

    if sell_amount.endswith("%"):
        try:
            pct = float(sell_amount[:-1])
            return 0 < pct <= 100
        except ValueError:
            return False

    if sell_amount.startswith("usd:"):
        try:
            val = float(sell_amount[4:])
            return val > 0
        except ValueError:
            return False

    # Plain number treated as percentage
    try:
        pct = float(sell_amount)
        return 0 < pct <= 100
    except ValueError:
        return False


def get_target(target_id: int) -> SellTarget | None:
    """Get a target by ID."""
    _init_targets_db()

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM targets WHERE id = ?", (target_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return _row_to_target(row)


def get_active_targets() -> list[SellTarget]:
    """Get all pending targets."""
    _init_targets_db()

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM targets WHERE status = 'pending' ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [_row_to_target(row) for row in rows]


def get_all_targets(include_executed: bool = False) -> list[SellTarget]:
    """Get all targets, optionally including executed ones."""
    _init_targets_db()

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if include_executed:
        cursor.execute("SELECT * FROM targets ORDER BY created_at DESC")
    else:
        cursor.execute(
            "SELECT * FROM targets WHERE status != 'executed' ORDER BY created_at DESC"
        )

    rows = cursor.fetchall()
    conn.close()

    return [_row_to_target(row) for row in rows]


def remove_target(target_id: int) -> dict[str, Any]:
    """Remove/cancel a target."""
    _init_targets_db()

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if target exists
    cursor.execute("SELECT id, symbol, mint FROM targets WHERE id = ?", (target_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return {"success": False, "error": f"Target #{target_id} not found"}

    # Mark as cancelled (don't delete, keep for history)
    cursor.execute(
        "UPDATE targets SET status = 'cancelled', updated_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), target_id),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "target_id": target_id,
        "symbol": row[1],
        "message": f"Target #{target_id} cancelled",
    }


def delete_target(target_id: int) -> dict[str, Any]:
    """Permanently delete a target."""
    _init_targets_db()

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM targets WHERE id = ?", (target_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    if deleted:
        return {"success": True, "message": f"Target #{target_id} deleted"}
    return {"success": False, "error": f"Target #{target_id} not found"}


def mark_target_triggered(target_id: int, trigger_price: float) -> None:
    """Mark a target as triggered (condition met)."""
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE targets SET
            status = 'triggered',
            trigger_price = ?,
            trigger_time = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            trigger_price,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            target_id,
        ),
    )

    conn.commit()
    conn.close()


def mark_target_executed(target_id: int, signature: str | None = None) -> None:
    """Mark a target as executed (sell completed)."""
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE targets SET
            status = 'executed',
            execution_signature = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            signature,
            datetime.now(timezone.utc).isoformat(),
            target_id,
        ),
    )

    conn.commit()
    conn.close()


def update_trailing_peak(target_id: int, current_price: float) -> None:
    """Update peak value for trailing stop if current price is higher."""
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE targets SET
            peak_value = MAX(COALESCE(peak_value, 0), ?),
            updated_at = ?
        WHERE id = ? AND target_type = 'trailing_stop'
        """,
        (
            current_price,
            datetime.now(timezone.utc).isoformat(),
            target_id,
        ),
    )

    conn.commit()
    conn.close()


def check_target(
    target: SellTarget,
    current_price: float,
    current_mcap: float | None = None,
) -> bool:
    """
    Check if a target condition is met.

    Args:
        target: The target to check
        current_price: Current token price in USD
        current_mcap: Current market cap (optional)

    Returns:
        True if target condition is met
    """
    if target.status != TargetStatus.PENDING:
        return False

    if target.target_type == TargetType.MCAP:
        return current_mcap is not None and current_mcap >= target.target_value

    elif target.target_type == TargetType.PRICE:
        return current_price >= target.target_value

    elif target.target_type == TargetType.PCT_GAIN:
        if target.entry_price is None or target.entry_price <= 0:
            return False
        pct_change = ((current_price - target.entry_price) / target.entry_price) * 100
        return pct_change >= target.target_value

    elif target.target_type == TargetType.TRAILING_STOP:
        # Trailing stop: sell if price drops X% from peak
        if target.peak_value is None or target.peak_value <= 0:
            return False
        drop_pct = ((target.peak_value - current_price) / target.peak_value) * 100
        return drop_pct >= target.target_value

    return False


def parse_sell_amount(
    sell_amount: str,
    holdings_value_usd: float,
    token_amount: float,
) -> float:
    """
    Parse sell_amount string and return token amount to sell.

    Args:
        sell_amount: 'all', '50%', 'USD:100', etc.
        holdings_value_usd: Current USD value of holdings
        token_amount: Current token balance

    Returns:
        Token amount to sell
    """
    sell_amount = sell_amount.strip().lower()

    if sell_amount == "all" or sell_amount == "100%":
        return token_amount

    if sell_amount.endswith("%"):
        pct = float(sell_amount[:-1]) / 100
        return token_amount * pct

    if sell_amount.startswith("usd:"):
        usd_amount = float(sell_amount[4:])
        price_per_token = holdings_value_usd / token_amount if token_amount > 0 else 0
        if price_per_token > 0:
            return min(usd_amount / price_per_token, token_amount)
        return 0

    # Default: treat as percentage
    try:
        pct = float(sell_amount) / 100
        return token_amount * pct
    except ValueError:
        return token_amount  # Fallback to all


async def execute_target_sell(
    target: SellTarget,
    current_price: float,
) -> dict[str, Any]:
    """
    Execute sell for a triggered target.

    Args:
        target: The target that was triggered
        current_price: Current price at trigger time

    Returns:
        Execution result with success status
    """
    from . import quick_trade, solana_get_wallet

    # Get current holdings
    wallet = await solana_get_wallet()
    tokens = wallet.get("tokens", [])

    # Find the token in holdings
    holdings = None
    for token in tokens:
        if token.get("mint") == target.mint:
            holdings = token
            break

    if not holdings:
        return {
            "success": False,
            "error": f"Token {target.symbol or target.mint} not found in wallet",
        }

    token_amount = holdings.get("amount", 0)
    holdings_value_usd = holdings.get("value_usd", 0)

    if token_amount <= 0:
        return {
            "success": False,
            "error": f"No {target.symbol or target.mint} holdings to sell",
        }

    # Calculate amount to sell
    sell_tokens = parse_sell_amount(target.sell_amount, holdings_value_usd, token_amount)

    if sell_tokens <= 0:
        return {
            "success": False,
            "error": "Calculated sell amount is zero",
        }

    # Execute the sell via quick_trade
    # quick_trade accepts "all" or USD amount, so we need to handle this
    if target.sell_amount.lower() == "all":
        result = await quick_trade("sell", target.mint, "all")
    else:
        # Calculate USD value to sell
        sell_usd = sell_tokens * current_price
        result = await quick_trade("sell", target.mint, sell_usd)

    # Update target status
    if result.get("success") or result.get("auto_executed"):
        mark_target_executed(target.id, result.get("signature"))
    else:
        # Mark as triggered but not executed (for retry or manual intervention)
        mark_target_triggered(target.id, current_price)

    return {
        **result,
        "target_id": target.id,
        "target_type": target.target_type.value,
        "target_value": target.target_value,
        "sell_amount": target.sell_amount,
        "tokens_sold": sell_tokens if result.get("success") else 0,
    }


async def poll_targets_batch(
    targets: list[SellTarget],
) -> dict[str, dict[str, Any]]:
    """
    Fetch prices for multiple targets efficiently.

    Args:
        targets: List of active targets to check

    Returns:
        Dict mapping mint -> {price_usd, mcap}
    """
    if not targets:
        return {}

    from ..sdk import JupiterDataClient

    # Dedupe mints
    mints = list(set(t.mint for t in targets))

    client = JupiterDataClient(api_key=get_jupiter_api_key())
    results: dict[str, dict[str, Any]] = {}

    # Jupiter supports batch price fetch
    try:
        prices = await client.get_prices(mints)

        for mint in mints:
            price_data = prices.get(mint, {})
            results[mint] = {
                "price_usd": price_data.get("usdPrice", 0),
                "mcap": None,  # Will be fetched separately if needed
            }
    except Exception:
        # Initialize with zeros
        for mint in mints:
            results[mint] = {"price_usd": 0, "mcap": None}

    # Get token info for mcap (only for mcap targets)
    mcap_mints = set(t.mint for t in targets if t.target_type == TargetType.MCAP)

    for mint in mcap_mints:
        try:
            info = await client.get_token_info(mint)
            if info and mint in results:
                results[mint]["mcap"] = info.get("mcap")
        except Exception:
            pass

    return results


def format_target_for_display(target: SellTarget) -> dict[str, Any]:
    """Format a target for CLI display."""
    type_desc = {
        "mcap": f"mcap >= ${target.target_value:,.0f}",
        "price": f"price >= ${target.target_value:.8g}",
        "pct_gain": f"+{target.target_value:.1f}%",
        "trailing_stop": f"-{target.target_value:.1f}% from peak",
    }

    result = {
        "id": target.id,
        "symbol": target.symbol or target.mint[:8],
        "mint": target.mint,
        "type": target.target_type.value,
        "condition": type_desc.get(target.target_type.value, str(target.target_value)),
        "sell": target.sell_amount,
        "status": target.status.value,
        "created": target.created_at.strftime("%Y-%m-%d %H:%M") if target.created_at else None,
    }

    if target.entry_price:
        result["entry_price"] = f"${target.entry_price:.8g}"

    if target.peak_value and target.target_type == TargetType.TRAILING_STOP:
        result["peak"] = f"${target.peak_value:.8g}"

    if target.trigger_price:
        result["triggered_at"] = f"${target.trigger_price:.8g}"

    if target.execution_signature:
        result["signature"] = target.execution_signature

    return result
