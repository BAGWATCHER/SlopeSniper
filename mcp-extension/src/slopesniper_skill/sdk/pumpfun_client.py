"""
Pump.fun Data Client via PumpPortal.

Provides access to Pump.fun data via PumpPortal's WebSocket API:
- Real-time new token launches
- Token trades and migrations
- Bonding curve data (free tier)
- PumpSwap data after migration (requires API key - BYOK)

API Docs: https://pumpportal.fun/data-api/real-time
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, AsyncIterator, Callable

import websockets
from websockets.exceptions import ConnectionClosed

from .utils import Utils


class PumpPortalClient:
    """
    Client for Pump.fun data via PumpPortal WebSocket API.

    Free tier: Bonding curve trades and new token events
    Paid tier: PumpSwap data after migration (set PUMPPORTAL_API_KEY)

    Usage:
        client = PumpPortalClient()

        # Stream new tokens
        async for token in client.stream_new_tokens(limit=10):
            print(token)

        # Get recent tokens (collects from stream)
        tokens = await client.get_latest_tokens(limit=20, timeout=30)
    """

    WS_URL = "wss://pumpportal.fun/api/data"

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize PumpPortal client.

        Args:
            api_key: Optional PumpPortal API key for PumpSwap data.
                     Can also be set via PUMPPORTAL_API_KEY env var.
        """
        self.logger = Utils.setup_logger("PumpPortalClient")
        self.api_key = api_key or os.environ.get("PUMPPORTAL_API_KEY")
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._subscriptions: set[str] = set()

    def _get_version(self) -> str:
        """Get package version for logging."""
        try:
            from .. import __version__

            return __version__
        except Exception:
            return "unknown"

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL with API key if available."""
        if self.api_key:
            return f"{self.WS_URL}?api-key={self.api_key}"
        return self.WS_URL

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if self._ws is not None:
            return

        self.logger.debug("[connect] Connecting to PumpPortal...")
        try:
            self._ws = await websockets.connect(
                self.ws_url,
                close_timeout=5,
                user_agent_header=f"SlopeSniper/{self._get_version()}",
            )
            self.logger.info("[connect] Connected to PumpPortal WebSocket")
        except Exception as e:
            self.logger.error(f"[connect] Failed: {e}")
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._subscriptions.clear()
            self.logger.debug("[disconnect] Disconnected from PumpPortal")

    async def _send(self, payload: dict) -> None:
        """Send a message to the WebSocket."""
        if not self._ws:
            await self.connect()
        await self._ws.send(json.dumps(payload))

    async def _recv(self, timeout: float = 30) -> dict | None:
        """Receive a message from the WebSocket."""
        if not self._ws:
            return None
        try:
            msg = await asyncio.wait_for(self._ws.recv(), timeout=timeout)
            return json.loads(msg)
        except asyncio.TimeoutError:
            return None
        except ConnectionClosed:
            self._ws = None
            return None

    async def subscribe_new_tokens(self) -> None:
        """Subscribe to new token creation events."""
        await self._send({"method": "subscribeNewToken"})
        self._subscriptions.add("newToken")
        self.logger.debug("[subscribe] Subscribed to new token events")

    async def subscribe_migrations(self) -> None:
        """Subscribe to token migration events (bonding curve -> DEX)."""
        await self._send({"method": "subscribeMigration"})
        self._subscriptions.add("migration")
        self.logger.debug("[subscribe] Subscribed to migration events")

    async def subscribe_token_trades(self, mints: list[str]) -> None:
        """
        Subscribe to trades for specific tokens.

        Args:
            mints: List of token mint addresses to watch
        """
        await self._send({"method": "subscribeTokenTrade", "keys": mints})
        self._subscriptions.add(f"tokenTrade:{','.join(mints[:3])}")
        self.logger.debug(f"[subscribe] Subscribed to trades for {len(mints)} tokens")

    async def subscribe_account_trades(self, accounts: list[str]) -> None:
        """
        Subscribe to trades by specific accounts.

        Args:
            accounts: List of wallet addresses to watch
        """
        await self._send({"method": "subscribeAccountTrade", "keys": accounts})
        self._subscriptions.add(f"accountTrade:{','.join(accounts[:3])}")
        self.logger.debug(f"[subscribe] Subscribed to trades for {len(accounts)} accounts")

    async def unsubscribe_new_tokens(self) -> None:
        """Unsubscribe from new token events."""
        await self._send({"method": "unsubscribeNewToken"})
        self._subscriptions.discard("newToken")

    async def unsubscribe_token_trades(self, mints: list[str]) -> None:
        """Unsubscribe from token trade events."""
        await self._send({"method": "unsubscribeTokenTrade", "keys": mints})

    async def stream_new_tokens(
        self,
        limit: int | None = None,
        timeout: float = 60,
        on_token: Callable[[dict], None] | None = None,
    ) -> AsyncIterator[dict]:
        """
        Stream new token creation events.

        Args:
            limit: Max number of tokens to yield (None = unlimited)
            timeout: Timeout in seconds for each message
            on_token: Optional callback for each token

        Yields:
            Token data dictionaries
        """
        await self.connect()
        await self.subscribe_new_tokens()

        count = 0
        try:
            while limit is None or count < limit:
                data = await self._recv(timeout=timeout)
                if data is None:
                    break

                # Skip subscription confirmations
                if "message" in data and "subscribed" in data.get("message", "").lower():
                    continue

                # Only yield actual token events
                if "mint" in data and data.get("txType") == "create":
                    formatted = self.format_token_event(data)
                    if on_token:
                        on_token(formatted)
                    yield formatted
                    count += 1

        except ConnectionClosed:
            self.logger.warning("[stream] Connection closed")
        finally:
            await self.disconnect()

    async def stream_migrations(
        self,
        limit: int | None = None,
        timeout: float = 120,
    ) -> AsyncIterator[dict]:
        """
        Stream token migration events (graduated tokens).

        Args:
            limit: Max number of migrations to yield
            timeout: Timeout for each message

        Yields:
            Migration event dictionaries
        """
        await self.connect()
        await self.subscribe_migrations()

        count = 0
        try:
            while limit is None or count < limit:
                data = await self._recv(timeout=timeout)
                if data is None:
                    break

                if "message" in data:
                    continue

                if "mint" in data:
                    yield self.format_migration_event(data)
                    count += 1

        except ConnectionClosed:
            self.logger.warning("[stream] Connection closed")
        finally:
            await self.disconnect()

    async def stream_token_trades(
        self,
        mint: str,
        limit: int | None = None,
        timeout: float = 60,
    ) -> AsyncIterator[dict]:
        """
        Stream trades for a specific token.

        Args:
            mint: Token mint address
            limit: Max trades to yield
            timeout: Timeout per message

        Yields:
            Trade event dictionaries
        """
        await self.connect()
        await self.subscribe_token_trades([mint])

        count = 0
        try:
            while limit is None or count < limit:
                data = await self._recv(timeout=timeout)
                if data is None:
                    break

                if "message" in data:
                    continue

                if "mint" in data and data.get("mint") == mint:
                    yield self.format_trade_event(data)
                    count += 1

        except ConnectionClosed:
            self.logger.warning("[stream] Connection closed")
        finally:
            await self.disconnect()

    async def get_latest_tokens(self, limit: int = 20, timeout: float = 30) -> list[dict]:
        """
        Get recently created tokens by collecting from stream.

        Args:
            limit: Number of tokens to collect
            timeout: Max time to wait

        Returns:
            List of token dictionaries
        """
        self.logger.info(f"[get_latest_tokens] Collecting {limit} tokens (timeout: {timeout}s)")
        tokens = []

        try:
            async for token in self.stream_new_tokens(limit=limit, timeout=timeout / max(limit, 1)):
                tokens.append(token)
                if len(tokens) >= limit:
                    break
        except Exception as e:
            self.logger.warning(f"[get_latest_tokens] Stopped early: {e}")

        self.logger.info(f"[get_latest_tokens] Collected {len(tokens)} tokens")
        return tokens

    async def get_graduated_tokens(self, limit: int = 20, timeout: float = 60) -> list[dict]:
        """
        Get recently graduated/migrated tokens.

        Note: Migrations are less frequent than new tokens.

        Args:
            limit: Number of migrations to collect
            timeout: Max time to wait

        Returns:
            List of migration event dictionaries
        """
        self.logger.info(f"[get_graduated_tokens] Collecting migrations (timeout: {timeout}s)")
        migrations = []

        try:
            async for event in self.stream_migrations(limit=limit, timeout=timeout):
                migrations.append(event)
                if len(migrations) >= limit:
                    break
        except Exception as e:
            self.logger.warning(f"[get_graduated_tokens] Stopped early: {e}")

        self.logger.info(f"[get_graduated_tokens] Collected {len(migrations)} migrations")
        return migrations

    async def get_token_trades(self, mint: str, limit: int = 20, timeout: float = 30) -> list[dict]:
        """
        Get recent trades for a token.

        Args:
            mint: Token mint address
            limit: Number of trades to collect
            timeout: Max time to wait

        Returns:
            List of trade dictionaries
        """
        self.logger.info(f"[get_token_trades] Collecting trades for {mint[:8]}...")
        trades = []

        try:
            async for trade in self.stream_token_trades(mint, limit=limit, timeout=timeout):
                trades.append(trade)
                if len(trades) >= limit:
                    break
        except Exception as e:
            self.logger.warning(f"[get_token_trades] Stopped early: {e}")

        return trades

    def format_token_event(self, data: dict) -> dict:
        """
        Format a PumpPortal token creation event.

        Args:
            data: Raw event from WebSocket

        Returns:
            Normalized token dictionary
        """
        # Calculate bonding curve progress from virtual reserves
        v_sol = float(data.get("vSolInBondingCurve", 0))
        market_cap_sol = float(data.get("marketCapSol", 0))

        # Estimate USD value (rough, would need price feed for accuracy)
        # Using ~$150/SOL as rough estimate
        sol_price_estimate = 150
        market_cap_usd = market_cap_sol * sol_price_estimate

        # Bonding curve graduates around 85 SOL (~$12k at current prices)
        bonding_progress = min(100, (v_sol / 85) * 100)

        return {
            "symbol": data.get("symbol", "???"),
            "name": data.get("name", "Unknown"),
            "mint": data.get("mint"),
            "market_cap_sol": round(market_cap_sol, 4),
            "market_cap_usd": round(market_cap_usd, 2),
            "bonding_progress": round(bonding_progress, 1),
            "is_graduated": False,
            "signature": data.get("signature"),
            "creator": data.get("traderPublicKey"),
            "initial_buy_sol": float(data.get("solAmount", 0)),
            "bonding_curve_key": data.get("bondingCurveKey"),
            "uri": data.get("uri"),
            "pool": data.get("pool", "pump"),
            "is_mayhem_mode": data.get("is_mayhem_mode", False),
            "timestamp": datetime.now().isoformat(),
        }

    def format_migration_event(self, data: dict) -> dict:
        """
        Format a token migration/graduation event.

        Args:
            data: Raw migration event

        Returns:
            Normalized migration dictionary
        """
        return {
            "symbol": data.get("symbol", "???"),
            "name": data.get("name", "Unknown"),
            "mint": data.get("mint"),
            "is_graduated": True,
            "signature": data.get("signature"),
            "pool": data.get("pool"),
            "timestamp": datetime.now().isoformat(),
        }

    def format_trade_event(self, data: dict) -> dict:
        """
        Format a trade event.

        Args:
            data: Raw trade event

        Returns:
            Normalized trade dictionary
        """
        return {
            "type": data.get("txType", "unknown"),
            "mint": data.get("mint"),
            "symbol": data.get("symbol"),
            "trader": data.get("traderPublicKey"),
            "sol_amount": float(data.get("solAmount", 0)),
            "token_amount": float(data.get("tokenAmount", 0)) if data.get("tokenAmount") else None,
            "market_cap_sol": float(data.get("marketCapSol", 0)),
            "signature": data.get("signature"),
            "is_buy": data.get("txType") == "buy",
            "timestamp": datetime.now().isoformat(),
        }

    def format_token_summary(self, token: dict) -> dict:
        """
        Format token for display (backward compatibility).

        Handles both old Pump.fun format and new PumpPortal format.
        """
        # Check if already in new format
        if "market_cap_sol" in token:
            return token

        # Convert old format
        market_cap = float(token.get("usd_market_cap", 0))
        bonding_progress = min(100, (market_cap / 69000) * 100)

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


# Backward compatibility alias
PumpFunClient = PumpPortalClient
