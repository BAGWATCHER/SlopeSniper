<div align="center">

<img src="logo.jpg" alt="SlopeSniper Logo" width="500">

# SlopeSniper Skill

**Safe Solana token trading for Claude Code**

[![CI](https://github.com/slopesniper/slopesniper-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/slopesniper/slopesniper-skill/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/slopesniper-skill.svg)](https://pypi.org/project/slopesniper-skill/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://slopesniper.github.io/slopesniper-skill)

[Documentation](https://slopesniper.github.io/slopesniper-skill) · [PyPI](https://pypi.org/project/slopesniper-skill/) · [Issues](https://github.com/slopesniper/slopesniper-skill/issues)

</div>

---

A Claude Code skill that provides **policy-enforced, two-step token swaps** on Solana via Jupiter aggregator.

## ✨ Features

- **🔒 Two-Step Swaps** - Quote → Confirm flow prevents accidental trades
- **🛡️ Policy Gates** - Configurable limits on slippage, trade size, and token safety
- **🔍 Rugcheck Integration** - Automatic safety analysis before trading
- **⚡ Jupiter Aggregation** - Best prices across all Solana DEXs
- **🔑 Secure** - Private keys never exposed to LLM

## 📦 Installation

```bash
pip install slopesniper-skill
```

## 🚀 Quick Start

```python
import asyncio
from slopesniper_skill import solana_get_price, solana_quote, solana_swap_confirm

async def main():
    # Check price
    price = await solana_get_price("SOL")
    print(f"SOL: ${price['price_usd']:.2f}")

    # Get a quote (runs policy checks)
    quote = await solana_quote(
        from_mint="So11111111111111111111111111111111111111112",
        to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        amount="0.1"
    )
    print(f"Swap: {quote['in_amount']} SOL → {quote['out_amount_est']} USDC")

    # Confirm the swap
    result = await solana_swap_confirm(quote['intent_id'])
    print(f"Done: {result['explorer_url']}")

asyncio.run(main())
```

## 🛠️ Tools

| Tool | Description |
|------|-------------|
| `solana_get_price` | Get real-time token prices |
| `solana_search_token` | Search for tokens by name/symbol |
| `solana_check_token` | Run rugcheck safety analysis |
| `solana_get_wallet` | View wallet balances |
| `solana_quote` | Get swap quote with policy checks |
| `solana_swap_confirm` | Execute a quoted swap |

## ⚙️ Configuration

### Required

```bash
export SOLANA_PRIVATE_KEY="your-base58-private-key"
```

### Optional

```bash
export JUPITER_API_KEY="..."              # Higher rate limits
export SOLANA_RPC_URL="..."               # Custom RPC
```

### Policy Settings

```bash
export POLICY_MAX_SLIPPAGE_BPS=100        # 1% max slippage
export POLICY_MAX_TRADE_USD=50.0          # $50 max per trade
export POLICY_MIN_RUGCHECK_SCORE=2000     # Max risk score
export POLICY_DENY_MINTS="mint1,mint2"    # Blocked tokens
```

## 🔐 Security

- **Private keys** never logged or passed to LLM
- **Symbols blocked** for execution - only mint addresses accepted
- **One-time execution** - Each intent can only be used once
- **2-minute expiry** - Stale quotes automatically expire
- **Policy gates** - All trades checked against configurable limits

## 📖 Documentation

Full documentation at [slopesniper.github.io/slopesniper-skill](https://slopesniper.github.io/slopesniper-skill)

- [Installation Guide](https://slopesniper.github.io/slopesniper-skill/getting-started/installation/)
- [Configuration](https://slopesniper.github.io/slopesniper-skill/getting-started/configuration/)
- [Tool Reference](https://slopesniper.github.io/slopesniper-skill/tools/overview/)
- [Security Model](https://slopesniper.github.io/slopesniper-skill/security/policy/)

## 🧪 Development

```bash
# Clone
git clone https://github.com/slopesniper/slopesniper-skill.git
cd slopesniper-skill

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

<div align="center">

**Built with ❤️ by [SlopeSniper](https://github.com/slopesniper)**

</div>
