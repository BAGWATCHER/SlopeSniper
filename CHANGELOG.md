# Changelog

All notable changes to SlopeSniper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/maddefientist/SlopeSniper/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/maddefientist/SlopeSniper/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/maddefientist/SlopeSniper/releases/tag/v0.1.0
