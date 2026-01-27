"""
Solana Trading Tools.

Six tools for safe Solana token trading with policy enforcement.
"""

from __future__ import annotations

from typing import Any, Optional

from ..sdk import JupiterDataClient, JupiterUltraClient, RugCheckClient, Utils
from .config import get_jupiter_api_key, get_keypair, get_wallet_address
from .intents import create_intent, get_intent, mark_executed
from .policy import KNOWN_SAFE_MINTS, check_policy, is_known_safe_mint


# Well-known token symbols to mint addresses
SYMBOL_TO_MINT: dict[str, str] = {
    "SOL": "So11111111111111111111111111111111111111112",
    "WSOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "MSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
    "STSOL": "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
}

# Token decimals for common tokens
TOKEN_DECIMALS: dict[str, int] = {
    "So11111111111111111111111111111111111111112": 9,  # SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,  # USDT
}

# Default decimals for unknown tokens
DEFAULT_DECIMALS = 9


def resolve_token(token: str) -> Optional[str]:
    """
    Resolve a token symbol or mint address to a mint address.

    Args:
        token: Token symbol (e.g., "SOL") or mint address

    Returns:
        Mint address or None if not found
    """
    # Check if it's already a mint address (base58, 32-44 chars)
    if len(token) >= 32 and len(token) <= 44:
        return token

    # Check known symbols
    upper = token.upper()
    if upper in SYMBOL_TO_MINT:
        return SYMBOL_TO_MINT[upper]

    return None


def get_token_decimals(mint: str) -> int:
    """Get decimals for a token (default 9 if unknown)."""
    return TOKEN_DECIMALS.get(mint, DEFAULT_DECIMALS)


def _get_symbol_for_mint(mint: str) -> str:
    """Get symbol for a mint address from known tokens."""
    for symbol, m in SYMBOL_TO_MINT.items():
        if m == mint:
            return symbol
    return mint[:8]  # Fallback to truncated mint


async def _get_sol_price_async() -> float:
    """Get current SOL price in USD."""
    try:
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        price_data = await data_client.get_price(SYMBOL_TO_MINT["SOL"])
        return float(price_data.get("usdPrice", 0)) if price_data else 0
    except Exception:
        return 0


async def solana_resolve_token(token: str) -> dict[str, Any]:
    """
    Resolve a token symbol or name to its mint address.

    Useful for finding the mint address of any token before trading.

    Args:
        token: Token symbol (e.g., "BONK", "POPCAT") or partial name

    Returns:
        Dict with symbol, name, mint, verified status.
        For ambiguous searches, returns top matches.
    """
    # First check if it's already a valid mint address
    if Utils.is_valid_solana_address(token):
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        info = await data_client.get_token_info(token)
        return {
            "mint": token,
            "symbol": info.get("symbol", "???") if info else "???",
            "name": info.get("name", "Unknown") if info else "Unknown",
            "verified": info.get("verified", False) if info else False,
            "found": True,
        }

    # Check known symbols
    upper = token.upper()
    if upper in SYMBOL_TO_MINT:
        mint = SYMBOL_TO_MINT[upper]
        return {
            "mint": mint,
            "symbol": upper,
            "name": upper,  # Known tokens
            "verified": True,
            "found": True,
        }

    # Search for the token
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    results = await data_client.search_token(token)

    if not results:
        return {
            "found": False,
            "error": f"No tokens found matching '{token}'",
            "suggestion": "Try a different search term or use the full mint address",
        }

    # Return best match + alternatives
    # Jupiter API uses "id" for mint address, not "address"
    best = results[0]
    response = {
        "mint": best.get("id") or best.get("address"),
        "symbol": best.get("symbol", ""),
        "name": best.get("name", ""),
        "verified": best.get("isVerified", False),
        "found": True,
    }

    # Include alternatives if ambiguous
    if len(results) > 1:
        response["alternatives"] = [
            {
                "mint": r.get("id") or r.get("address"),
                "symbol": r.get("symbol", ""),
                "name": r.get("name", ""),
            }
            for r in results[1:5]  # Up to 4 alternatives
        ]
        response["note"] = "Multiple matches found. Using best match. See 'alternatives' for other options."

    return response


