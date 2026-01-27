"""
Opportunity Scanner - Find trading opportunities.

Multi-source scanner using:
- DexScreener: Trending pairs, new listings, volume data
- Pump.fun: Graduated tokens, new launches
- Jupiter: Price data and token search
- Rugcheck: Safety analysis
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from ..sdk.jupiter_data_client import JupiterDataClient
from ..sdk.rugcheck_client import RugCheckClient
from ..sdk.dexscreener_client import DexScreenerClient
from ..sdk.pumpfun_client import PumpFunClient
from .config import get_jupiter_api_key
from .strategies import _get_config_db_path, _init_db


@dataclass
class TokenOpportunity:
    """A trading opportunity with full details."""

    mint: str
    symbol: str
    name: str
    source: str  # "dexscreener", "pumpfun", "jupiter"
    signal: str  # "graduated", "trending", "new_pair", "volume_spike", "price_pump"

    # Price data
    price_usd: float
    price_change_5m: Optional[float] = None
    price_change_1h: Optional[float] = None
    price_change_24h: Optional[float] = None

    # Volume & Liquidity
    volume_24h_usd: Optional[float] = None
    liquidity_usd: Optional[float] = None

    # Age & Activity
    age: Optional[str] = None
    buys_24h: Optional[int] = None
    sells_24h: Optional[int] = None

    # Safety
    risk_score: Optional[int] = None
    is_safe: Optional[bool] = None

    # Metadata
    dex: Optional[str] = None
    pair_address: Optional[str] = None
    url: Optional[str] = None
    boosted: bool = False

    # Recommendation
    recommendation: str = "watch"
    reason: str = ""


# Well-known tokens to filter out
ESTABLISHED_TOKENS = {
    "So11111111111111111111111111111111111111112",  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
    "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",  # POPCAT
}


async def scan_opportunities(
    filter: Literal["all", "trending", "new", "graduated", "pumping"] = "all",
    min_liquidity_usd: float = 10000,
    min_volume_usd: float = 5000,
    limit: int = 15,
) -> list[dict]:
    """
    Scan for trading opportunities across multiple sources.

    Filters:
    - "trending": Hot tokens with high volume and activity
    - "new": Recently launched pairs (last 24h)
    - "graduated": Pump.fun tokens that completed bonding curve
    - "pumping": Tokens with >10% price increase
    - "all": Combination of all signals

    Args:
        filter: Type of opportunities to find
        min_liquidity_usd: Minimum liquidity (safety filter)
        min_volume_usd: Minimum 24h volume
        limit: Maximum results

    Returns:
        List of opportunities with recommendations
    """
    dex = DexScreenerClient()
    pump = PumpFunClient()
    rugcheck = RugCheckClient()

    opportunities: list[TokenOpportunity] = []
    seen_mints: set[str] = set()

    try:
        # Run scans in parallel based on filter
        tasks = []

        if filter in ("all", "trending"):
            tasks.append(_scan_trending(dex, seen_mints, min_liquidity_usd))

        if filter in ("all", "new"):
            tasks.append(_scan_new_pairs(dex, seen_mints, min_liquidity_usd))

        if filter in ("all", "graduated"):
            tasks.append(_scan_graduated(pump, dex, seen_mints, min_liquidity_usd))

        if filter in ("all", "pumping"):
            tasks.append(_scan_pumping(dex, seen_mints, min_liquidity_usd))

        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                opportunities.extend(result)

        # Filter by volume
        opportunities = [
            o for o in opportunities
            if (o.volume_24h_usd or 0) >= min_volume_usd
        ]

        # Add safety scores (batch for efficiency)
        await _add_safety_scores(opportunities[:20], rugcheck)

        # Generate recommendations
        for opp in opportunities:
            opp.recommendation, opp.reason = _get_recommendation(opp)

        # Sort: buy > watch > avoid, then by volume
        order = {"buy": 0, "watch": 1, "avoid": 2}
        opportunities.sort(
            key=lambda o: (order.get(o.recommendation, 3), -(o.volume_24h_usd or 0))
        )

    except Exception as e:
        return [{"error": f"Scan failed: {str(e)}"}]

    # Convert to dicts
    return [_format_opportunity(o) for o in opportunities[:limit]]


async def scan_pumpfun(
    filter: Literal["graduated", "new", "trending"] = "graduated",
    limit: int = 20,
) -> list[dict]:
    """
    Scan Pump.fun specifically.

    Args:
        filter: "graduated" (migrated to Raydium), "new" (fresh launches), "trending"
        limit: Max results

    Returns:
        List of Pump.fun tokens
    """
    pump = PumpFunClient()

    try:
        if filter == "graduated":
            tokens = await pump.get_graduated_tokens(limit=limit)
        elif filter == "new":
            tokens = await pump.get_latest_tokens(limit=limit)
        else:
            tokens = await pump.get_trending(limit=limit)

        results = []
        for token in tokens[:limit]:
            summary = pump.format_token_summary(token)
            results.append(summary)

        return results

    except Exception as e:
        return [{"error": f"Pump.fun scan failed: {str(e)}"}]


async def scan_new_pairs(
    max_age_hours: int = 6,
    min_liquidity_usd: float = 10000,
    limit: int = 20,
) -> list[dict]:
    """
    Scan for newly created trading pairs.

    Args:
        max_age_hours: Maximum pair age in hours
        min_liquidity_usd: Minimum liquidity
        limit: Max results

    Returns:
        List of new pairs with details
    """
    dex = DexScreenerClient()

    try:
        pairs = await dex.get_new_pairs(
            min_liquidity_usd=min_liquidity_usd,
            max_age_hours=max_age_hours,
            limit=limit
        )

        results = []
        for pair in pairs:
            summary = dex.format_pair_summary(pair)
            results.append(summary)

        return results

    except Exception as e:
        return [{"error": f"New pairs scan failed: {str(e)}"}]


async def get_token_details(mint_or_symbol: str) -> dict:
    """
    Get comprehensive details for a token.

    Combines data from DexScreener, Jupiter, and Rugcheck.

    Args:
        mint_or_symbol: Token mint address or symbol

    Returns:
        Full token details including price, volume, safety
    """
    dex = DexScreenerClient()
    jupiter = JupiterDataClient(api_key=get_jupiter_api_key())
    rugcheck = RugCheckClient()

    # Resolve symbol to mint if needed
    mint = mint_or_symbol
    if len(mint_or_symbol) < 32:
        try:
            results = await jupiter.search_token(mint_or_symbol)
            if results:
                mint = results[0].get("mint", mint_or_symbol)
        except Exception:
            pass

    result = {
        "mint": mint,
        "symbol": None,
        "name": None,
        "dexscreener": None,
        "safety": None,
        "jupiter": None,
    }

    # Get DexScreener data
    try:
        pairs = await dex.get_token_pairs(mint)
        if pairs:
            best_pair = pairs[0]
            result["dexscreener"] = dex.format_pair_summary(best_pair)
            result["symbol"] = result["dexscreener"]["symbol"]
            result["name"] = result["dexscreener"]["name"]
    except Exception:
        pass

    # Get safety data
    try:
        report = await rugcheck.get_report_summary(mint)
        result["safety"] = {
            "score": report.get("score"),
            "risks": report.get("risks", [])[:3],
            "is_safe": report.get("score", 9999) < 2000,
        }
    except Exception:
        pass

    # Get Jupiter data
    try:
        info = await jupiter.get_token_info(mint)
        result["jupiter"] = {
            "symbol": info.get("symbol"),
            "name": info.get("name"),
            "price_usd": info.get("price"),
            "market_cap": info.get("market_cap"),
        }
        if not result["symbol"]:
            result["symbol"] = info.get("symbol")
            result["name"] = info.get("name")
    except Exception:
        pass

    return result


# ============================================================================
# Internal scan functions
# ============================================================================


async def _scan_trending(
    dex: DexScreenerClient,
    seen: set[str],
    min_liquidity: float
) -> list[TokenOpportunity]:
    """Scan trending tokens from DexScreener."""
    opportunities = []

    try:
        trending = await dex.get_trending(limit=20)

        for pair in trending:
            summary = dex.format_pair_summary(pair)
            mint = summary.get("mint")

            if not mint or mint in seen or mint in ESTABLISHED_TOKENS:
                continue

            liquidity = summary.get("liquidity_usd", 0)
            if liquidity < min_liquidity:
                continue

            seen.add(mint)
            opportunities.append(TokenOpportunity(
                mint=mint,
                symbol=summary.get("symbol", "???"),
                name=summary.get("name", "Unknown"),
                source="dexscreener",
                signal="trending",
                price_usd=summary.get("price_usd", 0),
                price_change_5m=summary.get("price_change_5m"),
                price_change_1h=summary.get("price_change_1h"),
                price_change_24h=summary.get("price_change_24h"),
                volume_24h_usd=summary.get("volume_24h"),
                liquidity_usd=liquidity,
                age=summary.get("age"),
                buys_24h=summary.get("buys_24h"),
                sells_24h=summary.get("sells_24h"),
                dex=summary.get("dex"),
                pair_address=summary.get("pair_address"),
                url=summary.get("url"),
                boosted=summary.get("boosted", False),
            ))

    except Exception:
        pass

    return opportunities


async def _scan_new_pairs(
    dex: DexScreenerClient,
    seen: set[str],
    min_liquidity: float
) -> list[TokenOpportunity]:
    """Scan new pairs from DexScreener."""
    opportunities = []

    try:
        pairs = await dex.get_new_pairs(
            min_liquidity_usd=min_liquidity,
            max_age_hours=24,
            limit=20
        )

        for pair in pairs:
            summary = dex.format_pair_summary(pair)
            mint = summary.get("mint")

            if not mint or mint in seen or mint in ESTABLISHED_TOKENS:
                continue

            seen.add(mint)
            opportunities.append(TokenOpportunity(
                mint=mint,
                symbol=summary.get("symbol", "???"),
                name=summary.get("name", "Unknown"),
                source="dexscreener",
                signal="new_pair",
                price_usd=summary.get("price_usd", 0),
                price_change_5m=summary.get("price_change_5m"),
                price_change_1h=summary.get("price_change_1h"),
                price_change_24h=summary.get("price_change_24h"),
                volume_24h_usd=summary.get("volume_24h"),
                liquidity_usd=summary.get("liquidity_usd"),
                age=summary.get("age"),
                buys_24h=summary.get("buys_24h"),
                sells_24h=summary.get("sells_24h"),
                dex=summary.get("dex"),
                pair_address=summary.get("pair_address"),
                url=summary.get("url"),
            ))

    except Exception:
        pass

    return opportunities


async def _scan_graduated(
    pump: PumpFunClient,
    dex: DexScreenerClient,
    seen: set[str],
    min_liquidity: float
) -> list[TokenOpportunity]:
    """Scan graduated tokens from Pump.fun."""
    opportunities = []

    try:
        graduated = await pump.get_graduated_tokens(limit=30)

        for token in graduated:
            summary = pump.format_token_summary(token)
            mint = summary.get("mint")

            if not mint or mint in seen or mint in ESTABLISHED_TOKENS:
                continue

            if not summary.get("is_graduated"):
                continue

            # Get DexScreener data for price/volume
            try:
                pairs = await dex.get_token_pairs(mint)
                if pairs:
                    pair_summary = dex.format_pair_summary(pairs[0])
                    liquidity = pair_summary.get("liquidity_usd", 0)

                    if liquidity < min_liquidity:
                        continue

                    seen.add(mint)
                    opportunities.append(TokenOpportunity(
                        mint=mint,
                        symbol=summary.get("symbol", "???"),
                        name=summary.get("name", "Unknown"),
                        source="pumpfun",
                        signal="graduated",
                        price_usd=pair_summary.get("price_usd", 0),
                        price_change_5m=pair_summary.get("price_change_5m"),
                        price_change_1h=pair_summary.get("price_change_1h"),
                        price_change_24h=pair_summary.get("price_change_24h"),
                        volume_24h_usd=pair_summary.get("volume_24h"),
                        liquidity_usd=liquidity,
                        age=summary.get("age"),
                        buys_24h=pair_summary.get("buys_24h"),
                        sells_24h=pair_summary.get("sells_24h"),
                        dex=pair_summary.get("dex"),
                        url=pair_summary.get("url"),
                    ))
            except Exception:
                continue

            await asyncio.sleep(0.1)  # Rate limiting

    except Exception:
        pass

    return opportunities


async def _scan_pumping(
    dex: DexScreenerClient,
    seen: set[str],
    min_liquidity: float
) -> list[TokenOpportunity]:
    """Scan tokens with significant price increases."""
    opportunities = []

    try:
        # Search for pump-related terms
        for query in ["pump", "moon", "100x"]:
            pairs = await dex.search_pairs(query)

            for pair in pairs[:10]:
                summary = dex.format_pair_summary(pair)
                mint = summary.get("mint")

                if not mint or mint in seen or mint in ESTABLISHED_TOKENS:
                    continue

                # Check for significant price increase
                change_1h = summary.get("price_change_1h", 0)
                change_24h = summary.get("price_change_24h", 0)

                if change_1h < 10 and change_24h < 20:
                    continue

                liquidity = summary.get("liquidity_usd", 0)
                if liquidity < min_liquidity:
                    continue

                seen.add(mint)
                opportunities.append(TokenOpportunity(
                    mint=mint,
                    symbol=summary.get("symbol", "???"),
                    name=summary.get("name", "Unknown"),
                    source="dexscreener",
                    signal="price_pump",
                    price_usd=summary.get("price_usd", 0),
                    price_change_5m=summary.get("price_change_5m"),
                    price_change_1h=change_1h,
                    price_change_24h=change_24h,
                    volume_24h_usd=summary.get("volume_24h"),
                    liquidity_usd=liquidity,
                    age=summary.get("age"),
                    buys_24h=summary.get("buys_24h"),
                    sells_24h=summary.get("sells_24h"),
                    dex=summary.get("dex"),
                    url=summary.get("url"),
                ))

            await asyncio.sleep(0.2)

    except Exception:
        pass

    return opportunities


async def _add_safety_scores(
    opportunities: list[TokenOpportunity],
    rugcheck: RugCheckClient
) -> None:
    """Add safety scores to opportunities."""
    for opp in opportunities[:10]:  # Limit to avoid rate limits
        try:
            report = await rugcheck.get_report_summary(opp.mint)
            opp.risk_score = report.get("score")
            opp.is_safe = (opp.risk_score or 9999) < 2000
            await asyncio.sleep(0.1)
        except Exception:
            pass


def _get_recommendation(opp: TokenOpportunity) -> tuple[str, str]:
    """Generate recommendation based on metrics."""

    # High risk score = avoid
    if opp.risk_score and opp.risk_score > 3000:
        return "avoid", f"High risk score ({opp.risk_score}). Possible rug."

    # Very low liquidity = avoid
    if (opp.liquidity_usd or 0) < 20000:
        return "avoid", f"Low liquidity (${opp.liquidity_usd:,.0f}). Exit difficult."

    # Extreme pump = caution
    if (opp.price_change_1h or 0) > 50:
        return "watch", f"Pumping +{opp.price_change_1h:.0f}% 1h. May dump."

    # Good metrics = buy signal
    if opp.is_safe and (opp.liquidity_usd or 0) > 50000:
        if opp.signal == "graduated":
            return "buy", "Fresh graduation, good liquidity. Early entry."
        if (opp.price_change_1h or 0) > 5:
            return "buy", "Momentum + liquidity. Consider entry."
        return "watch", "Safe token. Wait for better entry."

    # New with decent metrics
    if opp.signal == "new_pair" and (opp.volume_24h_usd or 0) > 50000:
        return "watch", "New pair with volume. Monitor for trend."

    # Default
    return "watch", "Monitor for more data."


def _format_opportunity(opp: TokenOpportunity) -> dict:
    """Format opportunity for output."""
    return {
        "token": {
            "mint": opp.mint,
            "symbol": opp.symbol,
            "name": opp.name,
        },
        "source": opp.source,
        "signal": opp.signal,
        "price_usd": opp.price_usd,
        "price_change": {
            "5m": opp.price_change_5m,
            "1h": opp.price_change_1h,
            "24h": opp.price_change_24h,
        },
        "volume_24h_usd": opp.volume_24h_usd,
        "liquidity_usd": opp.liquidity_usd,
        "age": opp.age,
        "activity": {
            "buys_24h": opp.buys_24h,
            "sells_24h": opp.sells_24h,
        },
        "safety": {
            "risk_score": opp.risk_score,
            "is_safe": opp.is_safe,
        },
        "dex": opp.dex,
        "url": opp.url,
        "boosted": opp.boosted,
        "recommendation": opp.recommendation,
        "reason": opp.reason,
    }


# ============================================================================
# Watchlist functions (unchanged)
# ============================================================================


async def watch_token(mint: str, alert_on: str = "10% change") -> dict:
    """Add a token to your watchlist."""
    _init_db()
    db_path = _get_config_db_path()

    client = JupiterDataClient(api_key=get_jupiter_api_key())
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
    """Get all tokens in your watchlist with current prices."""
    _init_db()
    db_path = _get_config_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT mint, symbol, alert_condition, added_at FROM watchlist")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    client = JupiterDataClient(api_key=get_jupiter_api_key())
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
    """Remove a token from your watchlist."""
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
