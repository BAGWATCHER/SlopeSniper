# SlopeSniper - Solana Trading for Claude

Trade Solana tokens directly through Claude Desktop. Just talk naturally:
- "Buy $20 of BONK"
- "What's trending?"
- "Check my wallet"

## Quick Install (One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/maddefientist/SlopeSniper/mcpext/mcp-extension/install.sh | bash
```

Then:
1. **Restart Claude Desktop**
2. **Add your wallet key** (see below)
3. **Start trading!**

---

## Configure Your Wallet

After install, add your Solana private key:

1. Open Claude Desktop
2. Go to **Settings → Developer → MCP Servers**
3. Find **slopesniper** → click **Edit**
4. Add environment variable:
   ```
   SOLANA_PRIVATE_KEY = <your_base58_key>
   ```
5. Restart Claude Desktop

**Get your key from Phantom:**
Settings → Security & Privacy → Export Private Key

⚠️ **Use a dedicated trading wallet** - only fund with amounts you're willing to risk!

---

## Usage Examples

| Say This | What Happens |
|----------|--------------|
| "Check my status" | Shows wallet + strategy |
| "Buy $25 of BONK" | Buys $25 worth of BONK |
| "Sell $50 of WIF" | Sells $50 worth of WIF |
| "What's trending?" | Scans for opportunities |
| "Is POPCAT safe?" | Runs safety check |
| "Set aggressive mode" | Higher limits |

---

## Trading Strategies

| Strategy | Max Trade | Auto-Execute | Rugcheck |
|----------|-----------|--------------|----------|
| Conservative | $25 | Under $10 | Required |
| Balanced | $100 | Under $25 | Required |
| Aggressive | $500 | Under $50 | Disabled |
| Degen | $1000 | Under $100 | Disabled |

Change with: "Set me to balanced" or "Make it aggressive"

---

## Troubleshooting

**Claude doesn't use the tools:**
- Restart Claude Desktop completely (Cmd+Q)
- Start a new conversation
- Say "Check my trading status"

**Wallet not configured:**
- Add `SOLANA_PRIVATE_KEY` in Settings → Developer → MCP Servers

**Need help?**
Open an issue at [github.com/maddefientist/SlopeSniper](https://github.com/maddefientist/SlopeSniper)

---

## Safety Features

- **Two-step swaps**: Quote first, then confirm
- **Policy limits**: Max trade size enforced
- **Rugcheck integration**: Blocks unsafe tokens
- **Auto-execute thresholds**: Only small trades auto-run

Built with [Jupiter](https://jup.ag) • [Rugcheck](https://rugcheck.xyz)
