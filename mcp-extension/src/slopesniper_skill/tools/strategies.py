"""
Trading Strategies - Presets and user preferences.

Manage trading style, limits, and auto-execution thresholds.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal


@dataclass
class TradingStrategy:
    """A trading strategy with limits and preferences."""

    name: str
    description: str
    max_trade_usd: float  # Maximum USD per trade
    auto_execute_under_usd: float  # Auto-trade without asking if under this
    max_loss_pct: float  # Stop-loss percentage (for future use)
    slippage_bps: int  # Slippage tolerance in basis points
    require_rugcheck: bool  # Run safety check before trading
    allowed_tokens: list[str] = field(default_factory=list)  # Whitelist (empty = all)


# Preset strategies
STRATEGY_PRESETS: dict[str, TradingStrategy] = {
    "conservative": TradingStrategy(
        name="conservative",
        description="Safe trading with low limits. Best for beginners.",
        max_trade_usd=25.0,
        auto_execute_under_usd=10.0,
        max_loss_pct=5.0,
        slippage_bps=50,
        require_rugcheck=True,
        allowed_tokens=[],
    ),
    "balanced": TradingStrategy(
        name="balanced",
        description="Moderate limits with safety checks. Good for most traders.",
        max_trade_usd=100.0,
        auto_execute_under_usd=25.0,
        max_loss_pct=10.0,
        slippage_bps=100,
        require_rugcheck=True,
        allowed_tokens=[],
    ),
    "aggressive": TradingStrategy(
        name="aggressive",
        description="Higher limits, faster execution. For experienced traders.",
        max_trade_usd=500.0,
        auto_execute_under_usd=50.0,
        max_loss_pct=25.0,
        slippage_bps=200,
        require_rugcheck=False,
        allowed_tokens=[],
    ),
    "degen": TradingStrategy(
        name="degen",
        description="Maximum risk tolerance. YOLO mode. You've been warned.",
        max_trade_usd=1000.0,
        auto_execute_under_usd=100.0,
        max_loss_pct=50.0,
        slippage_bps=500,
        require_rugcheck=False,
        allowed_tokens=[],
    ),
}

# Default strategy
DEFAULT_STRATEGY = "balanced"


def _get_config_db_path() -> Path:
    """Get path to config database."""
    config_dir = Path.home() / ".slopesniper"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.db"


def _init_db():
    """Initialize the config database."""
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            max_trade_usd REAL NOT NULL,
            auto_execute_under_usd REAL NOT NULL,
            max_loss_pct REAL NOT NULL,
            slippage_bps INTEGER NOT NULL,
            require_rugcheck INTEGER NOT NULL,
            allowed_tokens TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            mint TEXT NOT NULL UNIQUE,
            symbol TEXT,
            alert_condition TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def _save_strategy(strategy: TradingStrategy, is_active: bool = True):
    """Save strategy to database."""
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # If setting as active, deactivate others first
    if is_active:
        cursor.execute("UPDATE strategies SET is_active = 0")

    # Check if strategy exists
    cursor.execute("SELECT id FROM strategies WHERE name = ?", (strategy.name,))
    existing = cursor.fetchone()

    allowed_tokens_json = json.dumps(strategy.allowed_tokens)

    if existing:
        cursor.execute(
            """
            UPDATE strategies SET
                description = ?, max_trade_usd = ?, auto_execute_under_usd = ?,
                max_loss_pct = ?, slippage_bps = ?, require_rugcheck = ?,
                allowed_tokens = ?, is_active = ?
            WHERE name = ?
            """,
            (
                strategy.description,
                strategy.max_trade_usd,
                strategy.auto_execute_under_usd,
                strategy.max_loss_pct,
                strategy.slippage_bps,
                1 if strategy.require_rugcheck else 0,
                allowed_tokens_json,
                1 if is_active else 0,
                strategy.name,
            ),
        )
    else:
        cursor.execute(
            """
            INSERT INTO strategies (
                name, description, max_trade_usd, auto_execute_under_usd,
                max_loss_pct, slippage_bps, require_rugcheck, allowed_tokens, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                strategy.name,
                strategy.description,
                strategy.max_trade_usd,
                strategy.auto_execute_under_usd,
                strategy.max_loss_pct,
                strategy.slippage_bps,
                1 if strategy.require_rugcheck else 0,
                allowed_tokens_json,
                1 if is_active else 0,
            ),
        )

    conn.commit()
    conn.close()


