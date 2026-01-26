# Quick Start

This guide walks you through your first trade with SlopeSniper Skill.

## Prerequisites

1. [Install the package](installation.md)
2. [Configure your wallet](configuration.md)

## Step 1: Check Token Prices

```python
import asyncio
from slopesniper_skill import solana_get_price

async def main():
    # Get SOL price
    sol = await solana_get_price("SOL")
    print(f"SOL: ${sol['price_usd']:.2f}")

    # Get USDC price
    usdc = await solana_get_price("USDC")
    print(f"USDC: ${usdc['price_usd']:.2f}")

asyncio.run(main())
```

## Step 2: View Your Wallet

```python
from slopesniper_skill import solana_get_wallet

async def main():
    wallet = await solana_get_wallet()
    print(f"Address: {wallet['address']}")
    print(f"SOL Balance: {wallet['sol_balance']:.4f}")

    for token in wallet.get('tokens', []):
        print(f"  {token['symbol']}: {token['amount']}")

asyncio.run(main())
```

## Step 3: Search for Tokens

```python
from slopesniper_skill import solana_search_token

async def main():
    results = await solana_search_token("bonk")

    for token in results[:5]:
        print(f"{token['symbol']}: {token['mint']}")
        print(f"  Verified: {token['verified']}")

asyncio.run(main())
```

## Step 4: Check Token Safety

```python
from slopesniper_skill import solana_check_token

async def main():
    # Check BONK safety
    bonk_mint = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    result = await solana_check_token(bonk_mint)

    print(f"Is Safe: {result['is_safe']}")
    print(f"Score: {result['score']}")

    if result['risk_factors']:
        print("Risks:")
        for risk in result['risk_factors']:
            print(f"  - {risk}")

asyncio.run(main())
```

## Step 5: Execute a Swap

```python
from slopesniper_skill import solana_quote, solana_swap_confirm

SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

async def main():
    # Step 1: Get a quote
    quote = await solana_quote(
        from_mint=SOL_MINT,
        to_mint=USDC_MINT,
        amount="0.1",
        slippage_bps=50,
    )

    if "error" in quote:
        print(f"Quote failed: {quote['error']}")
        return

    print(f"Quote: {quote['in_amount']} SOL -> {quote['out_amount_est']} USDC")
    print(f"Price Impact: {quote['price_impact_pct']:.2f}%")
    print(f"Expires: {quote['expires_at']}")

    # Step 2: Confirm the swap
    confirm = input("Confirm swap? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled")
        return

    result = await solana_swap_confirm(quote['intent_id'])

    if result.get('success'):
        print(f"Swap complete!")
        print(f"Received: {result['out_amount_actual']} USDC")
        print(f"View: {result['explorer_url']}")
    else:
        print(f"Swap failed: {result.get('error')}")

asyncio.run(main())
```

## Next Steps

- Learn about [Policy Gates](../security/policy.md)
- Explore all [Trading Tools](../tools/overview.md)
- Understand [Two-Step Swaps](../security/two-step-swaps.md)