async def solana_get_price(token: str) -> dict[str, Any]:
    """
    Get current USD price for a token.

    Args:
        token: Token mint address OR symbol (e.g., "SOL", "BONK")

    Returns:
        Dict with mint, symbol, price_usd, and optional market_cap
    """
    # Resolve symbol to mint if needed
    mint = resolve_token(token)

    if not mint:
        # Try searching for the token
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        results = await data_client.search_token(token)
        if results:
            # Jupiter API uses "id" for mint address
            mint = results[0].get("id") or results[0].get("address")
        else:
            return {"error": f"Token not found: {token}"}

    # Get price
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    price_data = await data_client.get_price(mint)

    if not price_data:
        return {"error": f"Price not available for {mint}"}

    # Get token info for symbol/market cap
    token_info = await data_client.get_token_info(mint)

    result: dict[str, Any] = {
        "mint": mint,
        "symbol": token_info.get("symbol") if token_info else None,
        "price_usd": float(price_data.get("usdPrice", 0)),
    }

    if token_info and "mcap" in token_info:
        result["market_cap"] = token_info["mcap"]

    return result


async def solana_search_token(query: str) -> list[dict[str, Any]]:
    """
    Search for tokens by name or symbol.

    Args:
        query: Search term (e.g., "bonk", "pepe")

    Returns:
        List of matching tokens with symbol, name, mint, verified, liquidity
    """
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    results = await data_client.search_token(query)

    tokens = []
    for token in results[:10]:  # Limit to top 10
        # Jupiter API uses "id" for mint address
        tokens.append({
            "symbol": token.get("symbol", ""),
            "name": token.get("name", ""),
            "mint": token.get("id") or token.get("address", ""),
            "verified": token.get("isVerified", False),
            "liquidity": token.get("liquidity"),
            "market_cap": token.get("mcap"),
            "price_usd": token.get("usdPrice"),
        })

    return tokens


async def solana_check_token(token: str) -> dict[str, Any]:
    """
    Run rugcheck safety analysis on a token.

    Args:
        token: Token mint address OR symbol (e.g., "BONK", "POPCAT")

    Returns:
        Dict with mint, symbol, is_safe, score, risk_factors, and reason
    """
    # Try to resolve symbol to mint
    mint_address = resolve_token(token)
    resolved_symbol = None

    if not mint_address:
        # Not a known symbol or valid address - try searching
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        results = await data_client.search_token(token)
        if results:
            # Jupiter API uses "id" for mint address
            mint_address = results[0].get("id") or results[0].get("address")
            resolved_symbol = results[0].get("symbol", token)
        else:
            return {"error": f"Token not found: {token}. Try searching first."}
    else:
        # Check if we resolved from a known symbol
        upper = token.upper()
        if upper in SYMBOL_TO_MINT:
            resolved_symbol = upper

    if not Utils.is_valid_solana_address(mint_address):
        return {"error": f"Could not resolve to valid mint address: {token}"}

    # Get symbol if we don't have it yet
    if not resolved_symbol:
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        info = await data_client.get_token_info(mint_address)
        resolved_symbol = info.get("symbol", mint_address[:8]) if info else mint_address[:8]

    # Known safe tokens always pass
    if is_known_safe_mint(mint_address):
        return {
            "mint": mint_address,
            "symbol": resolved_symbol,
            "is_safe": True,
            "score": 0,
            "risk_factors": [],
            "reason": "Known safe token (SOL/USDC/USDT/etc)",
        }

    rugcheck = RugCheckClient()
    result = await rugcheck.check_token(mint_address)

    risk_factors = []
    for risk in result.get("risks", []):
        level = risk.get("level", "")
        name = risk.get("name", "")
        if level in ["danger", "critical", "warning"]:
            risk_factors.append(f"[{level.upper()}] {name}")

    return {
        "mint": mint_address,
        "symbol": resolved_symbol,
        "is_safe": result.get("is_safe", False),
        "score": result.get("score"),
        "risk_factors": risk_factors,
        "reason": result.get("reason", ""),
    }


