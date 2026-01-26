# SlopeSniper Skill

**Safe Solana token trading for Claude Code with policy-enforced two-step swaps.**

[![CI](https://github.com/slopesniper/slopesniper-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/slopesniper/slopesniper-skill/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/slopesniper-skill.svg)](https://badge.fury.io/py/slopesniper-skill)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

SlopeSniper Skill provides Claude Code with the ability to safely trade tokens on Solana. It features:

- **Two-Step Swaps** - Quote → Confirm flow prevents accidental trades
- **Policy Gates** - Configurable limits on slippage, trade size, and token safety
- **Rugcheck Integration** - Automatic safety analysis before trading
- **Jupiter Aggregation** - Best prices across all Solana DEXs

## Quick Example

```python
from slopesniper_skill import solana_get_price, solana_quote, solana_swap_confirm
import asyncio

async def main():
    # Check price
    price = await solana_get_price("SOL")
    print(f"SOL: ${price['price_usd']}")

    # Get a quote (runs policy checks)
    quote = await solana_quote(
        from_mint="So11111111111111111111111111111111111111112",  # SOL
        to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",   # USDC
        amount="0.1"
    )
    print(f"Quote: {quote['in_amount']} SOL -> {quote['out_amount_est']} USDC")

    # Confirm the swap
    result = await solana_swap_confirm(quote['intent_id'])
    print(f"Swap complete: {result['explorer_url']}")

asyncio.run(main())
```

## Installation

```bash
pip install slopesniper-skill
```

## Features

### 6 Trading Tools

| Tool | Description |
|------|-------------|
| `solana_get_price` | Get real-time token prices |
| `solana_search_token` | Search for tokens by name/symbol |
| `solana_check_token` | Run rugcheck safety analysis |
| `solana_get_wallet` | View wallet balances |
| `solana_quote` | Get swap quote with policy checks |
| `solana_swap_confirm` | Execute a quoted swap |

### Policy Gates

All trades are checked against configurable safety limits:

- **Max Slippage** - Default 1% (100 bps)
- **Max Trade Size** - Default $50 USD
- **Rugcheck Score** - Default max 2000
- **Mint/Freeze Authority** - Block tokens with active authorities
- **Deny/Allow Lists** - Custom token filtering

### Two-Step Swap Flow

```
1. solana_quote()
   ↓ Policy checks run
   ↓ Rugcheck analysis
   ↓ Intent created (2 min TTL)

2. solana_swap_confirm(intent_id)
   ↓ Intent validated
   ↓ Transaction signed
   ↓ Swap executed
```

## Security

- **Private keys** are never logged or passed to the LLM
- **Symbols not allowed** for execution - only mint addresses
- **One-time execution** - Each intent can only be used once
- **2-minute expiry** - Stale quotes automatically expire

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Configuration](getting-started/configuration.md)
- [Tool Reference](tools/overview.md)
- [Security Model](security/policy.md)
