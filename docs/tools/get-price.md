# solana_get_price

Get current USD price for a token.

## Usage

```python
from slopesniper_skill import solana_get_price

result = await solana_get_price("SOL")
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | str | Yes | Token symbol (e.g., "SOL") or mint address |

## Returns

```python
{
    "mint": "So11111111111111111111111111111111111111112",
    "symbol": "SOL",
    "price_usd": 98.45,
    "market_cap": 45000000000  # Optional
}
```

## Examples

### By Symbol

```python
sol = await solana_get_price("SOL")
print(f"SOL: ${sol['price_usd']:.2f}")
```

### By Mint Address

```python
usdc = await solana_get_price("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
print(f"USDC: ${usdc['price_usd']:.2f}")
```

### With Unknown Token

```python
# Will search for the token first
result = await solana_get_price("bonk")
if "error" in result:
    print(f"Not found: {result['error']}")
else:
    print(f"{result['symbol']}: ${result['price_usd']:.8f}")
```

## Supported Symbols

The following symbols are resolved directly:

- SOL, WSOL
- USDC, USDT
- MSOL, STSOL
- BONK, JUP, WIF, PYTH, RAY

Other symbols will trigger a search via Jupiter API.
