"""
Trading Strategies - Presets and user preferences.

Manage trading style, limits, and auto-execution thresholds.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


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

    # Trade history for PnL tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT NOT NULL,
            mint TEXT NOT NULL,
            symbol TEXT,
            amount_tokens REAL NOT NULL,
            amount_usd REAL NOT NULL,
            price_per_token REAL NOT NULL,
            signature TEXT,
            notes TEXT
        )
    """)

    # PnL snapshots for baseline tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pnl_snapshots (
            id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sol_balance REAL,
            sol_value_usd REAL,
            total_value_usd REAL,
            trigger TEXT DEFAULT 'manual'
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
        presets.append(
            {
                "name": name,
                "description": strategy.description,
                "max_trade_usd": strategy.max_trade_usd,
                "auto_execute_under_usd": strategy.auto_execute_under_usd,
                "slippage_bps": strategy.slippage_bps,
                "require_rugcheck": strategy.require_rugcheck,
                "is_active": name == active.name,
            }
        )

    return {
        "active_strategy": active.name,
        "presets": presets,
    }


# =============================================================================
# TRADE HISTORY & PnL TRACKING
# =============================================================================


def record_trade(
    action: str,
    mint: str,
    symbol: str,
    amount_tokens: float,
    amount_usd: float,
    price_per_token: float,
    signature: str | None = None,
    notes: str | None = None,
) -> None:
    """
    Record a trade for PnL tracking.

    Args:
        action: "buy" or "sell"
        mint: Token mint address
        symbol: Token symbol
        amount_tokens: Number of tokens traded
        amount_usd: USD value of trade
        price_per_token: Price per token at trade time
        signature: Transaction signature
        notes: Optional notes
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO trade_history
        (action, mint, symbol, amount_tokens, amount_usd, price_per_token, signature, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (action, mint, symbol, amount_tokens, amount_usd, price_per_token, signature, notes),
    )

    conn.commit()
    conn.close()


def get_trade_history(mint: str | None = None, limit: int = 50) -> list[dict]:
    """
    Get trade history, optionally filtered by token.

    Args:
        mint: Filter by token mint (optional)
        limit: Maximum records to return

    Returns:
        List of trade records
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if mint:
        cursor.execute(
            """
            SELECT timestamp, action, mint, symbol, amount_tokens, amount_usd,
                   price_per_token, signature, notes
            FROM trade_history WHERE mint = ?
            ORDER BY timestamp DESC LIMIT ?
            """,
            (mint, limit),
        )
    else:
        cursor.execute(
            """
            SELECT timestamp, action, mint, symbol, amount_tokens, amount_usd,
                   price_per_token, signature, notes
            FROM trade_history
            ORDER BY timestamp DESC LIMIT ?
            """,
            (limit,),
        )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "timestamp": row[0],
            "action": row[1],
            "mint": row[2],
            "symbol": row[3],
            "amount_tokens": row[4],
            "amount_usd": row[5],
            "price_per_token": row[6],
            "signature": row[7],
            "notes": row[8],
        }
        for row in rows
    ]


def calculate_pnl_for_token(mint: str, current_price: float) -> dict:
    """
    Calculate PnL for a specific token.

    Args:
        mint: Token mint address
        current_price: Current price per token

    Returns:
        PnL breakdown for this token
    """
    trades = get_trade_history(mint=mint)

    if not trades:
        return {"error": "No trade history for this token"}

    total_bought_tokens = 0.0
    total_bought_usd = 0.0
    total_sold_tokens = 0.0
    total_sold_usd = 0.0

    for trade in trades:
        if trade["action"] == "buy":
            total_bought_tokens += trade["amount_tokens"]
            total_bought_usd += trade["amount_usd"]
        elif trade["action"] == "sell":
            total_sold_tokens += trade["amount_tokens"]
            total_sold_usd += trade["amount_usd"]

    # Current holdings
    holdings = total_bought_tokens - total_sold_tokens
    holdings_value = holdings * current_price

    # Cost basis (average cost of remaining tokens)
    if total_bought_tokens > 0:
        avg_buy_price = total_bought_usd / total_bought_tokens
    else:
        avg_buy_price = 0

    cost_basis = holdings * avg_buy_price

    # Realized PnL (from sells)
    if total_sold_tokens > 0:
        realized_pnl = total_sold_usd - (total_sold_tokens * avg_buy_price)
    else:
        realized_pnl = 0

    # Unrealized PnL (current holdings vs cost basis)
    unrealized_pnl = holdings_value - cost_basis

    # Total PnL
    total_pnl = realized_pnl + unrealized_pnl

    return {
        "mint": mint,
        "symbol": trades[0]["symbol"] if trades else None,
        "total_bought_tokens": total_bought_tokens,
        "total_bought_usd": total_bought_usd,
        "total_sold_tokens": total_sold_tokens,
        "total_sold_usd": total_sold_usd,
        "current_holdings": holdings,
        "current_price": current_price,
        "holdings_value_usd": holdings_value,
        "avg_buy_price": avg_buy_price,
        "cost_basis": cost_basis,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_pnl / total_bought_usd * 100) if total_bought_usd > 0 else 0,
        "trade_count": len(trades),
    }


