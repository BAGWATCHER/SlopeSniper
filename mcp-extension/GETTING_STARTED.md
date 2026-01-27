# SlopeSniper - Getting Started

## First Time Setup

After installing the extension in Claude Desktop:

### Step 1: Start a conversation

Say one of these to activate trading mode:

```
"Check my trading status"
"Help me trade Solana tokens"
"Start SlopeSniper"
```

### Step 2: Configure your wallet

Claude will guide you through wallet setup:
1. Export private key from Phantom/Solflare
2. Add it to extension settings
3. Restart Claude Desktop

### Step 3: Set your strategy

```
"Set me up as balanced"      # $100 max, safe
"Make me aggressive"         # $500 max, fast
"I want conservative mode"   # $25 max, safest
```

---

## Trading Commands

| Say This | What Happens |
|----------|--------------|
| "Buy $20 of BONK" | Buys $20 worth of BONK |
| "Sell $50 of WIF" | Sells $50 worth of WIF |
| "What's trending?" | Shows hot tokens |
| "Check my wallet" | Shows balances |
| "Is POPCAT safe?" | Runs safety check |
| "What's the price of SOL?" | Gets current price |

---

## Pro Tips

- Trades under your auto-execute limit happen instantly
- Larger trades ask for confirmation
- Say "scan for pumps" to find opportunities
- Say "watch BONK" to add to watchlist

---

## Troubleshooting

**Claude gives generic advice instead of using tools:**

Try being more specific:
- "Use SlopeSniper to check my status"
- "Use the quick_trade tool to buy BONK"

**Wallet not configured error:**

1. Go to Extensions → slopesniper → Configure
2. Add: `SOLANA_PRIVATE_KEY = your_key_here`
3. Restart Claude Desktop
