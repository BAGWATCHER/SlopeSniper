"""
Intent Storage System.

SQLite-based storage for swap intents with automatic expiry.
Intents store the quote details and unsigned transaction for later execution.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Intent TTL in seconds (2 minutes - crypto prices move fast)
INTENT_TTL_SECONDS = 120

# Database path (in user's home directory to avoid package issues)
DB_PATH = Path.home() / ".slopesniper" / "intents.db"


@dataclass
class Intent:
    """Swap intent with all details needed for execution."""

    intent_id: str
    from_mint: str
    to_mint: str
    amount: str
    slippage_bps: int
    out_amount_est: str
    unsigned_tx: str
    request_id: str
    created_at: datetime
    expires_at: datetime
    executed: bool = False


def get_db_connection() -> sqlite3.Connection:
    """Get database connection, creating tables if needed."""
    # Ensure parent directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY,
            from_mint TEXT NOT NULL,
            to_mint TEXT NOT NULL,
            amount TEXT NOT NULL,
            slippage_bps INTEGER NOT NULL,
            out_amount_est TEXT NOT NULL,
            unsigned_tx TEXT NOT NULL,
            request_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            executed INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    return conn


def cleanup_expired() -> int:
    """
    Delete expired intents from the database.

    Returns:
        Number of intents deleted
    """
    conn = get_db_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute("DELETE FROM intents WHERE expires_at < ?", (now,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def create_intent(
    from_mint: str,
    to_mint: str,
    amount: str,
    slippage_bps: int,
    out_amount_est: str,
    unsigned_tx: str,
    request_id: str,
) -> str:
    """
    Create a new swap intent.

    Args:
        from_mint: Token to sell
        to_mint: Token to buy
        amount: Amount to swap (string, in token units)
        slippage_bps: Slippage tolerance
        out_amount_est: Estimated output amount
        unsigned_tx: Base64 encoded unsigned transaction
        request_id: Jupiter request ID for execution

    Returns:
        Intent ID (UUID string)
    """
    # Clean up expired intents first
    cleanup_expired()

    intent_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=INTENT_TTL_SECONDS)

    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO intents (
                intent_id, from_mint, to_mint, amount, slippage_bps,
                out_amount_est, unsigned_tx, request_id, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                intent_id,
                from_mint,
                to_mint,
                amount,
                slippage_bps,
                out_amount_est,
                unsigned_tx,
                request_id,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()
        return intent_id
    finally:
        conn.close()


def get_intent(intent_id: str) -> Optional[Intent]:
    """
    Get an intent by ID if it exists and is not expired.

    Args:
        intent_id: Intent UUID

    Returns:
        Intent object or None if not found/expired
    """
    # Clean up expired intents first
    cleanup_expired()

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT * FROM intents
            WHERE intent_id = ?
            AND expires_at > ?
            """,
            (intent_id, datetime.now(timezone.utc).isoformat()),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return Intent(
            intent_id=row["intent_id"],
            from_mint=row["from_mint"],
            to_mint=row["to_mint"],
            amount=row["amount"],
            slippage_bps=row["slippage_bps"],
            out_amount_est=row["out_amount_est"],
            unsigned_tx=row["unsigned_tx"],
            request_id=row["request_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            executed=bool(row["executed"]),
        )
    finally:
        conn.close()


def mark_executed(intent_id: str) -> bool:
    """
    Mark an intent as executed (prevents replay).

    Args:
        intent_id: Intent UUID

    Returns:
        True if intent was found and marked, False otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "UPDATE intents SET executed = 1 WHERE intent_id = ? AND executed = 0",
            (intent_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_intent_time_remaining(intent: Intent) -> int:
    """
    Get seconds remaining before intent expires.

    Args:
        intent: Intent object

    Returns:
        Seconds remaining (0 if expired)
    """
    now = datetime.now(timezone.utc)
    # Ensure expires_at is timezone-aware
    expires_at = intent.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    remaining = (expires_at - now).total_seconds()
    return max(0, int(remaining))


def list_pending_intents() -> list[Intent]:
    """
    List all non-expired, non-executed intents.

    Returns:
        List of Intent objects
    """
    cleanup_expired()

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            SELECT * FROM intents
            WHERE expires_at > ?
            AND executed = 0
            ORDER BY created_at DESC
            """,
            (datetime.now(timezone.utc).isoformat(),),
        )
        rows = cursor.fetchall()

        return [
            Intent(
                intent_id=row["intent_id"],
                from_mint=row["from_mint"],
                to_mint=row["to_mint"],
                amount=row["amount"],
                slippage_bps=row["slippage_bps"],
                out_amount_est=row["out_amount_est"],
                unsigned_tx=row["unsigned_tx"],
                request_id=row["request_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                expires_at=datetime.fromisoformat(row["expires_at"]),
                executed=bool(row["executed"]),
            )
            for row in rows
        ]
    finally:
        conn.close()
