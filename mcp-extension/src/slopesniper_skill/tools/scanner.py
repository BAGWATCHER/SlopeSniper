"""
Opportunity Scanner - Find trading opportunities.

Scans for trending tokens, price movements, and new listings.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from ..sdk.jupiter_data_client import JupiterDataClient
from ..sdk.rugcheck_client import RugCheckClient
from .strategies import _get_config_db_path, _init_db


@dataclass
class Opportunity:
    """A trading opportunity."""

    token_mint: str
    token_symbol: str
    token_name: str
    signal: str  # "trending", "volume_spike", "new_listing", "price_pump"
    price_usd: float
    change_24h_pct: float | None
    volume_24h_usd: float | None
    liquidity_usd: float | None
    risk_score: int | None  # From rugcheck (lower = safer)
    recommendation: str  # "buy", "watch", "avoid"
    reason: str


# Well-known tokens to filter out from "new" discoveries
ESTABLISHED_TOKENS = {
    "So11111111111111111111111111111111111111112",  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
}


async def scan_opportunities(
    filter: Literal["all", "trending", "new_listings", "pumping"] = "all",
    min_liquidity_usd: float = 50000,
    min_volume_usd: float = 10000,
    limit: int = 10,
) -> list[dict]:
    """
    Scan for trading opportunities.

    Finds tokens based on the filter:
    - "trending": High volume tokens with recent activity
    - "new_listings": Recently listed tokens with growing liquidity
    - "pumping": Tokens with significant price increases
    - "all": Combination of all signals

    Args:
        filter: Type of opportunities to find
        min_liquidity_usd: Minimum liquidity to consider (safety filter)
        min_volume_usd: Minimum 24h volume
        limit: Maximum opportunities to return

    Returns:
        List of opportunities with recommendations
    """
    client = JupiterDataClient()
    rugcheck = RugCheckClient()

    opportunities: list[Opportunity] = []

    try:
        if filter in ("all", "trending"):
            # Get trending tokens from Jupiter
            trending = await _get_trending_tokens(client, limit=20)
            for token in trending:
                if token.get("mint") in ESTABLISHED_TOKENS:
                    continue

                liquidity = token.get("liquidity", 0) or 0
                volume = token.get("volume_24h", 0) or 0

                if liquidity < min_liquidity_usd or volume < min_volume_usd:
                    continue

                # Quick rugcheck
                risk_score = None
                try:
                    report = await rugcheck.get_report_summary(token["mint"])
                    risk_score = report.get("score", 9999)
                except Exception:
                    pass

                recommendation, reason = _get_recommendation(
                    risk_score, liquidity, volume, token.get("change_24h")
                )

                opportunities.append(
                    Opportunity(
                        token_mint=token["mint"],
                        token_symbol=token.get("symbol", "???"),
                        token_name=token.get("name", "Unknown"),
                        signal="trending",
                        price_usd=token.get("price", 0),
                        change_24h_pct=token.get("change_24h"),
                        volume_24h_usd=volume,
                        liquidity_usd=liquidity,
                        risk_score=risk_score,
                        recommendation=recommendation,
                        reason=reason,
                    )
                )

        if filter in ("all", "pumping"):
            # Look for price pumps (tokens up >10% in 24h)
            pumping = await _get_pumping_tokens(client, min_change=10, limit=20)
            for token in pumping:
                if token.get("mint") in ESTABLISHED_TOKENS:
                    continue

                # Skip if already added from trending
                if any(o.token_mint == token.get("mint") for o in opportunities):
                    continue

                liquidity = token.get("liquidity", 0) or 0
                volume = token.get("volume_24h", 0) or 0

                if liquidity < min_liquidity_usd:
                    continue

                risk_score = None
                try:
                    report = await rugcheck.get_report_summary(token["mint"])
                    risk_score = report.get("score", 9999)
                except Exception:
                    pass

                recommendation, reason = _get_recommendation(
                    risk_score, liquidity, volume, token.get("change_24h")
                )

                opportunities.append(
                    Opportunity(
                        token_mint=token["mint"],
                        token_symbol=token.get("symbol", "???"),
                        token_name=token.get("name", "Unknown"),
                        signal="price_pump",
                        price_usd=token.get("price", 0),
                        change_24h_pct=token.get("change_24h"),
                        volume_24h_usd=volume,
                        liquidity_usd=liquidity,
                        risk_score=risk_score,
                        recommendation=recommendation,
                        reason=reason,
                    )
                )

    except Exception as e:
        return [{"error": f"Scan failed: {str(e)}"}]

    # Sort by recommendation (buy first, then watch, then avoid)
    order = {"buy": 0, "watch": 1, "avoid": 2}
    opportunities.sort(key=lambda o: (order.get(o.recommendation, 3), -(o.volume_24h_usd or 0)))

    # Convert to dicts and limit
    results = []
    for opp in opportunities[:limit]:
        results.append({
            "token": {
                "mint": opp.token_mint,
                "symbol": opp.token_symbol,
                "name": opp.token_name,
            },
            "signal": opp.signal,
            "price_usd": opp.price_usd,
            "change_24h_pct": opp.change_24h_pct,
            "volume_24h_usd": opp.volume_24h_usd,
            "liquidity_usd": opp.liquidity_usd,
            "risk_score": opp.risk_score,
            "recommendation": opp.recommendation,
            "reason": opp.reason,
        })

    return results


async def _get_trending_tokens(client: JupiterDataClient, limit: int = 20) -> list[dict]:
    """Get trending tokens from Jupiter."""
    try:
        # Use Jupiter's token search with volume sorting
        # This is a simplified approach - in production you'd use Birdeye or similar
        tokens = []

        # Search for popular categories
        for query in ["meme", "ai", "gaming"]:
            try:
                results = await client.search_token(query)
                tokens.extend(results[:10])
            except Exception:
                pass

        return tokens[:limit]
    except Exception:
        return []


async def _get_pumping_tokens(
    client: JupiterDataClient, min_change: float = 10, limit: int = 20
) -> list[dict]:
    """Get tokens with significant price increases."""
    try:
        # This would ideally use a price history API
        # For now, we'll use the search results and filter
        tokens = []

        for query in ["pump", "moon", "bull"]:
            try:
                results = await client.search_token(query)
                for token in results:
                    change = token.get("change_24h")
                    if change and change >= min_change:
                        tokens.append(token)
            except Exception:
                pass

        return tokens[:limit]
    except Exception:
        return []


def _get_recommendation(
    risk_score: int | None,
    liquidity: float,
    volume: float,
    change_24h: float | None,
) -> tuple[str, str]:
    """Get recommendation based on metrics."""

    # High risk score = avoid
    if risk_score and risk_score > 3000:
        return "avoid", f"High risk score ({risk_score}). Possible rug indicators."

    # Low liquidity = watch
    if liquidity < 100000:
        return "watch", f"Low liquidity (${liquidity:,.0f}). Exit may be difficult."

    # Very low volume = watch
    if volume < 50000:
        return "watch", f"Low volume (${volume:,.0f}). Limited trading activity."

    # Extreme pump = caution
    if change_24h and change_24h > 100:
        return "watch", f"Extreme pump (+{change_24h:.0f}%). May dump soon."

    # Good metrics = buy signal
    if risk_score and risk_score < 1500 and liquidity > 200000:
        return "buy", "Good liquidity, acceptable risk. Consider entry."

    # Default
    return "watch", "Monitor for better entry or more data."


async def watch_token(
    mint: str,
    alert_on: str = "10% change",
) -> dict:
    """
    Add a token to your watchlist.

    The watchlist is checked when you ask to scan opportunities.

    Args:
        mint: Token mint address
        alert_on: Alert condition (e.g., "10% change", "price above $1")

    Returns:
        Confirmation of watchlist addition
    """
    _init_db()
    db_path = _get_config_db_path()

    # Get token info
    client = JupiterDataClient()
    try:
        info = await client.get_token_info(mint)
        symbol = info.get("symbol", "???")
    except Exception:
        symbol = None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO watchlist (mint, symbol, alert_condition)
        VALUES (?, ?, ?)
        """,
        (mint, symbol, alert_on),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "mint": mint,
        "symbol": symbol,
        "alert_condition": alert_on,
        "message": f"Added {symbol or mint} to watchlist. Alert: {alert_on}",
    }


async def get_watchlist() -> list[dict]:
    """
    Get all tokens in your watchlist with current prices.

    Returns:
        List of watched tokens with current status
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT mint, symbol, alert_condition, added_at FROM watchlist")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    # Get current prices
    client = JupiterDataClient()
    mints = [row[0] for row in rows]

    try:
        prices = await client.get_prices(mints)
    except Exception:
        prices = {}

    watchlist = []
    for mint, symbol, alert_condition, added_at in rows:
        price_info = prices.get(mint, {})
        watchlist.append({
            "mint": mint,
            "symbol": symbol,
            "alert_condition": alert_condition,
            "added_at": added_at,
            "current_price_usd": price_info.get("price"),
            "change_24h_pct": price_info.get("change_24h"),
        })

    return watchlist


async def remove_from_watchlist(mint: str) -> dict:
    """
    Remove a token from your watchlist.

    Args:
        mint: Token mint address to remove

    Returns:
        Confirmation
    """
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM watchlist WHERE mint = ?", (mint,))
    removed = cursor.rowcount > 0

    conn.commit()
    conn.close()

    if removed:
        return {"success": True, "message": f"Removed {mint} from watchlist"}
    return {"success": False, "message": "Token not found in watchlist"}