async def get_portfolio_pnl() -> dict:
    """
    Calculate PnL for entire portfolio.

    Returns:
        Portfolio-wide PnL summary with per-token breakdown
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get unique tokens traded
    cursor.execute("SELECT DISTINCT mint, symbol FROM trade_history")
    tokens = cursor.fetchall()
    conn.close()

    if not tokens:
        return {
            "error": "No trade history found",
            "message": "Start trading to track your PnL!",
        }

    # Import here to avoid circular import
    from .solana_tools import solana_get_price

    token_pnls = []
    total_invested = 0.0
    total_realized = 0.0
    total_unrealized = 0.0

    for mint, _symbol in tokens:
        # Get current price
        price_data = await solana_get_price(mint)
        current_price = price_data.get("price_usd", 0) if isinstance(price_data, dict) else 0

        pnl = calculate_pnl_for_token(mint, current_price)
        if "error" not in pnl:
            token_pnls.append(pnl)
            total_invested += pnl["total_bought_usd"]
            total_realized += pnl["realized_pnl"]
            total_unrealized += pnl["unrealized_pnl"]

    total_pnl = total_realized + total_unrealized

    return {
        "total_invested": total_invested,
        "total_realized_pnl": total_realized,
        "total_unrealized_pnl": total_unrealized,
        "total_pnl": total_pnl,
        "total_pnl_pct": (total_pnl / total_invested * 100) if total_invested > 0 else 0,
        "tokens_traded": len(token_pnls),
        "token_breakdown": token_pnls,
    }


# ============================================================================
# PnL Enhancement Functions (Issue #25)
# ============================================================================


async def pnl_init(starting_value: float | None = None) -> dict:
    """
    Initialize PnL tracking with current portfolio value as baseline.

    Args:
        starting_value: Optional manual starting value in USD.
                       If not provided, uses current wallet balance.

    Returns:
        Snapshot record with baseline set
    """
    _init_db()

    if starting_value is None:
        # Get current wallet value
        from .solana_tools import solana_get_wallet

        wallet = await solana_get_wallet()
        if "error" in wallet:
            return {"error": "Could not fetch wallet balance", "details": wallet}

        sol_balance = wallet.get("sol_balance", 0)
        sol_value = wallet.get("sol_value_usd", 0)
        token_value = sum(t.get("value_usd", 0) for t in wallet.get("tokens", []))
        total_value = sol_value + token_value
    else:
        sol_balance = 0
        sol_value = 0
        total_value = starting_value

    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO pnl_snapshots (sol_balance, sol_value_usd, total_value_usd, trigger)
        VALUES (?, ?, ?, 'init')
        """,
        (sol_balance, sol_value, total_value),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Baseline set: ${total_value:.2f}",
        "snapshot": {
            "sol_balance": sol_balance,
            "sol_value_usd": sol_value,
            "total_value_usd": total_value,
            "trigger": "init",
        },
    }


def get_pnl_baseline() -> dict | None:
    """Get the earliest (init) snapshot as baseline."""
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT timestamp, sol_balance, sol_value_usd, total_value_usd, trigger
        FROM pnl_snapshots
        WHERE trigger = 'init'
        ORDER BY timestamp ASC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "timestamp": row[0],
        "sol_balance": row[1],
        "sol_value_usd": row[2],
        "total_value_usd": row[3],
        "trigger": row[4],
    }