async def solana_get_wallet(address: Optional[str] = None) -> dict[str, Any]:
    """
    Get wallet balances and holdings.

    Args:
        address: Wallet address (optional - defaults to user's configured wallet)

    Returns:
        Dict with address, sol_balance, sol_value_usd, and tokens list
    """
    # Use provided address or default to user's wallet
    if not address:
        address = get_wallet_address()
        if not address:
            return {"error": "No wallet configured. Set SOLANA_PRIVATE_KEY."}

    if not Utils.is_valid_solana_address(address):
        return {"error": "Invalid wallet address"}

    ultra_client = JupiterUltraClient(api_key=get_jupiter_api_key())
    holdings = await ultra_client.get_holdings(address)

    # Parse holdings response
    # Holdings API returns: { amount, uiAmount, tokens: { mint: [{ account, amount, uiAmount, ... }] } }
    sol_balance = holdings.get("uiAmount", 0)
    tokens_data = holdings.get("tokens", {})

    # Get SOL price for USD calculation
    sol_price = await _get_sol_price_async()
    sol_value_usd = sol_balance * sol_price if sol_price > 0 else None

    # Collect all mints to fetch prices and info in batch
    mints = list(tokens_data.keys())

    # Get token info and prices
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    token_prices = {}
    token_symbols = {}

    if mints:
        try:
            # Get prices for all tokens
            prices = await data_client.get_prices(mints)
            for mint, price_data in prices.items():
                token_prices[mint] = float(price_data.get("usdPrice", 0))
        except Exception:
            pass  # Continue without prices

        # Get symbols from known list or search
        for mint in mints:
            # Check known symbols first
            symbol = None
            for sym, m in SYMBOL_TO_MINT.items():
                if m == mint:
                    symbol = sym
                    break
            if not symbol:
                try:
                    info = await data_client.get_token_info(mint)
                    symbol = info.get("symbol", mint[:8]) if info else mint[:8]
                except Exception:
                    symbol = mint[:8]
            token_symbols[mint] = symbol

    # Build tokens list
    tokens = []
    for mint, token_accounts in tokens_data.items():
        # Sum up uiAmount from all token accounts for this mint
        total_amount = 0.0
        if isinstance(token_accounts, list):
            for account in token_accounts:
                total_amount += float(account.get("uiAmount", 0))
        elif isinstance(token_accounts, dict):
            # Fallback if response format is different
            total_amount = float(token_accounts.get("uiAmount", 0))

        if total_amount > 0:
            price = token_prices.get(mint, 0)
            value_usd = total_amount * price if price > 0 else None

            tokens.append({
                "mint": mint,
                "symbol": token_symbols.get(mint, mint[:8]),
                "amount": total_amount,
                "value_usd": value_usd,
            })

    return {
        "address": address,
        "sol_balance": sol_balance,
        "sol_value_usd": sol_value_usd,
        "tokens": tokens,
    }


