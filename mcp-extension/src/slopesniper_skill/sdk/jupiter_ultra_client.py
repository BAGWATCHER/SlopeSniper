"""
Jupiter Ultra Client - Swap API.

Provides access to Jupiter's Ultra API for executing token swaps.
Ultra API combines quote generation and transaction execution.

APIs:
- GET /order - Get quote and unsigned transaction
- POST /execute - Execute signed transaction
- GET /holdings/{address} - Get wallet token balances
"""

from __future__ import annotations

import asyncio
import base64
import os
from typing import Any, Optional

import aiohttp
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

from .utils import Utils


class JupiterUltraClient:
    """
    Client for Jupiter Ultra Swap API.

    Features:
    - Get swap quotes with unsigned transactions
    - Execute signed swaps
    - Query wallet holdings
    - Exponential backoff with configurable retry logic
    """

    BASE_URL = "https://api.jup.ag/ultra/v1"

    # Solana token addresses
    SOL_MINT = "So11111111111111111111111111111111111111112"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    def __init__(
        self, api_key: Optional[str] = None, max_retries: int = 5
    ) -> None:
        """
        Initialize Jupiter Ultra Client.

        Args:
            api_key: Jupiter Ultra API key (or set JUPITER_API_KEY env var)
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.logger = Utils.setup_logger("JupiterUltraClient")
        self.max_retries = max_retries

        # Get API key: user override > env var > bundled default
        # Users can provide their own key for higher rate limits
        self.api_key = api_key or os.environ.get("JUPITER_API_KEY") or self._get_bundled_key()

        if os.environ.get("JUPITER_API_KEY"):
            self.logger.info("[__init__] JupiterUltraClient initialized with custom API key")
        else:
            self.logger.info("[__init__] JupiterUltraClient initialized with bundled API key")

    def _get_bundled_key(self) -> str:
        """Get bundled Jupiter API key from remote endpoint."""
        # Fetch from SlopeSniper API - key is centrally managed
        # Fallback to embedded key if endpoint unreachable
        config_url = os.environ.get(
            "SLOPESNIPER_CONFIG_URL",
            "https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/jup.json"
        )

        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                config_url,
                headers={"User-Agent": "SlopeSniper/0.1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

                # Decode obfuscated key (v1 format)
                if data.get("v") == 1 and data.get("k"):
                    key = self._xor_deobfuscate(data["k"], "slopesniper2024")
                    if key:
                        self.logger.debug("[_get_bundled_key] Fetched key from config endpoint")
                        return key

                # Legacy format (plain key)
                if data.get("key"):
                    self.logger.debug("[_get_bundled_key] Fetched key from config endpoint (legacy)")
                    return data["key"]

        except Exception as e:
            self.logger.debug(f"[_get_bundled_key] Could not fetch from endpoint: {e}")

        # Fallback to embedded key (base64 obfuscated)
        import base64
        _k = "YTI1YzM3NWEtN2QxMy00NDI1LWJiYzktZjhkOGJmNDA4ZjEx"
        try:
            self.logger.debug("[_get_bundled_key] Using fallback embedded key")
            return base64.b64decode(_k).decode()
        except Exception:
            return ""

    def _xor_deobfuscate(self, encoded: str, key: str) -> str:
        """Decode XOR-obfuscated string."""
        import base64
        try:
            xored = base64.b64decode(encoded)
            key_bytes = (key * ((len(xored) // len(key)) + 1))[:len(xored)]
            return bytes(a ^ b for a, b in zip(xored, key_bytes.encode())).decode()
        except Exception:
            return ""

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            url: Full URL to request
            method: HTTP method (GET, POST)
            params: Query parameters for GET requests
            json_data: JSON body for POST requests
            timeout: Request timeout in seconds

        Returns:
            JSON response as dictionary
        """
        self.logger.debug(f"[_make_request] {method} {url}, params={params}")

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Content-Type": "application/json"}
                    if self.api_key:
                        headers["x-api-key"] = self.api_key

                    request_kwargs: dict[str, Any] = {
                        "timeout": aiohttp.ClientTimeout(total=timeout),
                        "headers": headers,
                    }

                    if method == "GET":
                        request_kwargs["params"] = params
                        async with session.get(url, **request_kwargs) as response:
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
                                    f"failed: status={response.status}, "
                                    f"body={response_text[:500]}"
                                )

                    elif method == "POST":
                        request_kwargs["json"] = json_data
                        async with session.post(url, **request_kwargs) as response:
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
                                    f"failed: status={response.status}, "
                                    f"body={response_text[:500]}"
                                )

            except asyncio.TimeoutError:
                self.logger.warning(
                    f"[_make_request] Attempt {attempt + 1}/{self.max_retries} timed out"
                )
            except Exception as e:
                self.logger.error(
                    f"[_make_request] Attempt {attempt + 1}/{self.max_retries} error: {e}",
                    exc_info=(attempt == self.max_retries - 1),
                )
                if attempt == self.max_retries - 1:
                    raise

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = 2**attempt
                self.logger.info(f"[_make_request] Retrying in {delay}s...")
                await asyncio.sleep(delay)

        raise RuntimeError(f"Failed after {self.max_retries} attempts")

    async def get_order(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        taker: Optional[str] = None,
        slippage_bps: int = 50,
        exclude_dexes: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get swap quote and unsigned transaction.

        Args:
            input_mint: Token to sell (mint address)
            output_mint: Token to buy (mint address)
            amount: Amount in atomic units (smallest unit of token)
            taker: Wallet address (required to get transaction)
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)
            exclude_dexes: Comma-separated DEX names to exclude

        Returns:
            Order response with transaction and quote details
        """
        self.logger.info(
            f"[get_order] Requesting order: {input_mint[:8]}... -> {output_mint[:8]}..., "
            f"amount={amount}, slippage={slippage_bps}bps"
        )

        params: dict[str, Any] = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
        }

        if taker:
            params["taker"] = taker

        if exclude_dexes:
            params["excludeDexes"] = exclude_dexes

        try:
            url = f"{self.BASE_URL}/order"
            data = await self._make_request(url=url, method="GET", params=params)

            self.logger.info(
                f"[get_order] SUCCESS: "
                f"inAmount={data.get('inAmount')}, "
                f"outAmount={data.get('outAmount')}, "
                f"priceImpact={data.get('priceImpact', 0):.4f}%"
            )

            if data.get("errorCode"):
                self.logger.warning(
                    f"[get_order] Order has error: code={data.get('errorCode')}, "
                    f"message={data.get('errorMessage')}"
                )

            return data

        except Exception as e:
            self.logger.error(f"[get_order] FAILED: {e}", exc_info=True)
            raise

    async def execute_swap(
        self, signed_transaction: str, request_id: str
    ) -> dict[str, Any]:
        """
        Execute a signed swap transaction.

        Args:
            signed_transaction: Base64-encoded signed transaction
            request_id: Request ID from get_order() response

        Returns:
            Execution result with signature and amounts
        """
        self.logger.info(f"[execute_swap] Submitting transaction, requestId={request_id}")

        payload = {
            "signedTransaction": signed_transaction,
            "requestId": request_id,
        }

        try:
            url = f"{self.BASE_URL}/execute"
            data = await self._make_request(
                url=url, method="POST", json_data=payload, timeout=60
            )

            status = data.get("status")
            signature = data.get("signature")

            if status == "Success":
                self.logger.info(
                    f"[execute_swap] SUCCESS: signature={signature}, "
                    f"outputAmount={data.get('outputAmountResult')}"
                )
            else:
                self.logger.error(
                    f"[execute_swap] FAILED: status={status}, "
                    f"error={data.get('error')}"
                )

            return data

        except Exception as e:
            self.logger.error(f"[execute_swap] FAILED: {e}", exc_info=True)
            raise

    def sign_transaction(self, unsigned_tx_base64: str, keypair: Keypair) -> str:
        """
        Sign an unsigned transaction.

        Args:
            unsigned_tx_base64: Base64-encoded unsigned transaction
            keypair: Solana keypair to sign with

        Returns:
            Base64-encoded signed transaction
        """
        self.logger.info("[sign_transaction] Signing transaction")

        try:
            tx_bytes = base64.b64decode(unsigned_tx_base64)
            tx = VersionedTransaction.from_bytes(tx_bytes)
            signed_tx = VersionedTransaction(tx.message, [keypair])
            signed_tx_base64 = base64.b64encode(bytes(signed_tx)).decode("utf-8")

            self.logger.info("[sign_transaction] Transaction signed successfully")
            return signed_tx_base64

        except Exception as e:
            self.logger.error(f"[sign_transaction] FAILED: {e}", exc_info=True)
            raise

    async def get_holdings(self, address: str) -> dict[str, Any]:
        """
        Get token holdings for a wallet address.

        Args:
            address: Wallet address

        Returns:
            Holdings data with SOL balance and token holdings
        """
        self.logger.info(f"[get_holdings] Fetching holdings for {address}")

        try:
            url = f"{self.BASE_URL}/holdings/{address}"
            data = await self._make_request(url=url, method="GET")

            sol_balance = data.get("uiAmount", 0)
            token_count = len(data.get("tokens", {}))

            self.logger.info(
                f"[get_holdings] SUCCESS: SOL={sol_balance:.4f}, {token_count} token type(s)"
            )

            return data

        except Exception as e:
            self.logger.error(f"[get_holdings] FAILED: {e}", exc_info=True)
            raise
