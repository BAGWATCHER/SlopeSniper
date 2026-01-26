# Trading Tools Overview

SlopeSniper Skill provides 6 tools for safe Solana token trading.

## Tool Summary

| Tool | Purpose | Requires Wallet |
|------|---------|-----------------|
| [`solana_get_price`](get-price.md) | Get token prices | No |
| [`solana_search_token`](search-token.md) | Search for tokens | No |
| [`solana_check_token`](check-token.md) | Safety analysis | No |
| [`solana_get_wallet`](get-wallet.md) | View balances | Yes |
| [`solana_quote`](quote.md) | Get swap quote | Yes |
| [`solana_swap_confirm`](swap-confirm.md) | Execute swap | Yes |

## Information Tools

These tools retrieve information and don't require a configured wallet:

- **solana_get_price** - Real-time USD prices from Jupiter
- **solana_search_token** - Find tokens by name or symbol
- **solana_check_token** - Rugcheck safety analysis

## Trading Tools

These tools require a configured wallet (`SOLANA_PRIVATE_KEY`):

- **solana_get_wallet** - View SOL and token balances
- **solana_quote** - Get swap quote (runs policy checks)
- **solana_swap_confirm** - Execute a quoted swap

## Two-Step Swap Flow

Trading uses a two-step flow for safety:

```
┌─────────────────┐     ┌─────────────────┐
│  solana_quote   │────▶│ Intent Created  │
│                 │     │ (2 min TTL)     │
│ - Policy checks │     └────────┬────────┘
│ - Rugcheck      │              │
│ - Get price     │              ▼
└─────────────────┘     ┌─────────────────┐
                        │ User Confirms   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │solana_swap_     │
                        │    confirm      │
                        │                 │
                        │ - Sign tx       │
                        │ - Execute       │
                        └─────────────────┘
```

## Token Identification

**Symbols** (like "SOL", "USDC") are allowed for:

- `solana_get_price`
- `solana_search_token`

**Mint addresses** are required for:

- `solana_check_token`
- `solana_quote`
- `solana_swap_confirm`

This prevents accidental trades on wrong tokens with similar names.

## Error Handling

All tools return a dict. Check for the `error` key:

```python
result = await solana_quote(...)

if "error" in result:
    print(f"Failed: {result['error']}")
    if "reason" in result:
        print(f"Reason: {result['reason']}")
else:
    print(f"Success: {result}")
```