async def solana_quote(
    from_mint: str,
    to_mint: str,
    amount: str,
    slippage_bps: int = 50,
) -> dict[str, Any]:
    """
    Get a swap quote and create an intent (does NOT execute).

    Policy checks run here - blocks if trade fails safety checks.

    Args:
        from_mint: Token to sell (MUST be mint address)
        to_mint: Token to buy (MUST be mint address)
        amount: Amount to swap (string, in token units e.g., "1.5" for 1.5 SOL)
        slippage_bps: Slippage tolerance (default 50 = 0.5%)

    Returns:
        Dict with intent_id, amounts, price_impact, route, and expiry
    """
    # Validate inputs are mint addresses, not symbols
    if not Utils.is_valid_solana_address(from_mint):
        return {
            "error": f"from_mint must be a valid mint address, not a symbol. Got: {from_mint}"
        }
    if not Utils.is_valid_solana_address(to_mint):
        return {
            "error": f"to_mint must be a valid mint address, not a symbol. Got: {to_mint}"
        }

    # Get user's wallet
    keypair = get_keypair()
    if not keypair:
        return {"error": "No wallet configured. Set SOLANA_PRIVATE_KEY."}

    taker = str(keypair.pubkey())

    # Convert amount to atomic units
    decimals = get_token_decimals(from_mint)
    try:
        amount_float = float(amount)
        amount_atomic = int(amount_float * (10**decimals))
    except ValueError:
        return {"error": f"Invalid amount: {amount}"}

    # Get price of from_token to calculate USD value
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    price_data = await data_client.get_price(from_mint)
    if price_data:
        price_usd = float(price_data.get("usdPrice", 0))
        amount_usd = amount_float * price_usd
    else:
        # If we can't get price, assume $0 (will pass USD check)
        amount_usd = 0

    # Run rugcheck on destination token (if not known safe)
    rugcheck_result = None
    if not is_known_safe_mint(to_mint):
        rugcheck = RugCheckClient()
        rugcheck_result = await rugcheck.check_token(to_mint)

    # Run policy checks
    policy_result = check_policy(
        from_mint=from_mint,
        to_mint=to_mint,
        amount_usd=amount_usd,
        slippage_bps=slippage_bps,
        rugcheck_result=rugcheck_result,
    )

    if not policy_result.allowed:
        return {
            "error": "Policy blocked",
            "reason": policy_result.reason,
            "checks_passed": policy_result.checks_passed,
            "checks_failed": policy_result.checks_failed,
        }

    # Get quote from Jupiter
    ultra_client = JupiterUltraClient(api_key=get_jupiter_api_key())
    order = await ultra_client.get_order(
        input_mint=from_mint,
        output_mint=to_mint,
        amount=amount_atomic,
        taker=taker,
        slippage_bps=slippage_bps,
    )

    if order.get("errorCode"):
        return {
            "error": "Quote failed",
            "reason": order.get("errorMessage", "Unknown error"),
        }

    if not order.get("transaction"):
        return {"error": "No transaction returned from quote"}

    # Calculate output amount in UI units
    out_decimals = get_token_decimals(to_mint)
    out_amount_atomic = int(order.get("outAmount", 0))
    out_amount_ui = out_amount_atomic / (10**out_decimals)

    # Create intent
    intent_id = create_intent(
        from_mint=from_mint,
        to_mint=to_mint,
        amount=amount,
        slippage_bps=slippage_bps,
        out_amount_est=str(out_amount_ui),
        unsigned_tx=order["transaction"],
        request_id=order["requestId"],
    )

    # Get token symbols for route summary
    from_symbol = None
    to_symbol = None

    # Check known symbols first
    for symbol, mint in SYMBOL_TO_MINT.items():
        if mint == from_mint:
            from_symbol = symbol
        if mint == to_mint:
            to_symbol = symbol

    # Fallback to API lookup if needed
    if not from_symbol or not to_symbol:
        if not from_symbol:
            info = await data_client.get_token_info(from_mint)
            from_symbol = info.get("symbol", from_mint[:8]) if info else from_mint[:8]
        if not to_symbol:
            info = await data_client.get_token_info(to_mint)
            to_symbol = info.get("symbol", to_mint[:8]) if info else to_mint[:8]

    # Calculate expiry
    intent = get_intent(intent_id)
    expires_at = intent.expires_at.isoformat() if intent else None

    return {
        "intent_id": intent_id,
        "from_mint": from_mint,
        "to_mint": to_mint,
        "in_amount": amount,
        "out_amount_est": f"{out_amount_ui:.6f}".rstrip("0").rstrip("."),
        "price_impact_pct": order.get("priceImpact", 0),
        "route_summary": f"{from_symbol} -> {to_symbol}",
        "expires_at": expires_at,
        "policy_checks_passed": policy_result.checks_passed,
    }


