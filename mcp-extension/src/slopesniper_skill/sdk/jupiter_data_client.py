"""
Jupiter Data Client - Price and Token Search APIs.

Provides access to Jupiter's Price API and Token Search API
for getting token prices and searching for tokens.
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Any, Optional

import aiohttp

from .utils import Utils


class JupiterDataClient:
    """
    Client for Jupiter Price and Token Search APIs.

    Features:
    - Get USD prices for tokens (up to 50 at once)
    - Search tokens by symbol, name, or mint address
    - Detailed token metadata including audit info and stats
    """

    # Use main API endpoints (not lite-api) for better rate limits with API key
    BASE_URL_PRICE = "https://api.jup.ag/price/v3"
    BASE_URL_TOKENS = "https://api.jup.ag/tokens/v2"

    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3) -> None:
        """
        Initialize Jupiter Data Client.

        Args:
            api_key: Optional Jupiter API key for higher rate limits
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.logger = Utils.setup_logger("JupiterDataClient")
        self.max_retries = max_retries

        # Get API key: user override > env var > bundled default
        self.api_key = api_key or os.environ.get("JUPITER_API_KEY") or self._get_bundled_key()

        if os.environ.get("JUPITER_API_KEY"):
            self.logger.info("[__init__] JupiterDataClient initialized with custom API key")
        elif api_key:
            self.logger.info("[__init__] JupiterDataClient initialized with provided API key")
        else:
            self.logger.info("[__init__] JupiterDataClient initialized with bundled API key")

    def _get_bundled_key(self) -> str:
        """
        Get bundled Jupiter API key from remote config.

        The key is fetched from GitHub and decoded at runtime.
        No fallback key is embedded in code for security.
        """
        config_url = os.environ.get(
            "SLOPESNIPER_CONFIG_URL",
            "https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/config/jup.json"
        )

        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                config_url,
                headers={"User-Agent": f"SlopeSniper/{self._get_version()}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

                # Decode key based on version
                version = data.get("v", 0)

                if version == 1 and data.get("k"):
                    # v1: XOR obfuscated
                    key = self._decode_v1(data["k"])
                    if key:
                        self.logger.debug("[_get_bundled_key] Fetched key from config (v1)")
                        return key

                # Legacy format (plain key) - for backwards compatibility
                if data.get("key"):
                    self.logger.debug("[_get_bundled_key] Fetched key (legacy format)")
                    return data["key"]

        except Exception as e:
            self.logger.warning(f"[_get_bundled_key] Could not fetch config: {e}")
            self.logger.warning("[_get_bundled_key] Set JUPITER_API_KEY env var or check network")

        return ""

    def _get_version(self) -> str:
        """Get package version for User-Agent."""
        try:
            from .. import __version__
            return __version__
        except Exception:
            return "0.0.0"

    def _decode_v1(self, encoded: str) -> str:
        """Decode v1 format (XOR obfuscated)."""
        _p = "slopesniper"
        _y = "2024"
        try:
            xored = base64.b64decode(encoded)
            key = f"{_p}{_y}"
            key_bytes = (key * ((len(xored) // len(key)) + 1))[:len(xored)]
            return bytes(a ^ b for a, b in zip(xored, key_bytes.encode())).decode()
        except Exception:
            return ""

    async def _make_request(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        """Make HTTP request with exponential backoff retry logic."""
        self.logger.debug(f"[_make_request] {method} {url}, params={params}")

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Build headers with API key if available
                    headers = {"Content-Type": "application/json"}
                    if self.api_key:
                        headers["x-api-key"] = self.api_key

                    if method == "GET":
                        timeout = aiohttp.ClientTimeout(total=10)
                        async with session.get(
                            url, params=params, timeout=timeout, headers=headers
                        ) as response:
                            response_text = await response.text()

                            if response.status == 200:
                                data = await response.json()
                                self.logger.debug(
                                    f"[_make_request] SUCCESS on attempt {attempt + 1}"
                                )
                                return data
                            else:
                                self.logger.warning(
                                    f"[_make_request] Attempt {attempt + 1}/{self.max_retries} "
                                    f"failed: status={response.status}"
                                )

                                if response.status == 400:
                                    raise ValueError(
                                        f"Bad request (400): {response_text}"
                                    )

            except asyncio.TimeoutError:
                self.logger.warning(
                    f"[_make_request] Attempt {attempt + 1}/{self.max_retries} timed out"
                )
            except Exception as e:
                self.logger.error(
                    f"[_make_request] Attempt {attempt + 1}/{self.max_retries} error: {e}"
                )
                if attempt == self.max_retries - 1:
                    raise

            if attempt < self.max_retries - 1:
                delay = 2**attempt
                self.logger.info(f"[_make_request] Retrying in {delay}s...")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Failed after {self.max_retries} attempts")

    async def get_prices(
        self, mint_addresses: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Get USD prices for one or more tokens.

        Args:
            mint_addresses: List of token mint addresses (max 50)

        Returns:
            Dictionary mapping mint addresses to price data
        """
        self.logger.info(
            f"[get_prices] Fetching prices for {len(mint_addresses)} token(s)"
        )

        if len(mint_addresses) > 50:
            self.logger.warning(
                f"[get_prices] Truncating to 50 mints (received {len(mint_addresses)})"
            )
            mint_addresses = mint_addresses[:50]

        ids_param = ",".join(mint_addresses)

        try:
            data = await self._make_request(
                url=self.BASE_URL_PRICE, params={"ids": ids_param}
            )
            self.logger.info(
                f"[get_prices] SUCCESS: Retrieved prices for {len(data)} token(s)"
            )
            return data

        except Exception as e:
            self.logger.error(f"[get_prices] FAILED: {e}", exc_info=True)
            raise

    async def get_price(self, mint_address: str) -> Optional[dict[str, Any]]:
        """
        Get USD price for a single token.

        Args:
            mint_address: Token mint address

        Returns:
            Price data dictionary or None if not found
        """
        self.logger.info(f"[get_price] Fetching price for {mint_address}")

        try:
            prices = await self.get_prices([mint_address])

            if mint_address in prices:
                price_data = prices[mint_address]
                self.logger.info(
                    f"[get_price] SUCCESS: ${price_data.get('usdPrice', 0):.8f}"
                )
                return price_data
            else:
                self.logger.warning(f"[get_price] Price not found for {mint_address}")
                return None

        except Exception as e:
            self.logger.error(f"[get_price] FAILED: {e}", exc_info=True)
            raise

    async def search_token(self, query: str) -> list[dict[str, Any]]:
        """
        Search for tokens by symbol, name, or mint address.

        Args:
            query: Search query

        Returns:
            List of token information dictionaries
        """
        self.logger.info(f"[search_token] Searching for: {query}")

        try:
            url = f"{self.BASE_URL_TOKENS}/search"
            data = await self._make_request(url=url, params={"query": query})

            if isinstance(data, list):
                self.logger.info(f"[search_token] SUCCESS: Found {len(data)} token(s)")
                return data
            else:
                self.logger.warning("[search_token] Unexpected response format")
                return []

        except Exception as e:
            self.logger.error(f"[search_token] FAILED: {e}", exc_info=True)
            raise

    async def get_token_info(self, mint_address: str) -> Optional[dict[str, Any]]:
        """
        Get detailed information for a specific token.

        Args:
            mint_address: Token mint address

        Returns:
            Token information dictionary or None
        """
        self.logger.info(f"[get_token_info] Fetching info for {mint_address}")

        try:
            results = await self.search_token(mint_address)

            if results and len(results) > 0:
                token_info = results[0]
                self.logger.info(
                    f"[get_token_info] SUCCESS: {token_info.get('symbol', 'N/A')} - "
                    f"MCap: ${token_info.get('mcap', 0):,.0f}"
                )
                return token_info
            else:
                self.logger.warning(f"[get_token_info] Token not found: {mint_address}")
                return None

        except Exception as e:
            self.logger.error(f"[get_token_info] FAILED: {e}", exc_info=True)
            raise

    def is_token_suspicious(self, token_info: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Check if a token has suspicious characteristics.

        Args:
            token_info: Token information from get_token_info()

        Returns:
            Tuple of (is_suspicious: bool, reasons: list[str])
        """
        reasons: list[str] = []
        audit = token_info.get("audit", {})

        if audit:
            if audit.get("isSus"):
                reasons.append("Flagged as suspicious by Jupiter")

            if not audit.get("mintAuthorityDisabled"):
                reasons.append("Mint authority not disabled")

            if not audit.get("freezeAuthorityDisabled"):
                reasons.append("Freeze authority not disabled")

            top_holders_pct = audit.get("topHoldersPercentage", 0)
            if top_holders_pct > 50:
                reasons.append(f"High holder concentration: {top_holders_pct:.1f}%")

            dev_balance_pct = audit.get("devBalancePercentage", 0)
            if dev_balance_pct > 10:
                reasons.append(f"Dev holds {dev_balance_pct:.1f}% of supply")

        organic_label = token_info.get("organicScoreLabel", "")
        if organic_label == "low":
            reasons.append("Low organic trading activity")

        is_suspicious = len(reasons) > 0

        if is_suspicious:
            self.logger.warning(
                f"[is_token_suspicious] Token {token_info.get('symbol', 'N/A')} "
                f"flagged: {', '.join(reasons)}"
            )

        return is_suspicious, reasons
