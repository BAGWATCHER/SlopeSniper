# SlopeSniper for Clawdbot

Trade Solana tokens using natural language through Clawdbot.

## One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/skills/install.sh | bash
```

## Manual Install

### Option 1: Copy the skill folder

```bash
# Clone and copy
git clone https://github.com/maddefientist/SlopeSniper.git
cp -r SlopeSniper/skills/slopesniper ~/.clawdbot/skills/

# Install the Python package
uv pip install "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension"
```

### Option 2: ClawdHub (coming soon)

```bash
clawdhub install slopesniper
```

## Configuration

Add your Solana wallet key to `~/.clawdbot/clawdbot.json`:

```json
{
  "skills": {
    "entries": {
      "slopesniper": {
        "apiKey": "your_base58_private_key_here"
      }
    }
  }
}
```

**Get your private key from:**
- **Phantom**: Settings → Security & Privacy → Export Private Key
- **Solflare**: Settings → Export Private Key

⚠️ **Use a dedicated trading wallet!** Only fund with amounts you're willing to risk.

## Usage

Once installed, just talk naturally:

```
You: check my status
Bot: Your wallet has 2.5 SOL. Strategy: balanced (auto-execute under $25)

You: buy $20 of BONK
Bot: Bought 1,234,567 BONK for $20.00. Tx: solscan.io/tx/abc123...

You: what's trending?
Bot: Hot tokens right now:
     - WIF: +45% (24h), $2.1B mcap
     - POPCAT: +23% (24h), $890M mcap
     ...
```

## Features

- **Natural language trading** - Just say what you want
- **Auto-execution** - Small trades execute automatically
- **Safety checks** - Rugcheck integration blocks scam tokens
- **Multiple strategies** - Conservative to degen modes
- **Opportunity scanning** - Find trending tokens
- **Encrypted wallets** - Private keys encrypted at rest
- **PnL tracking** - Track your profit/loss
- **Export/backup** - `slopesniper export` reveals key for backup
- **Self-update** - `slopesniper update` keeps you current

## Commands

| Command | Action |
|---------|--------|
| `buy $X of TOKEN` | Purchase tokens |
| `sell $X of TOKEN` | Sell tokens |
| `sell all TOKEN` | Exit entire position |
| `check status` | View wallet & holdings |
| `show wallet` | View all token balances |
| `export key` | Backup private key |
| `what's my PnL` | Show profit/loss |
| `trade history` | Show recent trades |
| `set aggressive mode` | Change strategy |
| `what's trending` | Scan for opportunities |
| `is TOKEN safe` | Run safety check |

## Requirements

- [Clawdbot](https://clawd.bot) installed and running
- [uv](https://github.com/astral-sh/uv) package manager
- Solana wallet with SOL for trading

## Support

- [GitHub Issues](https://github.com/maddefientist/SlopeSniper/issues)
- [Documentation](https://github.com/maddefientist/SlopeSniper)