async def solana_swap_confirm(intent_id: str) -> dict[str, Any]:
    """
    Execute a previously quoted intent.

    Args:
        intent_id: UUID from solana_quote

    Returns:
        Dict with success, signature, amounts, and explorer_url
    """
    # Get the intent
    intent = get_intent(intent_id)

    if not intent:
        return {"error": "Intent not found or expired. Please create a new quote."}

    if intent.executed:
        return {"error": "Intent already executed. Each quote can only be used once."}

    # Get user's keypair for signing
    keypair = get_keypair()
    if not keypair:
        return {"error": "No wallet configured. Set SOLANA_PRIVATE_KEY."}

    # Sign the transaction
    ultra_client = JupiterUltraClient(api_key=get_jupiter_api_key())
    signed_tx = ultra_client.sign_transaction(intent.unsigned_tx, keypair)

    # Execute the swap
    result = await ultra_client.execute_swap(signed_tx, intent.request_id)

    # Mark intent as executed (prevent replay)
    mark_executed(intent_id)

    status = result.get("status")
    signature = result.get("signature", "")

    if status == "Success":
        # Calculate actual output amount
        out_decimals = get_token_decimals(intent.to_mint)
        out_amount_atomic = int(result.get("outputAmountResult", 0))
        out_amount_ui = out_amount_atomic / (10**out_decimals)

        # Record trade for PnL tracking
        try:
            from .strategies import record_trade

            sol_mint = SYMBOL_TO_MINT["SOL"]

            # Determine if this is a buy or sell based on SOL direction
            if intent.from_mint == sol_mint:
                # Buying token with SOL
                action = "buy"
                trade_mint = intent.to_mint
                trade_amount_tokens = out_amount_ui
                # Estimate USD value: input SOL * SOL price
                sol_price = await _get_sol_price_async()
                trade_amount_usd = float(intent.amount) * sol_price
            else:
                # Selling token for SOL
                action = "sell"
                trade_mint = intent.from_mint
                trade_amount_tokens = float(intent.amount)
                # Estimate USD value: output SOL * SOL price
                sol_price = await _get_sol_price_async()
                trade_amount_usd = out_amount_ui * sol_price

            # Get symbol for the traded token
            symbol = _get_symbol_for_mint(trade_mint)

            # Calculate price per token
            price_per_token = trade_amount_usd / trade_amount_tokens if trade_amount_tokens > 0 else 0

            record_trade(
                action=action,
                mint=trade_mint,
                symbol=symbol,
                amount_tokens=trade_amount_tokens,
                amount_usd=trade_amount_usd,
                price_per_token=price_per_token,
                signature=signature,
            )
        except Exception:
            pass  # Don't fail the trade if recording fails

        return {
            "success": True,
            "signature": signature,
            "from_mint": intent.from_mint,
            "to_mint": intent.to_mint,
            "in_amount": intent.amount,
            "out_amount_actual": f"{out_amount_ui:.6f}".rstrip("0").rstrip("."),
            "explorer_url": f"https://solscan.io/tx/{signature}",
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Swap failed"),
            "signature": signature,
            "from_mint": intent.from_mint,
            "to_mint": intent.to_mint,
            "in_amount": intent.amount,
        }


