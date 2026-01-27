"""
DexScreener API Client.

Provides access to real-time DEX data including:
- New token pairs
- Trending tokens
- Token profiles with age, volume, price changes
- Boosted/promoted tokens

API Docs: https://docs.dexscreener.com/api/reference
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import aiohttp

from .utils import Utils


class DexScreenerClient:
    """
    Client for DexScreener API.

    Free tier, no API key required.
    Rate limits: Be respectful, no official limits published.
    """

    BASE_URL = "https://api.dexscreener.com"

    def __init__(self) -> None:
        self.logger = Utils.setup_logger("DexScreenerClient")

    async def _request(
        self,
        endpoint: str,
        params: dict | None = None,
        timeout: int = 15
    ) -> dict[str, Any]:
        """Make API request."""
        url = f"{self.BASE_URL}{endpoint}"
        self.logger.debug(f"[_request] GET {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers={"User-Agent": "SlopeSniper/0.1.0"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data
                    else:
                        self.logger.warning(f"[_request] Status {resp.status}")
                        return {}
        except Exception as e:
            self.logger.error(f"[_request] Error: {e}")
            return {}

    async def get_token_profiles(self, chain: str = "solana") -> list[dict]:
        """
        Get latest token profiles (new listings with metadata).

        Returns tokens that have set up profiles on DexScreener.
        Good for finding legitimate new projects.
        """
        self.logger.info(f"[get_token_profiles] Fetching profiles for {chain}")
        data = await self._request("/token-profiles/latest/v1")

        # Filter to Solana only
        profiles = []
        for item in data if isinstance(data, list) else []:
            if item.get("chainId") == chain:
                profiles.append(item)

        self.logger.info(f"[get_token_profiles] Found {len(profiles)} profiles")
        return profiles[:20]  # Limit results

    async def get_boosted_tokens(self, chain: str = "solana") -> list[dict]:
        """
        Get tokens that are currently boosted/promoted.

        These are tokens where teams paid for visibility.
        Can indicate active marketing (bullish) or desperation (bearish).
        """
        self.logger.info(f"[get_boosted_tokens] Fetching boosted for {chain}")
        data = await self._request("/token-boosts/latest/v1")

        boosted = []
        for item in data if isinstance(data, list) else []:
            if item.get("chainId") == chain:
                boosted.append(item)

        self.logger.info(f"[get_boosted_tokens] Found {len(boosted)} boosted")
        return boosted[:20]

    async def get_top_boosted(self, chain: str = "solana") -> list[dict]:
        """Get tokens with most active boosts."""
        self.logger.info(f"[get_top_boosted] Fetching top boosted for {chain}")
        data = await self._request("/token-boosts/top/v1")

        top = []
        for item in data if isinstance(data, list) else []:
            if item.get("chainId") == chain:
                top.append(item)

        self.logger.info(f"[get_top_boosted] Found {len(top)} top boosted")
        return top[:20]

    async def search_pairs(self, query: str) -> list[dict]:
        """
        Search for token pairs by name, symbol, or address.

        Returns detailed pair info including:
        - Price, volume, liquidity
        - Price changes (5m, 1h, 6h, 24h)
        - Pair age
        - Transaction counts
        """
        self.logger.info(f"[search_pairs] Searching: {query}")
        data = await self._request("/latest/dex/search", {"q": query})

        pairs = data.get("pairs", [])
        # Filter to Solana
        solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]

        self.logger.info(f"[search_pairs] Found {len(solana_pairs)} Solana pairs")
        return solana_pairs[:20]

    async def get_token_pairs(self, token_address: str) -> list[dict]:
        """
        Get all trading pairs for a specific token.

        Includes full details: price, volume, liquidity, age, etc.
        """
        self.logger.info(f"[get_token_pairs] Fetching pairs for {token_address[:8]}...")
        data = await self._request(f"/tokens/v1/solana/{token_address}")

        pairs = data if isinstance(data, list) else data.get("pairs", [])
        self.logger.info(f"[get_token_pairs] Found {len(pairs)} pairs")
        return pairs

    async def get_pair_by_address(self, pair_address: str) -> dict | None:
        """Get detailed info for a specific pair address."""
        self.logger.info(f"[get_pair_by_address] Fetching {pair_address[:8]}...")
        data = await self._request(f"/pairs/solana/{pair_address}")

        pair = data.get("pair") if isinstance(data, dict) else None
        return pair

    async def get_new_pairs(
        self,
        min_liquidity_usd: float = 10000,
        max_age_hours: int = 24,
        limit: int = 20
    ) -> list[dict]:
        """
        Get newly created pairs on Solana.

        Filters by:
        - Minimum liquidity (default $10k)
        - Maximum age (default 24 hours)
        """
        self.logger.info(
            f"[get_new_pairs] Searching for new pairs "
            f"(min_liq=${min_liquidity_usd}, max_age={max_age_hours}h)"
        )

        # Search for recent popular terms to find new pairs
        queries = ["pump", "pepe", "trump", "ai", "meme", "doge", "cat"]
        all_pairs = []

        for query in queries[:3]:  # Limit queries to avoid rate limits
            pairs = await self.search_pairs(query)
            all_pairs.extend(pairs)
            await asyncio.sleep(0.2)  # Be nice to the API

        # Deduplicate by pair address
        seen = set()
        unique_pairs = []
        for pair in all_pairs:
            addr = pair.get("pairAddress")
            if addr and addr not in seen:
                seen.add(addr)
                unique_pairs.append(pair)

        # Filter by liquidity and age
        now = datetime.now()
        filtered = []
        for pair in unique_pairs:
            try:
                liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                if liquidity < min_liquidity_usd:
                    continue

                # Check age
                created_at = pair.get("pairCreatedAt")
                if created_at:
                    created = datetime.fromtimestamp(created_at / 1000)
                    age_hours = (now - created).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        continue
                    pair["_age_hours"] = round(age_hours, 1)

                filtered.append(pair)
            except (ValueError, TypeError):
                continue

        # Sort by volume
        filtered.sort(
            key=lambda p: float(p.get("volume", {}).get("h24", 0)),
            reverse=True
        )

        self.logger.info(f"[get_new_pairs] Found {len(filtered)} matching pairs")
        return filtered[:limit]

    async def get_trending(self, limit: int = 20) -> list[dict]:
        """
        Get trending tokens based on volume and activity.

        Combines multiple signals:
        - High 24h volume
        - Significant price changes
        - Active trading (many transactions)
        """
        self.logger.info("[get_trending] Fetching trending tokens")

        # Get boosted tokens (active marketing)
        boosted = await self.get_boosted_tokens()

        # Get pairs from boosted tokens
        trending = []
        for token in boosted[:10]:
            try:
                token_addr = token.get("tokenAddress")
                if token_addr:
                    pairs = await self.get_token_pairs(token_addr)
                    if pairs:
                        # Add boost info to best pair
                        best_pair = pairs[0]
                        best_pair["_boosted"] = True
                        best_pair["_boost_amount"] = token.get("amount", 0)
                        trending.append(best_pair)
                    await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.debug(f"[get_trending] Error processing token: {e}")
                continue

        # Sort by volume
        trending.sort(
            key=lambda p: float(p.get("volume", {}).get("h24", 0)),
            reverse=True
        )

        self.logger.info(f"[get_trending] Found {len(trending)} trending")
        return trending[:limit]

    def format_pair_summary(self, pair: dict) -> dict:
        """Format a pair into a clean summary."""
        base_token = pair.get("baseToken", {})
        price_change = pair.get("priceChange", {})
        volume = pair.get("volume", {})
        liquidity = pair.get("liquidity", {})
        txns = pair.get("txns", {})

        # Calculate age
        age_str = "unknown"
        created_at = pair.get("pairCreatedAt")
        if created_at:
            try:
                created = datetime.fromtimestamp(created_at / 1000)
                age = datetime.now() - created
                if age.days > 0:
                    age_str = f"{age.days}d"
                elif age.seconds > 3600:
                    age_str = f"{age.seconds // 3600}h"
                else:
                    age_str = f"{age.seconds // 60}m"
            except Exception:
                pass

        return {
            "symbol": base_token.get("symbol", "???"),
            "name": base_token.get("name", "Unknown"),
            "mint": base_token.get("address"),
            "price_usd": float(pair.get("priceUsd", 0)),
            "price_change_5m": float(price_change.get("m5", 0)),
            "price_change_1h": float(price_change.get("h1", 0)),
            "price_change_24h": float(price_change.get("h24", 0)),
            "volume_24h": float(volume.get("h24", 0)),
            "liquidity_usd": float(liquidity.get("usd", 0)),
            "buys_24h": txns.get("h24", {}).get("buys", 0),
            "sells_24h": txns.get("h24", {}).get("sells", 0),
            "age": age_str,
            "pair_address": pair.get("pairAddress"),
            "dex": pair.get("dexId", "unknown"),
            "url": pair.get("url"),
            "boosted": pair.get("_boosted", False),
        }
