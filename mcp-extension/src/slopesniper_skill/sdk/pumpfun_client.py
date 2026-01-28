"""
Pump.fun API Client.

Provides access to Pump.fun data including:
- Graduated/migrated tokens (bonding curve completed)
- New token launches
- Token details and trading activity

Note: Pump.fun's API is unofficial and may change.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import aiohttp

from .utils import Utils


class PumpFunClient:
    """
    Client for Pump.fun data.

    Endpoints discovered from their frontend.
    May break if they change their API.
    """

    BASE_URL = "https://frontend-api.pump.fun"
    GRADUATED_URL = "https://client-api-2-74b1891ee9f9.herokuapp.com"

    def __init__(self) -> None:
        self.logger = Utils.setup_logger("PumpFunClient")

    def _get_version(self) -> str:
        """Get package version for User-Agent."""
        try:
            from .. import __version__

            return __version__
        except Exception:
            return "unknown"

    async def _request(self, url: str, params: dict | None = None, timeout: int = 15) -> Any:
        """Make API request."""
        self.logger.debug(f"[_request] GET {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers={
                        "User-Agent": f"Mozilla/5.0 (compatible; SlopeSniper/{self._get_version()})",
                        "Accept": "application/json",
                    },
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        self.logger.warning(f"[_request] Status {resp.status}")
                        return None
        except Exception as e:
            self.logger.error(f"[_request] Error: {e}")
            return None

    async def get_graduated_tokens(self, limit: int = 50) -> list[dict]:
        """
        Get tokens that have graduated (completed bonding curve).

        These are tokens that filled their bonding curve and
        migrated to Raydium for open trading.
        """
        self.logger.info("[get_graduated_tokens] Fetching graduated tokens")

        # Try the graduated coins endpoint
        data = await self._request(
            f"{self.GRADUATED_URL}/coins/graduated", {"limit": limit, "offset": 0}
        )

        if data and isinstance(data, list):
            self.logger.info(f"[get_graduated_tokens] Found {len(data)} graduated")
            return data

        # Fallback: try king of the hill (top tokens)
        data = await self._request(
            f"{self.BASE_URL}/coins/king-of-the-hill", {"includeNsfw": "false"}
        )

        if data and isinstance(data, list):
            self.logger.info(f"[get_graduated_tokens] Found {len(data)} from KOTH")
            return data

        return []

    async def get_latest_tokens(self, limit: int = 50) -> list[dict]:
        """
        Get most recently created tokens on Pump.fun.

        These are brand new tokens still in bonding curve phase.
        """
        self.logger.info("[get_latest_tokens] Fetching latest tokens")

        data = await self._request(
            f"{self.BASE_URL}/coins",
            {"offset": 0, "limit": limit, "sort": "created_timestamp", "order": "DESC"},
        )

        if data and isinstance(data, list):
            self.logger.info(f"[get_latest_tokens] Found {len(data)} tokens")
            return data

        return []

    async def get_token(self, mint: str) -> dict | None:
        """Get detailed info for a specific token."""
        self.logger.info(f"[get_token] Fetching {mint[:8]}...")

        data = await self._request(f"{self.BASE_URL}/coins/{mint}")
        return data

    async def get_token_trades(self, mint: str, limit: int = 50) -> list[dict]:
        """Get recent trades for a token."""
        self.logger.info(f"[get_token_trades] Fetching trades for {mint[:8]}...")

        data = await self._request(f"{self.BASE_URL}/trades/latest/{mint}", {"limit": limit})

        if data and isinstance(data, list):
            return data
        return []

    async def search_tokens(self, query: str, limit: int = 20) -> list[dict]:
        """Search for tokens by name or symbol."""
        self.logger.info(f"[search_tokens] Searching: {query}")

        data = await self._request(
            f"{self.BASE_URL}/coins/search", {"query": query, "limit": limit}
        )

        if data and isinstance(data, list):
            self.logger.info(f"[search_tokens] Found {len(data)} results")
            return data

        return []

    async def get_trending(self, limit: int = 20) -> list[dict]:
        """
        Get trending tokens on Pump.fun.

        Based on recent trading activity and volume.
        """
        self.logger.info("[get_trending] Fetching trending tokens")

        # Try multiple endpoints
        endpoints = [
            (f"{self.BASE_URL}/coins/featured", {}),
            (f"{self.BASE_URL}/coins/king-of-the-hill", {"includeNsfw": "false"}),
        ]

        for url, params in endpoints:
            data = await self._request(url, params)
            if data and isinstance(data, list) and len(data) > 0:
                self.logger.info(f"[get_trending] Found {len(data)} trending")
                return data[:limit]

        return []

    def format_token_summary(self, token: dict) -> dict:
        """Format a Pump.fun token into a clean summary."""
        # Calculate progress through bonding curve
        market_cap = float(token.get("usd_market_cap", 0))
        bonding_progress = min(100, (market_cap / 69000) * 100)  # ~$69k to graduate

        # Parse created time
        age_str = "unknown"
        created = token.get("created_timestamp")
        if created:
            try:
                created_dt = datetime.fromtimestamp(created / 1000)
                age = datetime.now() - created_dt
                if age.days > 0:
                    age_str = f"{age.days}d"
                elif age.seconds > 3600:
                    age_str = f"{age.seconds // 3600}h"
                else:
                    age_str = f"{age.seconds // 60}m"
            except Exception:
                pass

        return {
            "symbol": token.get("symbol", "???"),
            "name": token.get("name", "Unknown"),
            "mint": token.get("mint"),
            "market_cap_usd": market_cap,
            "bonding_progress": round(bonding_progress, 1),
            "is_graduated": token.get("complete", False) or bonding_progress >= 100,
            "age": age_str,
            "creator": token.get("creator"),
            "description": token.get("description", "")[:100],
            "image_uri": token.get("image_uri"),
            "twitter": token.get("twitter"),
            "telegram": token.get("telegram"),
            "website": token.get("website"),
            "reply_count": token.get("reply_count", 0),
            "king_of_the_hill": token.get("king_of_the_hill_timestamp") is not None,
            "raydium_pool": token.get("raydium_pool"),
        }