async def quick_trade(
    action: str,
    token: str,
    amount_usd: float,
) -> dict[str, Any]:
    """
    One-step trade with smart defaults and auto-execution.

    This is the easiest way to trade. Just say "buy" or "sell", the token,
    and how much in USD. The tool handles everything else.

    Auto-executes if amount is under your strategy's auto_execute_under_usd.
    Otherwise returns a quote for you to confirm with swap_confirm().

    Args:
        action: "buy" or "sell"
        token: Token symbol (e.g., "BONK") or mint address
        amount_usd: USD amount to trade (e.g., 25.0 for $25)

    Returns:
        If auto-executed: execution result with signature
        If manual needed: quote with intent_id for confirmation

    Example:
        quick_trade("buy", "BONK", 20)  # Buy $20 worth of BONK
        quick_trade("sell", "WIF", 50)  # Sell $50 worth of WIF
    """
    from .strategies import get_active_strategy

    action = action.lower()
    if action not in ("buy", "sell"):
        return {"error": "Action must be 'buy' or 'sell'"}

    # Get current strategy for limits
    strategy = get_active_strategy()

    # Check trade limit
    if amount_usd > strategy.max_trade_usd:
        return {
            "error": f"Trade exceeds limit",
            "amount_usd": amount_usd,
            "max_trade_usd": strategy.max_trade_usd,
            "suggestion": f"Reduce amount to ${strategy.max_trade_usd} or change strategy",
        }

    # Resolve token to mint address
    mint = resolve_token(token)
    if not mint:
        # Try searching
        data_client = JupiterDataClient(api_key=get_jupiter_api_key())
        results = await data_client.search_token(token)
        if results:
            # Jupiter API uses "id" for mint address
            mint = results[0].get("id") or results[0].get("address")
            token_symbol = results[0].get("symbol", token)
        else:
            return {"error": f"Token not found: {token}"}
    else:
        # Get symbol for display
        token_symbol = token.upper() if len(token) < 10 else None
        if not token_symbol:
            data_client = JupiterDataClient(api_key=get_jupiter_api_key())
            info = await data_client.get_token_info(mint)
            token_symbol = info.get("symbol", mint[:8]) if info else mint[:8]

    # SOL mint for trading pairs
    sol_mint = SYMBOL_TO_MINT["SOL"]

    # Set up trade direction
    if action == "buy":
        from_mint = sol_mint
        to_mint = mint
    else:  # sell
        from_mint = mint
        to_mint = sol_mint

    # Get price to calculate amount
    data_client = JupiterDataClient(api_key=get_jupiter_api_key())
    price_data = await data_client.get_price(from_mint)

    if not price_data or not price_data.get("usdPrice"):
        return {"error": f"Could not get price for {from_mint}"}

    price_usd = float(price_data.get("usdPrice", 0))
    if price_usd <= 0:
        return {"error": "Invalid price data"}

    # Calculate token amount from USD
    token_amount = amount_usd / price_usd

    # Run safety check if required and buying (not for known safe tokens)
    if action == "buy" and strategy.require_rugcheck and not is_known_safe_mint(to_mint):
        rugcheck = RugCheckClient()
        check_result = await rugcheck.check_token(to_mint)

        if not check_result.get("is_safe", False):
            return {
                "error": "Safety check failed",
                "token": token_symbol,
                "risk_score": check_result.get("score"),
                "reason": check_result.get("reason", "Token failed rugcheck"),
                "suggestion": "Use set_strategy to disable rugcheck if you want to proceed",
            }

    # Get quote
    quote_result = await solana_quote(
        from_mint=from_mint,
        to_mint=to_mint,
        amount=str(token_amount),
        slippage_bps=strategy.slippage_bps,
    )

    if "error" in quote_result:
        return quote_result

    # Determine if we auto-execute
    should_auto_execute = amount_usd <= strategy.auto_execute_under_usd

    if should_auto_execute:
        # Auto-execute the trade
        exec_result = await solana_swap_confirm(quote_result["intent_id"])

        return {
            "auto_executed": True,
            "action": action,
            "token": token_symbol,
            "amount_usd": amount_usd,
            **exec_result,
        }
    else:
        # Return quote for manual confirmation
        return {
            "auto_executed": False,
            "action": action,
            "token": token_symbol,
            "amount_usd": amount_usd,
            "requires_confirmation": True,
            "message": (
                f"Trade of ${amount_usd} exceeds auto-execute threshold "
                f"(${strategy.auto_execute_under_usd}). "
                f"Call swap_confirm('{quote_result['intent_id']}') to execute."
            ),
            **quote_result,
        }