async def pnl_with_baseline() -> dict:
    """
    Get PnL compared to baseline snapshot.

    Returns:
        Portfolio PnL with baseline comparison
    """
    baseline = get_pnl_baseline()
    current_pnl = await get_portfolio_pnl()

    if "error" in current_pnl:
        return current_pnl

    # Get current wallet value
    from .solana_tools import solana_get_wallet

    wallet = await solana_get_wallet()
    sol_value = wallet.get("sol_value_usd", 0) if "error" not in wallet else 0
    token_value = sum(t.get("value_usd", 0) for t in wallet.get("tokens", []))
    current_total = sol_value + token_value

    result = {
        "current_value_usd": current_total,
        **current_pnl,
    }

    if baseline:
        baseline_value = baseline["total_value_usd"]
        pnl_vs_baseline = current_total - baseline_value
        pnl_vs_baseline_pct = (pnl_vs_baseline / baseline_value * 100) if baseline_value > 0 else 0

        result["baseline"] = {
            "value_usd": baseline_value,
            "timestamp": baseline["timestamp"],
        }
        result["pnl_vs_baseline"] = pnl_vs_baseline
        result["pnl_vs_baseline_pct"] = pnl_vs_baseline_pct

    return result


def pnl_stats() -> dict:
    """
    Calculate trading statistics: win rate, avg gain/loss, etc.

    Returns:
        Trading statistics summary
    """
    trades = get_trade_history(limit=1000)  # Get all trades

    if not trades:
        return {"error": "No trade history", "message": "Complete some trades to see stats"}

    # Group trades by token to calculate per-position results
    token_trades: dict = {}
    for trade in trades:
        mint = trade["mint"]
        if mint not in token_trades:
            token_trades[mint] = {"buys": [], "sells": [], "symbol": trade.get("symbol")}
        if trade["action"] == "buy":
            token_trades[mint]["buys"].append(trade)
        else:
            token_trades[mint]["sells"].append(trade)

    # Calculate closed position results
    closed_positions = []
    for mint, data in token_trades.items():
        if data["sells"]:  # Only count if there are sells
            total_bought = sum(t["amount_usd"] for t in data["buys"])
            total_sold = sum(t["amount_usd"] for t in data["sells"])
            if total_bought > 0:
                pnl = total_sold - total_bought
                pnl_pct = (pnl / total_bought) * 100
                closed_positions.append({
                    "symbol": data["symbol"],
                    "mint": mint,
                    "invested": total_bought,
                    "returned": total_sold,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "is_win": pnl > 0,
                })

    if not closed_positions:
        return {
            "message": "No closed positions yet",
            "total_trades": len(trades),
            "buys": sum(1 for t in trades if t["action"] == "buy"),
            "sells": sum(1 for t in trades if t["action"] == "sell"),
        }

    wins = [p for p in closed_positions if p["is_win"]]
    losses = [p for p in closed_positions if not p["is_win"]]

    win_rate = (len(wins) / len(closed_positions)) * 100 if closed_positions else 0
    avg_gain = sum(p["pnl_pct"] for p in wins) / len(wins) if wins else 0
    avg_loss = sum(p["pnl_pct"] for p in losses) / len(losses) if losses else 0

    largest_win = max(wins, key=lambda x: x["pnl"]) if wins else None
    largest_loss = min(losses, key=lambda x: x["pnl"]) if losses else None

    return {
        "total_trades": len(trades),
        "closed_positions": len(closed_positions),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(win_rate, 2),
        "avg_gain_pct": round(avg_gain, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "largest_win": {
            "symbol": largest_win["symbol"],
            "pnl": round(largest_win["pnl"], 2),
            "pnl_pct": round(largest_win["pnl_pct"], 2),
        } if largest_win else None,
        "largest_loss": {
            "symbol": largest_loss["symbol"],
            "pnl": round(largest_loss["pnl"], 2),
            "pnl_pct": round(largest_loss["pnl_pct"], 2),
        } if largest_loss else None,
        "total_realized_pnl": round(sum(p["pnl"] for p in closed_positions), 2),
    }


async def pnl_positions() -> dict:
    """
    Get detailed view of all positions (open and closed).

    Returns:
        Position-level breakdown with PnL
    """
    trades = get_trade_history(limit=1000)

    if not trades:
        return {"error": "No trade history", "positions": []}

    # Group by token
    token_data: dict = {}
    for trade in trades:
        mint = trade["mint"]
        if mint not in token_data:
            token_data[mint] = {
                "symbol": trade.get("symbol"),
                "buys": [],
                "sells": [],
                "first_trade": trade["timestamp"],
            }
        if trade["action"] == "buy":
            token_data[mint]["buys"].append(trade)
        else:
            token_data[mint]["sells"].append(trade)

    from .solana_tools import solana_get_price

    positions = []
    for mint, data in token_data.items():
        total_bought_tokens = sum(t["amount_tokens"] for t in data["buys"])
        total_bought_usd = sum(t["amount_usd"] for t in data["buys"])
        total_sold_tokens = sum(t["amount_tokens"] for t in data["sells"])
        total_sold_usd = sum(t["amount_usd"] for t in data["sells"])

        holdings = total_bought_tokens - total_sold_tokens
        avg_buy_price = total_bought_usd / total_bought_tokens if total_bought_tokens > 0 else 0

        # Get current price
        price_data = await solana_get_price(mint)
        current_price = price_data.get("price_usd", 0) if isinstance(price_data, dict) else 0

        holdings_value = holdings * current_price
        cost_basis = holdings * avg_buy_price

        # Calculate PnL
        realized_pnl = total_sold_usd - (total_sold_tokens * avg_buy_price) if total_sold_tokens > 0 else 0
        unrealized_pnl = holdings_value - cost_basis
        total_pnl = realized_pnl + unrealized_pnl

        status = "closed" if holdings <= 0 else "open"

        positions.append({
            "symbol": data["symbol"],
            "mint": mint,
            "status": status,
            "current_holdings": holdings,
            "current_price": current_price,
            "holdings_value_usd": round(holdings_value, 2),
            "total_invested": round(total_bought_usd, 2),
            "avg_buy_price": avg_buy_price,
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / total_bought_usd) * 100, 2) if total_bought_usd > 0 else 0,
            "first_trade": data["first_trade"],
            "trade_count": len(data["buys"]) + len(data["sells"]),
        })

    # Sort by status (open first) then by PnL
    positions.sort(key=lambda x: (x["status"] == "closed", -x["total_pnl"]))

    open_positions = [p for p in positions if p["status"] == "open"]
    closed_positions = [p for p in positions if p["status"] == "closed"]

    return {
        "open_count": len(open_positions),
        "closed_count": len(closed_positions),
        "positions": positions,
    }


