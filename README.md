<div align="center">

<img src="logo.jpg" alt="SlopeSniper logo" width="280">

# SlopeSniper 🦞

**AI-assisted Solana trading from a CLI, Moltbot skill, or MCP-style integration.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/optimizedwf/SlopeSniper/actions/workflows/ci.yml/badge.svg)](https://github.com/optimizedwf/SlopeSniper/actions/workflows/ci.yml)
[![Security Policy](https://img.shields.io/badge/security-policy-informational.svg)](SECURITY.md)

[Quick start](#quick-start) · [Features](#features) · [Safety model](#safety-model) · [Development](#development) · [Disclaimer](#disclaimer)

</div>

---

## What is SlopeSniper?

SlopeSniper is an experimental open-source trading assistant for Solana tokens. It turns natural-language trading intent into a safer execution flow:

1. resolve token symbol or mint
2. check token risk signals
3. request a Jupiter quote
4. enforce local policy limits
5. require confirmation when needed
6. execute with a dedicated wallet

Example intents:

```text
"Buy $25 of BONK"
"Check if POPCAT is safe"
"Sell half my WIF position"
"Show my wallet status"
```

> SlopeSniper is not a custody service, broker, exchange, or financial advisor. You run it locally and remain responsible for every trade.

## Current status

| Interface | Status | Notes |
| --- | --- | --- |
| CLI / Moltbot skill | Beta | Core wallet, quote, safety, and swap flows |
| MCP server | Experimental | Package includes an MCP entry point for local integrations |
| Web API | Experimental | Optional FastAPI wrapper; secure it before exposing anywhere |

## Quick start

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/optimizedwf/SlopeSniper/main/skills/install.sh | bash
```

Or install directly with `uv`:

```bash
uv tool install "slopesniper-mcp @ git+https://github.com/optimizedwf/SlopeSniper.git#subdirectory=mcp-extension"
```

### Set up a dedicated wallet

```bash
slopesniper setup
```

Use a dedicated trading wallet. Do **not** import your main wallet unless you fully understand the risk.

### Optional: configure Jupiter API key

SlopeSniper does not ship public bundled API keys. For better rate limits, use your own key:

```bash
slopesniper config --set-jupiter-key YOUR_JUPITER_KEY
# or
export JUPITER_API_KEY=YOUR_JUPITER_KEY
```

### Start with status and small quotes

```bash
slopesniper status
slopesniper price SOL
slopesniper check BONK
slopesniper buy BONK 10
```

## Features

| Area | Capability |
| --- | --- |
| Natural language skill | Maps conversational requests into trading actions |
| Token discovery | Search, resolve, trending/pumping scans |
| Safety checks | Rugcheck integration, allow/deny lists, mint/freeze authority checks |
| Local policy | Max trade size, slippage limits, confirmation thresholds |
| Wallet isolation | Local encrypted wallet storage and export flow |
| Jupiter execution | Quotes and swaps through Jupiter APIs |
| Developer tooling | Tests, ruff linting, GitHub Actions CI, MkDocs docs |

## CLI examples

```bash
# Account and wallet
slopesniper status
slopesniper wallet
slopesniper export

# Market data
slopesniper price SOL
slopesniper search dog
slopesniper resolve BONK
slopesniper scan trending

# Safety
slopesniper check POPCAT

# Trading
slopesniper buy BONK 25
slopesniper sell WIF 50
slopesniper sell WIF all

# Strategy and config
slopesniper strategy conservative
slopesniper config --set-jupiter-key YOUR_KEY
```

## Safety model

SlopeSniper is designed to fail closed where practical:

- dedicated wallet recommended by default
- encrypted local wallet/config files under `~/.slopesniper/`
- no API keys, webhook tokens, GitHub tokens, seed phrases, or obfuscated secrets committed to the repository
- user-provided Jupiter keys only via environment or encrypted local config
- trade-size and slippage limits before execution
- rugcheck/token policy gates before risky swaps
- confirmation flow for trades above auto-execute thresholds

See [SECURITY.md](SECURITY.md) for vulnerability reporting and secret-handling rules.

## Configuration

| Variable / command | Purpose |
| --- | --- |
| `JUPITER_API_KEY` | Optional Jupiter API key for higher rate limits |
| `SOLANA_RPC_URL` | Optional custom Solana RPC endpoint |
| `SOLANA_PRIVATE_KEY` | Optional wallet override; prefer `slopesniper setup` for normal use |
| `POLICY_MAX_TRADE_USD` | Local max trade size |
| `POLICY_MAX_SLIPPAGE_BPS` | Local slippage cap in basis points |
| `slopesniper config --set-jupiter-key KEY` | Store Jupiter key in encrypted local config |

## Development

```bash
git clone https://github.com/optimizedwf/SlopeSniper.git
cd SlopeSniper
python -m pip install --upgrade pip
python -m pip install -e "mcp-extension[dev]"

pytest
ruff check mcp-extension/src tests
ruff format mcp-extension/src tests
python -m build mcp-extension
```

Project layout:

```text
SlopeSniper/
├── mcp-extension/          # Python package: CLI, MCP server, API wrapper, SDK/tools
├── skills/                 # Moltbot skill metadata and installer
├── docs/                   # MkDocs documentation
├── tests/                  # Unit tests
├── config/                 # Safe public example config only; no secrets
└── .github/workflows/      # CI, docs, publish, release automation
```

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

High-priority contribution areas:

- safer policy defaults and clearer warnings
- better test coverage around signing/confirmation flows
- docs, screenshots, and demo GIFs
- MCP integration hardening
- additional token-risk signals

## Disclaimer

SlopeSniper is experimental software for volatile crypto assets.

- Not financial advice.
- Trades are irreversible.
- Meme coins can go to zero.
- APIs, RPCs, quotes, and transaction submission can fail.
- Bugs or misconfiguration can cause loss of funds.

Only use a dedicated wallet and only deposit funds you can afford to lose.

## License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">

[Report bug](https://github.com/optimizedwf/SlopeSniper/issues) · [Request feature](https://github.com/optimizedwf/SlopeSniper/issues) · [Pull requests](https://github.com/optimizedwf/SlopeSniper/pulls)

<img src="banner.jpg" alt="SlopeSniper banner" width="800">

</div>