def _load_active_strategy() -> TradingStrategy | None:
    """Load active strategy from database."""
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name, description, max_trade_usd, auto_execute_under_usd,
               max_loss_pct, slippage_bps, require_rugcheck, allowed_tokens
        FROM strategies WHERE is_active = 1
        """
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return TradingStrategy(
            name=row[0],
            description=row[1] or "",
            max_trade_usd=row[2],
            auto_execute_under_usd=row[3],
            max_loss_pct=row[4],
            slippage_bps=row[5],
            require_rugcheck=bool(row[6]),
            allowed_tokens=json.loads(row[7]) if row[7] else [],
        )
    return None


def get_active_strategy() -> TradingStrategy:
    """Get the currently active trading strategy."""
    saved = _load_active_strategy()
    if saved:
        return saved
    return STRATEGY_PRESETS[DEFAULT_STRATEGY]


async def set_strategy(
    strategy: str | None = None,
    max_trade_usd: float | None = None,
    auto_execute_under_usd: float | None = None,
    max_loss_pct: float | None = None,
    slippage_bps: int | None = None,
    require_rugcheck: bool | None = None,
) -> dict:
    """
    Set the trading strategy.

    Use a preset name OR customize individual parameters.
    If both preset and params provided, params override the preset values.

    Preset strategies:
    - "conservative": $25 max, $10 auto, 0.5% slippage, rugcheck ON
    - "balanced": $100 max, $25 auto, 1% slippage, rugcheck ON
    - "aggressive": $500 max, $50 auto, 2% slippage, rugcheck OFF
    - "degen": $1000 max, $100 auto, 5% slippage, rugcheck OFF

    Args:
        strategy: Preset name ("conservative", "balanced", "aggressive", "degen")
        max_trade_usd: Override max trade size
        auto_execute_under_usd: Override auto-execution threshold
        max_loss_pct: Override stop-loss percentage
        slippage_bps: Override slippage tolerance
        require_rugcheck: Override safety check requirement

    Returns:
        The active strategy configuration
    """
    # Start with preset or current strategy
    if strategy and strategy in STRATEGY_PRESETS:
        base = STRATEGY_PRESETS[strategy]
        new_strategy = TradingStrategy(
            name=base.name,
            description=base.description,
            max_trade_usd=base.max_trade_usd,
            auto_execute_under_usd=base.auto_execute_under_usd,
            max_loss_pct=base.max_loss_pct,
            slippage_bps=base.slippage_bps,
            require_rugcheck=base.require_rugcheck,
            allowed_tokens=base.allowed_tokens.copy(),
        )
    else:
        current = get_active_strategy()
        new_strategy = TradingStrategy(
            name="custom",
            description="Custom strategy",
            max_trade_usd=current.max_trade_usd,
            auto_execute_under_usd=current.auto_execute_under_usd,
            max_loss_pct=current.max_loss_pct,
            slippage_bps=current.slippage_bps,
            require_rugcheck=current.require_rugcheck,
            allowed_tokens=current.allowed_tokens.copy(),
        )

    # Apply overrides
    if max_trade_usd is not None:
        new_strategy.max_trade_usd = max_trade_usd
        new_strategy.name = "custom"
    if auto_execute_under_usd is not None:
        new_strategy.auto_execute_under_usd = auto_execute_under_usd
        new_strategy.name = "custom"
    if max_loss_pct is not None:
        new_strategy.max_loss_pct = max_loss_pct
        new_strategy.name = "custom"
    if slippage_bps is not None:
        new_strategy.slippage_bps = slippage_bps
        new_strategy.name = "custom"
    if require_rugcheck is not None:
        new_strategy.require_rugcheck = require_rugcheck
        new_strategy.name = "custom"

    # Validate
    if new_strategy.auto_execute_under_usd > new_strategy.max_trade_usd:
        new_strategy.auto_execute_under_usd = new_strategy.max_trade_usd

    # Save
    _save_strategy(new_strategy, is_active=True)

    return {
        "success": True,
        "strategy": {
            "name": new_strategy.name,
            "description": new_strategy.description,
            "max_trade_usd": new_strategy.max_trade_usd,
            "auto_execute_under_usd": new_strategy.auto_execute_under_usd,
            "max_loss_pct": new_strategy.max_loss_pct,
            "slippage_bps": new_strategy.slippage_bps,
            "require_rugcheck": new_strategy.require_rugcheck,
        },
        "explanation": (
            f"Strategy set to '{new_strategy.name}'. "
            f"Trades up to ${new_strategy.max_trade_usd} allowed. "
            f"Auto-execute enabled for trades under ${new_strategy.auto_execute_under_usd}."
        ),
    }


async def get_strategy() -> dict:
    """
    Get the current trading strategy and limits.

    Returns the active strategy with all settings.
    """
    strategy = get_active_strategy()

    return {
        "name": strategy.name,
        "description": strategy.description,
        "max_trade_usd": strategy.max_trade_usd,
        "auto_execute_under_usd": strategy.auto_execute_under_usd,
        "max_loss_pct": strategy.max_loss_pct,
        "slippage_bps": strategy.slippage_bps,
        "slippage_pct": strategy.slippage_bps / 100,
        "require_rugcheck": strategy.require_rugcheck,
        "allowed_tokens": strategy.allowed_tokens,
        "presets_available": list(STRATEGY_PRESETS.keys()),
    }


async def list_strategies() -> dict:
    """
    List all available strategy presets.

    Returns preset strategies with their configurations.
    """
    active = get_active_strategy()

    presets = []
    for name, strategy in STRATEGY_PRESETS.items():
        presets.append({
            "name": name,
            "description": strategy.description,
            "max_trade_usd": strategy.max_trade_usd,
            "auto_execute_under_usd": strategy.auto_execute_under_usd,
            "slippage_bps": strategy.slippage_bps,
            "require_rugcheck": strategy.require_rugcheck,
            "is_active": name == active.name,
        })

    return {
        "active_strategy": active.name,
        "presets": presets,
    }
