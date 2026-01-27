<div align="center">

<img src="logo.jpg" alt="SlopeSniper Logo" width="400">

# SlopeSniper

**Trade Solana tokens with natural language**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[Quick Start](#-quick-start) · [Features](#-features) · [Documentation](#-documentation) · [Contributing](#-contributing)

</div>

---

## What is SlopeSniper?

SlopeSniper is an AI-powered Solana trading assistant. Instead of navigating DEX interfaces, just tell it what you want:

```
"Buy $25 of BONK"
"What's trending right now?"
"Is POPCAT safe to trade?"
"Sell half my WIF position"
```

SlopeSniper handles token resolution, safety checks, quotes, and execution—all through conversation.

---

## Current Status

| Platform | Status | Description |
|----------|--------|-------------|
| **Clawdbot** | ✅ Beta | Natural language trading via Claude Code |
| Claude Desktop (MCP) | 🔜 Coming Soon | Direct integration with Claude Desktop |
| Web API | 🔜 Coming Soon | REST API for custom integrations |

---

## 🚀 Quick Start

### 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/skills/install.sh | bash
```

### 2. Initialize Your Wallet

```bash
slopesniper status
```

On first run, SlopeSniper automatically generates a dedicated trading wallet:

```
{
  "wallet_address": "7xK9mN2...",
  "private_key": "4ZBCvJL...",    <-- SAVE THIS! Only shown once!
  "IMPORTANT": "Send SOL to your wallet address to start trading"
}
```

### 3. Fund Your Wallet

Send SOL to the displayed wallet address. This is your dedicated trading wallet—only deposit what you're willing to trade.

### 4. Start Trading

Talk to Clawdbot:

```
You: "Check my trading status"
You: "Buy $20 of BONK"
You: "What's the price of SOL?"
```

---

## ✨ Features

### Natural Language Trading

No commands to memorize. Just describe what you want:

| You Say | What Happens |
|---------|--------------|
| "Buy $25 of BONK" | Resolves token → safety check → quote → execute |
| "Sell half my WIF" | Calculates 50% of holdings → executes sell |
| "Sell all my POPCAT" | Exits entire position |
| "What's pumping?" | Scans for trending tokens with volume spikes |
| "Is POPCAT safe?" | Runs rugcheck analysis, shows risk factors |
| "What's my PnL?" | Shows realized + unrealized profit/loss |
| "Show my trade history" | Lists recent trades with prices |
| "Set aggressive mode" | Increases trade limits and auto-execution threshold |

### Safety First

- **Rugcheck Integration** - Automatic scam token detection before every trade
- **Two-Step Confirmation** - Large trades require explicit approval
- **Auto-Execute Thresholds** - Only small trades execute automatically
- **Dedicated Wallet** - Auto-generated wallet isolates trading funds

### Trading Strategies

| Strategy | Max Trade | Auto-Execute | Safety Checks |
|----------|-----------|--------------|---------------|
| Conservative | $25 | Under $10 | Required |
| Balanced | $100 | Under $25 | Required |
| Aggressive | $500 | Under $50 | Optional |
| Degen | $1000 | Under $100 | None |

Change anytime: `"Set conservative mode"` or `"Use degen strategy"`

### Smart Execution

```
You: "Buy $20 of BONK"
     ↓
[1] Resolve BONK → mint address
[2] Run rugcheck safety analysis
[3] Get Jupiter quote (best price across all DEXs)
[4] Auto-execute (under $25 threshold)
     ↓
"Bought 1.2M BONK for $20. Tx: solscan.io/tx/..."
```

For trades above your auto-execute threshold, you'll be asked to confirm first.

---

## 📖 Documentation

### CLI Reference

#### Account & Wallet
```bash
slopesniper status              # Full status: wallet, holdings, strategy, config
slopesniper wallet              # Show wallet address and all token holdings
slopesniper export              # Export private key for backup/recovery
slopesniper pnl                 # Show portfolio profit/loss (realized + unrealized)
slopesniper history             # Show recent trade history
slopesniper history 50          # Show last 50 trades
```

#### Trading
```bash
slopesniper price SOL           # Get current token price
slopesniper price BONK          # Get meme coin price
slopesniper buy BONK 25         # Buy $25 of BONK
slopesniper sell WIF 50         # Sell $50 worth of WIF
slopesniper sell WIF all        # Sell entire WIF position
```

#### Token Discovery
```bash
slopesniper search "dog"        # Search for tokens by name
slopesniper check POPCAT        # Run rugcheck safety analysis
slopesniper resolve BONK        # Get mint address from symbol
slopesniper scan                # Scan for trading opportunities
slopesniper scan trending       # Filter: trending tokens
slopesniper scan new            # Filter: newly listed
slopesniper scan graduated      # Filter: graduated from pump.fun
slopesniper scan pumping        # Filter: high volume movers
```

#### Strategy & Config
```bash
slopesniper strategy            # View current strategy
slopesniper strategy aggressive # Change to aggressive mode
slopesniper config              # View current configuration
slopesniper config --set-jupiter-key YOUR_KEY  # Set custom Jupiter API key
slopesniper config --set-rpc mainnet URL       # Set custom RPC endpoint
```

#### Updates & Info
```bash
slopesniper version             # Show current version
slopesniper version --check     # Check for updates
slopesniper update              # Update to latest version
```

### Wallet Management

Your wallet is **encrypted** and stored locally at `~/.slopesniper/wallet.enc`. The encryption is machine-specific—wallet files won't work on other computers.

**View wallet and holdings:**
```bash
slopesniper wallet              # Quick view: address + all token balances
slopesniper status              # Full view: wallet + strategy + config
```

**Export private key:**
```bash
slopesniper export              # Decrypt and display private key for backup
```

**Import an existing wallet:**
Set the `SOLANA_PRIVATE_KEY` environment variable before running any commands. The wallet will be encrypted on first use.

### Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `SOLANA_PRIVATE_KEY` | No | Override auto-generated wallet |
| `SOLANA_RPC_URL` | No | Custom RPC endpoint (defaults to public mainnet) |
| `JUPITER_API_KEY` | No | Your own Jupiter key for higher rate limits |

### Trading Limits

Default limits (Balanced strategy):
- **Max trade size**: $100 per transaction
- **Auto-execute threshold**: $25 (trades under this execute without confirmation)
- **Slippage tolerance**: 1%

Customize with `slopesniper strategy <mode>` or set environment variables:

```bash
export POLICY_MAX_TRADE_USD=200
export POLICY_MAX_SLIPPAGE_BPS=50  # 0.5%
```

---

## 🔐 Security

### What We Do

- **Encrypted Storage** - Private keys encrypted at rest with Fernet (AES-128-CBC)
- **Machine-Bound** - Encryption key derived from machine fingerprint (wallets won't decrypt elsewhere)
- **Isolated Wallet** - Auto-generates a dedicated trading wallet separate from your main holdings
- **Local Only** - Private keys stored only on your machine (`~/.slopesniper/wallet.enc`)
- **No Key Exposure** - Private keys never sent to any API or logged
- **Rugcheck Integration** - Every trade runs safety analysis first
- **Two-Step Trades** - Large trades require explicit confirmation

### Best Practices

1. **Use the auto-generated wallet** - Don't import your main wallet
2. **Fund conservatively** - Only deposit what you're actively trading
3. **Start with conservative mode** - Get comfortable before increasing limits
4. **Save your private key** - It's only shown once at wallet creation
5. **Monitor your transactions** - Check Solscan for trade history

### ⚠️ CRITICAL: Backup Your Private Key

Your wallet's private key is **only shown once** when first created. You can retrieve it later with:

```bash
slopesniper export
```

**You MUST back it up OUTSIDE this system:**
- Password manager (1Password, Bitwarden, etc.)
- Encrypted USB drive
- Paper backup in a secure location
- Import into hardware wallet

**Why?** The wallet file (`~/.slopesniper/wallet.enc`) is:
- **Machine-bound** - Won't decrypt on another computer
- **Non-transferable** - If your machine dies, the file is useless

**If you lose your private key and your machine, your funds are GONE FOREVER.**

---

## 🛠️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Clawdbot                           │
│                    (Claude Code)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ Natural Language
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   SlopeSniper CLI                       │
│              slopesniper <command>                      │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Jupiter  │  │ Rugcheck  │  │  Solana   │
│  DEX API  │  │    API    │  │    RPC    │
└───────────┘  └───────────┘  └───────────┘
```

### Components

- **CLI** (`slopesniper`) - Command-line interface for direct execution
- **SDK** - Python library for Jupiter, Rugcheck, and Solana interactions
- **Strategy Engine** - Manages trading limits and auto-execution rules
- **Intent System** - Two-step quote → confirm flow with expiring intents

---

## 🔜 Roadmap

### Recently Shipped (v0.2.x)

- ✅ **Portfolio Tracking** - P&L tracking with `slopesniper pnl`
- ✅ **Trade History** - View past trades with `slopesniper history`
- ✅ **Encrypted Wallets** - Machine-specific encryption at rest
- ✅ **Multi-Source Scanning** - DexScreener + Pump.fun integration
- ✅ **Self-Update** - `slopesniper update` with changelog display

### Coming Soon

- **Claude Desktop Integration** - MCP extension for native Claude Desktop support
- **Web API** - REST endpoints for custom integrations
- **Price Alerts** - Notifications for price movements
- **DCA Automation** - Scheduled recurring buys

### Future Ideas

- Multi-wallet support
- Limit orders
- Copy trading
- Telegram bot interface

---

## 🧪 Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/BAGWATCHER/SlopeSniper.git
cd SlopeSniper

# Install in development mode
cd mcp-extension
uv pip install -e .

# Run tests
pytest

# Run linter
ruff check src/
```

### Project Structure

```
SlopeSniper/
├── config/                 # Public configuration files
├── skills/                 # Clawdbot skill definition
│   ├── install.sh         # One-line installer
│   └── slopesniper/
│       └── SKILL.md       # Skill metadata and docs
├── mcp-extension/         # Main package
│   ├── src/
│   │   ├── slopesniper_skill/    # Core trading logic
│   │   │   ├── cli.py            # CLI entry point
│   │   │   ├── sdk/              # API clients
│   │   │   └── tools/            # Trading tools
│   │   ├── slopesniper_mcp/      # MCP server (coming soon)
│   │   └── slopesniper_api/      # Web API (coming soon)
│   ├── Dockerfile
│   └── pyproject.toml
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to help:

1. **Report Bugs** - Open an issue with reproduction steps
2. **Suggest Features** - Open an issue describing your idea
3. **Submit PRs** - Fork, branch, code, test, PR

Please follow existing code style and include tests for new features.

---

## ⚠️ Disclaimer

SlopeSniper is experimental software for trading volatile assets.

- **Not financial advice** - Do your own research
- **Risk of loss** - Only trade what you can afford to lose
- **No guarantees** - Software may have bugs; trades may fail
- **Meme coins are risky** - Most go to zero

By using SlopeSniper, you acknowledge these risks and take full responsibility for your trades.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for degens, by degens** 🎯

[Report Bug](https://github.com/BAGWATCHER/SlopeSniper/issues) · [Request Feature](https://github.com/BAGWATCHER/SlopeSniper/issues) · [Contribute](https://github.com/BAGWATCHER/SlopeSniper/pulls)

</div>
