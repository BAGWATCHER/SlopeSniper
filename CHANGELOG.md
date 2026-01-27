# Changelog

All notable changes to SlopeSniper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.5] - 2026-01-27

### Fixed
- **Critical: Token decimals** - Now fetches actual decimals from Jupiter API instead of assuming 9
  - Fixes "insufficient funds" errors when selling memecoins (pump.fun uses 6, BONK uses 5)
- **Sell validation** - Checks wallet holdings before attempting to quote
  - Prevents wasted API calls on impossible trades
  - Clear error messages showing available vs requested amounts

### Added
- **Sell all/max** - Use `quick_trade("sell", "TOKEN", "all")` to sell entire position
- **Migration scripts** - Tools for fork-to-main repo merges (`scripts/migrate-to-main-repo.sh`)

## [0.2.4] - 2026-01-27

### Fixed
- **Jupiter Price API V3** - Now uses correct `usdPrice` field (was using deprecated `price`)
- **JupiterDataClient authentication** - Added bundled API key fallback (matches UltraClient)
- **Holdings API parsing** - Correctly handles array-of-accounts response format

### Changed
- Policy checks now use strategy limits (e.g., $100 for balanced) instead of hardcoded $50

## [0.2.3] - 2026-01-27

### Added
- **PnL tracking** - Records trades and calculates realized/unrealized profit/loss
- **Trade history** - `slopesniper history` shows recent trades
- **CLI enhancements**:
  - `slopesniper wallet` - Show wallet and all holdings
  - `slopesniper pnl` - Show portfolio profit/loss
  - `slopesniper export` - Export private key for backup
  - `slopesniper status` - Now shows full wallet, holdings, strategy, config
- **Contribution system** - Auto-reports improvements via GitHub Issues

### Changed
- `slopesniper contribute` no longer requires URL (uses GitHub Issues)

## [0.2.2] - 2026-01-27

### Fixed
- Update command now properly busts pip/uv cache with `--refresh` and `--no-cache-dir` flags

## [0.2.1] - 2026-01-27

### Added
- **User config command**: `slopesniper config` shows current configuration
- **Custom Jupiter API key**: `slopesniper config --set-jupiter-key KEY` for better performance
- Performance tips in `slopesniper status` when using shared API key

### Security
- User's Jupiter API key stored encrypted in `~/.slopesniper/config.enc`
- Key priority: environment variable > user config > bundled key

## [0.2.0] - 2026-01-27

### Added
- **Multi-source scanning**: DexScreener and Pump.fun integration for better token discovery
- **Symbol resolution**: Commands now accept symbols (e.g., `BONK`) instead of requiring mint addresses
- **New CLI commands**:
  - `slopesniper resolve <token>` - Get mint address from symbol
  - `slopesniper scan <filter>` - Filter by trending/new/graduated/pumping
  - `slopesniper update` - Self-update to latest version
  - `slopesniper version` - Show current version
- **Encrypted wallet storage**: Private keys encrypted at rest with machine-specific key
- **Auto-migration**: Existing plaintext wallets automatically encrypted on upgrade

### Changed
- `slopesniper check` now accepts symbols, not just mint addresses
- `slopesniper search` results now include mint addresses, market cap, and price
- Install script now detects updates vs fresh installs

### Security
- Wallet files encrypted with Fernet (AES-128-CBC)
- Encryption key derived from machine fingerprint + random salt (PBKDF2, 100k iterations)
- Wallet directory permissions set to 700, files to 600
- Wallet files are machine-bound (cannot be decrypted on different machine)

### Fixed
- Jupiter API field name (`id` vs `address`) for mint addresses

## [0.1.0] - 2026-01-26

### Added
- Initial release
- Core trading tools: price, search, check, buy, sell, quote, swap_confirm
- Jupiter Ultra API integration for swaps
- Rugcheck integration for token safety analysis
- Trading strategies: conservative, balanced, aggressive, degen
- Auto-execution for trades under threshold
- Two-step confirmation for larger trades
- Auto-generated trading wallet on first run
- Clawdbot skill integration

---

[Unreleased]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.5...HEAD
[0.2.5]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/BAGWATCHER/SlopeSniper/releases/tag/v0.1.0
