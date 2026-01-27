---
name: slopesniper
description: Trade Solana tokens via Jupiter DEX with policy-enforced safety limits
metadata: {"clawdbot":{"requires":{"bins":["uv"],"env":["SOLANA_PRIVATE_KEY"]},"emoji":"🎯","primaryEnv":"SOLANA_PRIVATE_KEY","install":[{"id":"uv","kind":"uv","package":"slopesniper-mcp","from":"git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension","bins":["slopesniper-mcp"],"label":"Install SlopeSniper (uv)"}]}}
user-invocable: true
homepage: https://github.com/maddefientist/SlopeSniper
---

# SlopeSniper - Solana Trading Assistant

You can trade Solana tokens directly. Use natural language - I'll handle the rest.

## Quick Commands

| Say | Action |
|-----|--------|
| "Check my status" | Verify wallet setup |
| "Buy $20 of BONK" | Purchase tokens |
| "Sell $50 of WIF" | Sell tokens |
| "What's trending?" | Find opportunities |
| "Is POPCAT safe?" | Safety check |

## How to Trade

1. **First, check status**: Always verify wallet is configured
2. **For buys**: Specify amount in USD and token name
3. **For sells**: Same format - amount and token

## Trading Strategies

- **Conservative**: $25 max, safety checks required
- **Balanced**: $100 max, moderate limits
- **Aggressive**: $500 max, faster execution
- **Degen**: $1000 max, no safety checks

Say "set aggressive mode" to change.

## Safety Features

- Two-step swaps (quote → confirm)
- Rugcheck integration blocks scam tokens
- Auto-execute only for small trades
- Policy limits enforced

## Tool Usage

Run the SlopeSniper server and call tools:

```bash
# Check status
uv run --directory {baseDir} python -c "
import asyncio
from slopesniper_skill import get_status
print(asyncio.run(get_status()))
"

# Quick trade
uv run --directory {baseDir} python -c "
import asyncio
from slopesniper_skill import quick_trade
print(asyncio.run(quick_trade('buy', 'BONK', 25)))
"
```

## Environment Variables

- `SOLANA_PRIVATE_KEY` - Your wallet private key (required)
- `SOLANA_RPC_URL` - Custom RPC endpoint (optional)
- `JUPITER_API_KEY` - For higher rate limits (optional)

## Security

⚠️ Use a **dedicated trading wallet** - only fund with amounts you're willing to risk!
