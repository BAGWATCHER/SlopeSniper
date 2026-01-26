# solana_quote

Get a swap quote and create an intent. **Does not execute the swap.**

This tool runs policy checks and creates an intent that can be confirmed later.

## Usage

```python
from slopesniper_skill import solana_quote

quote = await solana_quote(
    from_mint="So11111111111111111111111111111111111111112",   # SOL
    to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",    # USDC
    amount="0.1",
    slippage_bps=50,
)
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_mint` | str | Yes | Token to sell (mint address) |
| `to_mint` | str | Yes | Token to buy (mint address) |
| `amount` | str | Yes | Amount to swap (in token units) |
| `slippage_bps` | int | No | Slippage tolerance (default: 50 = 0.5%) |

!!! warning "Mint Addresses Only"
    Symbols like "SOL" are not accepted. Use `solana_search_token` to find mint addresses.

## Returns

### Success

```python
{
    "intent_id": "550e8400-e29b-41d4-a716-446655440000",
    "from_mint": "So11111111111111111111111111111111111111112",
    "to_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "in_amount": "0.1",
    "out_amount_est": "9.84",
    "price_impact_pct": 0.05,
    "route_summary": "SOL -> USDC",
    "expires_at": "2024-01-25T12:05:00Z",
    "policy_checks_passed": ["slippage (50bps)", "trade_size ($9.84)"]
}
```

### Policy Blocked

```python
{
    "error": "Policy blocked",
    "reason": "Policy blocked: trade_size ($150.00 > max $50.00)",
    "checks_passed": ["slippage (50bps)"],
    "checks_failed": ["trade_size ($150.00 > max $50.00)"]
}
```

## Policy Checks

The following checks run automatically:

1. **Slippage** - Must be ≤ configured max (default 100 bps)
2. **Trade Size** - USD value must be ≤ configured max (default $50)
3. **Deny List** - Tokens must not be in deny list
4. **Allow List** - If set, tokens must be in allow list
5. **Rugcheck** - Destination token must pass safety checks

## Examples

### Basic Quote

```python
SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

quote = await solana_quote(from_mint=SOL, to_mint=USDC, amount="0.1")

if "error" in quote:
    print(f"Quote failed: {quote['reason']}")
else:
    print(f"Swap {quote['in_amount']} SOL for ~{quote['out_amount_est']} USDC")
    print(f"Intent ID: {quote['intent_id']}")
    print(f"Expires: {quote['expires_at']}")
```

### With Custom Slippage

```python
quote = await solana_quote(
    from_mint=SOL,
    to_mint=USDC,
    amount="1.0",
    slippage_bps=100,  # 1%
)
```

### Handle Policy Errors

```python
quote = await solana_quote(from_mint=SOL, to_mint=USDC, amount="100")

if "error" in quote:
    print(f"Blocked: {quote['reason']}")
    print(f"Passed: {quote.get('checks_passed', [])}")
    print(f"Failed: {quote.get('checks_failed', [])}")
```

## Intent Expiry

Intents expire after **2 minutes**. This prevents:

- Stale quotes from being executed
- Price changes making trades unfavorable

If an intent expires, create a new quote with `solana_quote`.

## Next Step

Use `solana_swap_confirm(intent_id)` to execute the swap.
