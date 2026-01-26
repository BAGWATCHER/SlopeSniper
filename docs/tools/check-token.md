# solana_check_token

Run rugcheck safety analysis on a token.

## Usage

```python
from slopesniper_skill import solana_check_token

result = await solana_check_token("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mint_address` | str | Yes | Token mint address (**not** symbol) |

## Returns

```python
{
    "is_safe": True,
    "score": 450,
    "risk_factors": [],
    "reason": "Token passed rugcheck"
}
```

### Risk Levels

Risk factors include severity levels:

- `[CRITICAL]` - Major red flag
- `[DANGER]` - Significant risk
- `[WARNING]` - Potential concern

## Examples

### Basic Safety Check

```python
result = await solana_check_token("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")

if result['is_safe']:
    print(f"✓ Token is safe (score: {result['score']})")
else:
    print(f"✗ Token is risky: {result['reason']}")
```

### Check Before Trading

```python
async def safe_to_trade(mint: str) -> bool:
    result = await solana_check_token(mint)

    if not result['is_safe']:
        print(f"Token failed safety check: {result['reason']}")
        for risk in result['risk_factors']:
            print(f"  - {risk}")
        return False

    return True

# Usage
if await safe_to_trade(some_mint):
    quote = await solana_quote(...)
```

### Known Safe Tokens

Known safe tokens return immediately without API call:

```python
sol_result = await solana_check_token("So11111111111111111111111111111111111111112")
print(sol_result)
# {'is_safe': True, 'score': 0, 'risk_factors': [], 'reason': 'Known safe token (SOL/USDC/USDT/etc)'}
```

## Known Safe Tokens

These tokens skip rugcheck:

- SOL (wrapped)
- USDC
- USDT
- mSOL
- stSOL
- BONK
- JUP

## Error Handling

```python
result = await solana_check_token("invalid")

if "error" in result:
    print(f"Error: {result['error']}")
# Error: Invalid mint address. Must be a Solana address, not a symbol.
```

!!! warning "Symbols Not Allowed"
    This tool requires a mint address. Use `solana_search_token` first to find the mint.
