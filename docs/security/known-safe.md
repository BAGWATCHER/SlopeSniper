# Known Safe Tokens

Certain well-established tokens skip rugcheck verification.

## Why?

- **Performance** - Skip unnecessary API calls
- **Reliability** - These tokens are stable
- **Trust** - Established with high liquidity

## Token List

| Symbol | Mint Address |
|--------|--------------|
| SOL | `So11111111111111111111111111111111111111112` |
| USDC | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| USDT | `Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB` |
| mSOL | `mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So` |
| stSOL | `7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj` |
| BONK | `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263` |
| JUP | `JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN` |

## Behavior

### solana_check_token

Returns immediately without API call:

```python
result = await solana_check_token(
    "So11111111111111111111111111111111111111112"  # SOL
)
# {
#     "is_safe": True,
#     "score": 0,
#     "risk_factors": [],
#     "reason": "Known safe token (SOL/USDC/USDT/etc)"
# }
```

### solana_quote

Skips rugcheck for known safe destinations:

```python
# This won't call rugcheck API
quote = await solana_quote(
    from_mint="...",
    to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    amount="1.0",
)
```

### Policy Checks

Known safe tokens bypass `ALLOW_MINTS` whitelist:

```python
config = PolicyConfig(
    ALLOW_MINTS=["some-random-token"]  # Restrictive whitelist
)

# Still works because USDC is known safe
result = check_policy(
    from_mint="So11111111111111111111111111111111111111112",  # SOL
    to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",   # USDC
    ...
)
# result.allowed = True
```

## Check Programmatically

```python
from slopesniper_skill import is_known_safe_mint, KNOWN_SAFE_MINTS

# Check single mint
if is_known_safe_mint("So11111111111111111111111111111111111111112"):
    print("SOL is known safe")

# See all known safe mints
for mint in KNOWN_SAFE_MINTS:
    print(mint)
```

## Important Notes

!!! warning "Not Financial Advice"
    "Known safe" means these are well-established tokens, not that trading them is risk-free. Prices can still move against you.

!!! info "Updates"
    The known safe list is maintained in the source code. Major tokens may be added in future versions.
