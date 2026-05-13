# SlopeSniper FAQ

Common questions about using SlopeSniper for Solana trading.

---

## General Questions

### What is SlopeSniper?
SlopeSniper is an AI trading assistant that lets you trade Solana tokens using natural language. Tell it what you want in plain English, and it handles token resolution, safety checks, quotes, and execution.

### Do I need coding knowledge?
No! Just install Moltbot and SlopeSniper, then talk to your bot naturally.

### Is it safe?
SlopeSniper includes multiple safety features:
- **Rugcheck integration** - Scans every token before trading
- **Two-step confirmation** - Large trades require approval
- **Auto-execute limits** - Only small trades execute automatically
- **Encrypted wallet** - Your keys are encrypted at rest
- **Dedicated wallet** - Uses a separate wallet from your main holdings

However, **crypto is risky** and meme coins especially so. Only trade what you can afford to lose.

---

## Wallet & Security

### Where are my private keys stored?
**Local file:** `~/.slopesniper/wallet.enc` (encrypted)
**Encryption:** AES-128-CBC with machine-specific key
**Machine-bound:** Wallet file CANNOT be decrypted on another computer

### How do I back up my wallet?
```bash
slopesniper export
```
Save the private key shown in a password manager, on paper in a safe place, or import it into a hardware wallet.

**IMPORTANT:** The encrypted wallet file is useless without your private key. Back it up NOW.

### Can I use my main Solana wallet?
**Not recommended!** Create a dedicated trading wallet:
- Only deposit what you're actively trading
- Limits your exposure if something goes wrong
- Easier to track trading performance

### What if I lose my private key?
**Your funds are gone forever.** There is no recovery. This is why backing up is critical.

### Can I import my existing wallet?
Yes:
```bash
slopesniper setup --import-key YOUR_PRIVATE_KEY
```
Or set the `SOLANA_PRIVATE_KEY` environment variable.

---

## Costs & Fees

### How much SOL do I need?
**Minimum to start:** ~0.1 SOL
- Enough for a few small trades
- Covers gas fees (~$0.01 per transaction)

**Recommended:** 0.5-1 SOL to start

### What are the fees?
1. **Solana network fees** (gas): ~$0.005-0.01 per transaction
2. **Jupiter DEX fees**: 0.3% swap fee (varies by route)
3. **SlopeSniper fees**: None! It's free and open source

### Why did my transaction cost more than expected?
**Slippage** - Price moved between quote and execution. Increase tolerance:
```bash
slopesniper strategy --slippage 300  # 3% instead of 1%
```

---

## Trading

### How do I know what tokens are safe?
Run a safety check:
```bash
slopesniper check BONK
```
Or just ask: `"Is BONK safe to trade?"`

Every trade automatically runs rugcheck before executing.

### Why did my trade fail?
Common reasons:
1. **Insufficient SOL** - Need more for gas fees
2. **Slippage too low** - Price moved, increase tolerance
3. **Token not found** - Verify the symbol or mint address
4. **RPC timeout** - Use a custom RPC endpoint
5. **Rugcheck blocked** - Token flagged as unsafe

### What are the trading strategy modes?
| Strategy | Max Trade | Auto-Execute | Safety |
|----------|-----------|--------------|--------|
| Conservative | $25 | Under $10 | Required |
| Balanced | $100 | Under $25 | Required |
| Aggressive | $500 | Under $50 | Optional |
| Degen | $1000 | Under $100 | None |

Change with: `slopesniper strategy aggressive`

### Can I cancel a trade?
**Before confirmation:** Yes - just don't confirm
**After confirmation:** No - blockchain transactions are final

### How do I sell my entire position?
```bash
slopesniper sell BONK all
```
Or ask: `"Sell all my BONK"`

---

## Performance & Setup

### Commands are slow / timing out
**Problem:** Jupiter API rate limits (especially with 10+ token holdings)

**Solutions:**
1. **Get your own Jupiter API key** (recommended):
   ```bash
   slopesniper config --set-jupiter-key YOUR_KEY
   ```
   Free at: https://station.jup.ag/docs/apis/ultra-api

2. **Use custom RPC:**
   ```bash
   slopesniper config --set-rpc helius YOUR_KEY
   ```

### How do I update SlopeSniper?
```bash
slopesniper update
```
Shows changelog and installs latest version.

### Can I use this on multiple computers?
Your **wallet file is machine-bound** and won't work on other computers. 

To use on another machine:
1. Export your private key: `slopesniper export`
2. On new machine: `slopesniper setup --import-key YOUR_KEY`

---

## Tracking & History

### How do I check my profit/loss?
```bash
slopesniper pnl               # Summary
slopesniper pnl positions     # Per-token breakdown
slopesniper pnl stats         # Win rate, avg gain/loss
```

### How do I see my trade history?
```bash
slopesniper history           # Recent trades
slopesniper history 50        # Last 50 trades
```

### Can I export my trades?
```bash
slopesniper pnl export              # JSON format
slopesniper pnl export --format csv # CSV format
```
Exports saved to: `~/.slopesniper/exports/`

---

## moltbot Integration

### Commands don't work in Moltbot chat
1. **Check SlopeSniper is installed:**
   ```bash
   slopesniper version
   ```

2. **Restart Moltbot gateway:**
   ```bash
   moltbot gateway restart
   ```

3. **Check skill is loaded:**
   Look for "slopesniper" in: `~/.moltbot/skills/` or `~/.clawdbot/skills/`

### Bot says "Unknown command"
SlopeSniper works with **natural language**, not exact commands. Try:
- ❌ `/buy BONK`
- ✅ `buy $20 of BONK`
- ✅ `I want to buy some BONK`

---

## Advanced

### Can I set auto-sell targets?
Yes! (v0.3.0+)
```bash
# Sell at market cap
slopesniper target add BONK --mcap 1000000000 --sell all

# Sell at price
slopesniper target add WIF --price 5.00 --sell 50%

# Sell on % gain
slopesniper target add POPCAT --pct-gain 100 --sell all

# Trailing stop
slopesniper target add TOKEN --trailing 20 --sell all
```

Start monitoring:
```bash
slopesniper daemon start
```

### Can I adjust slippage without changing strategy?
Yes:
```bash
slopesniper strategy --slippage 300     # 3%
slopesniper strategy --max-trade 200    # $200
```

### What RPC endpoints work best?
1. **Helius** - https://helius.dev (paid plans)
2. **Alchemy** - https://alchemy.com (free tier available)
3. **QuickNode** - https://quicknode.com

Configure:
```bash
slopesniper config --set-rpc helius YOUR_KEY
```

---

## Still Have Questions?

**GitHub Issues:** [github.com/optimizedwf/SlopeSniper/issues](https://github.com/optimizedwf/SlopeSniper/issues)

**Documentation:** [github.com/optimizedwf/SlopeSniper](https://github.com/optimizedwf/SlopeSniper)
