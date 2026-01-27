---
name: slopesniper
description: Trade Solana tokens via Jupiter DEX with auto-execution and safety limits
metadata: {"clawdbot":{"requires":{"bins":["slopesniper"]},"emoji":"🎯","homepage":"https://github.com/BAGWATCHER/SlopeSniper","install":[{"id":"uv-install","kind":"uv","package":"slopesniper-mcp","from":"git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension","bins":["slopesniper"],"label":"Install SlopeSniper via uv"}]}}
user-invocable: true
homepage: https://github.com/BAGWATCHER/SlopeSniper
---

# SlopeSniper - Solana Trading Assistant

Trade Solana meme coins and tokens using natural language. Just tell me what you want to do.

## Examples

| You say | What happens |
|---------|--------------|
| "Check my status" | Shows wallet balance, holdings, and strategy |
| "Show my wallet" | Lists all token holdings with values |
| "Buy $25 of BONK" | Purchases BONK tokens |
| "Sell half my WIF" | Sells 50% of WIF position |
| "Sell all my POPCAT" | Exits entire position |
| "What's my PnL?" | Shows realized + unrealized profit/loss |
| "Show trade history" | Lists recent trades |
| "What's pumping?" | Scans for opportunities |
| "Is POPCAT safe?" | Runs rugcheck analysis |
| "Set aggressive mode" | Changes trading strategy |
| "Export my key" | Shows private key for backup |

## Getting Started

1. **Say "check my status"** - A wallet will be auto-generated on first run
2. **Save your private key** - It's shown once, save it securely!
3. **Fund your wallet** - Send SOL to the displayed address
4. **Start trading!** Just describe what you want in plain English

Optional: Set your own Jupiter API key for 10x better performance:
```bash
slopesniper config --set-jupiter-key YOUR_KEY
```
Get a free key at: https://station.jup.ag/docs/apis/ultra-api

## Trading Strategies

| Strategy | Max Trade | Auto-Execute | Safety Checks |
|----------|-----------|--------------|---------------|
| Conservative | $25 | Under $10 | Required |
| Balanced | $100 | Under $25 | Required |
| Aggressive | $500 | Under $50 | Optional |
| Degen | $1000 | Under $100 | None |

Say "set conservative mode" or "use aggressive strategy" to change.

## How It Works

```
You: "Buy $20 of BONK"
     ↓
[1] Resolve BONK → mint address
[2] Check rugcheck score
[3] Get Jupiter quote
[4] Auto-execute (under threshold)
     ↓
Result: "Bought 1.2M BONK for $20. Tx: solscan.io/tx/..."
```

For trades above your auto-execute threshold, you'll be asked to confirm first.

## Available Commands

### Trading
- `buy $X of TOKEN` - Purchase tokens
- `sell $X of TOKEN` - Sell tokens
- `sell X% of TOKEN` - Sell percentage of holdings
- `sell all TOKEN` - Exit entire position

### Account & Wallet
- `check status` / `am I ready?` - Full status with holdings
- `show wallet` / `my holdings` - View all token balances
- `export key` / `backup wallet` - Show private key for backup
- `what's my PnL?` - Profit/loss summary
- `trade history` - Recent trades

### Information
- `price of TOKEN` - Current price (symbol or mint)
- `search TOKEN` - Find token by name (returns mint addresses)
- `resolve TOKEN` - Get mint address from symbol
- `check TOKEN` / `is TOKEN safe?` - Safety analysis (symbol or mint)

### Strategy
- `set MODE strategy` - Change trading mode
- `what's my strategy?` - View current limits

### Scanning
- `what's trending?` - Find hot tokens
- `scan for opportunities` - Look for trades
- `watch TOKEN` - Add to watchlist

## CLI Commands

Use the `slopesniper` CLI for direct execution:

```bash
# Account & Wallet
slopesniper status              # Full status: wallet, holdings, strategy, config
slopesniper wallet              # Show wallet address and all token holdings
slopesniper export              # Export private key for backup/recovery
slopesniper pnl                 # Show portfolio profit/loss
slopesniper history             # Show recent trade history
slopesniper history 50          # Show last 50 trades

# Trading
slopesniper price SOL           # Get token price
slopesniper price BONK          # Get meme coin price
slopesniper buy BONK 25         # Buy $25 of BONK
slopesniper sell WIF 50         # Sell $50 of WIF
slopesniper sell WIF all        # Sell entire WIF position

# Token Discovery
slopesniper search "dog"        # Search for tokens by name
slopesniper check POPCAT        # Safety check (rugcheck analysis)
slopesniper resolve BONK        # Get mint address from symbol
slopesniper scan                # Scan for all opportunities
slopesniper scan trending       # Scan trending tokens
slopesniper scan new            # Scan new pairs
slopesniper scan graduated      # Scan pump.fun graduates
slopesniper scan pumping        # Scan tokens with price spikes

# Strategy & Config
slopesniper strategy            # View current strategy
slopesniper strategy aggressive # Set aggressive mode
slopesniper config              # View current configuration
slopesniper config --set-jupiter-key KEY  # Set custom API key (10x faster!)
slopesniper config --set-rpc mainnet URL  # Set custom RPC endpoint

# Updates
slopesniper version             # Show current version
slopesniper version --check     # Check for updates
slopesniper update              # Update to latest version (shows changelog)
```

All commands output JSON with mint addresses included for easy chaining.

## Security

- **Use a dedicated wallet** - Only fund with amounts you're willing to lose
- **Start with conservative mode** - Get comfortable before increasing limits
- **Rugcheck integration** - Automatic scam token detection
- **Two-step confirmation** - Large trades require explicit approval

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SOLANA_PRIVATE_KEY` | No | Import existing wallet (auto-generates if not set) |
| `SOLANA_RPC_URL` | No | Custom RPC (defaults to public mainnet) |
| `JUPITER_API_KEY` | No | Your own key for 10x better performance |

**Note:** Wallet and API keys are stored encrypted in `~/.slopesniper/`

## Support

- GitHub: https://github.com/BAGWATCHER/SlopeSniper
- Issues: https://github.com/BAGWATCHER/SlopeSniper/issues