def pnl_export(format_type: str = "json") -> dict:
    """
    Export trade history and PnL data.

    Args:
        format_type: "json" or "csv"

    Returns:
        Export data or file path
    """
    trades = get_trade_history(limit=10000)

    if not trades:
        return {"error": "No trade history to export"}

    if format_type == "csv":
        import csv
        import io
        from datetime import datetime

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "timestamp", "action", "symbol", "mint", "amount_tokens",
            "amount_usd", "price_per_token", "signature", "notes"
        ])

        for trade in trades:
            writer.writerow([
                trade["timestamp"],
                trade["action"],
                trade["symbol"],
                trade["mint"],
                trade["amount_tokens"],
                trade["amount_usd"],
                trade["price_per_token"],
                trade["signature"] or "",
                trade["notes"] or "",
            ])

        csv_content = output.getvalue()

        # Save to file
        export_dir = Path.home() / ".slopesniper" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = export_dir / filename

        with open(filepath, "w") as f:
            f.write(csv_content)

        return {
            "success": True,
            "format": "csv",
            "file": str(filepath),
            "trade_count": len(trades),
        }

    else:  # JSON format
        from datetime import datetime

        export_dir = Path.home() / ".slopesniper" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = export_dir / filename

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "trade_count": len(trades),
            "trades": trades,
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        return {
            "success": True,
            "format": "json",
            "file": str(filepath),
            "trade_count": len(trades),
        }


def pnl_reset() -> dict:
    """
    Reset PnL baseline by clearing init snapshots.

    Returns:
        Confirmation of reset
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pnl_snapshots WHERE trigger = 'init'")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "PnL baseline reset",
        "snapshots_deleted": deleted,
    }
