# Changelog

All notable changes to SlopeSniper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.9] - 2026-01-27

### Added
- **Backward compatibility** - Supports both Moltbot and Clawdbot installations
  - Skill metadata includes both `"moltbot"` and `"clawdbot"` keys
  - Installer checks both `.moltbot` and `.clawdbot` directories
  - Config checks both `MOLTBOT_GATEWAY_URL` and `CLAWDBOT_GATEWAY_URL`

### Changed
- **Rebranded** from Clawdbot to Moltbot (with backward compatibility)

### Security
- Added `_safe_float()` helper for safer API response parsing
- SQLite database now gets `0o600` permissions on creation
- Replaced generic exception handlers with specific types
- Added input validation on user amount parsing
- Truncate long token symbols to prevent overflow

## [0.2.8] - 2026-01-27

### Added
- **Wallet integrity diagnostics** - `slopesniper health --diagnose` for comprehensive wallet checks
  - Machine key status verification
  - Wallet file encryption health
  - Backup availability
  - Environment vs local conflict detection
  - Specific issues and recommendations
- **Wallet restore command** - `slopesniper restore TIMESTAMP` to restore from backup
  - Works with timestamps from `slopesniper export --list-backups`
  - Automatically backs up current wallet before restoring
- **Wallet fingerprint API** - `get_wallet_fingerprint()` for process sync detection
- **Better error messages** - Detailed diagnostics when wallet decryption fails

### Fixed
- **Issue #14**: Users couldn't clear invalid Jupiter API keys
  - Added `slopesniper config --clear jupiter-key`
  - Added `clear_jupiter_key()` MCP tool
- **Issue #15**: Wallet desync between Moltbot/MCP and CLI
  - Added `get_wallet_sync_status()` for mismatch detection
  - Added `wallet_source` field to status output
  - Added `WALLET_MISMATCH_WARNING` when configs differ
- **Issue #16**: Couldn't adjust slippage without changing strategy
  - Added `slopesniper strategy --slippage BPS` (e.g., `--slippage 300` for 3%)
  - Added `slopesniper strategy --max-trade USD`
  - Added `set_slippage()` MCP tool for quick adjustment

### Changed
- `load_local_wallet()` now accepts `raise_on_decrypt_error` parameter for better debugging
- Health check shows more detailed fix options for wallet mismatches
- Troubleshooting docs expanded with wallet recovery procedures

## [0.2.7] - 2026-01-27

### Added
- **Interactive wallet setup** - New `slopesniper setup` command with confirmation
  - Prompts user before creating wallet
  - Requires typing wallet address to confirm backup
  - Clearer private key display
  - `--import-key` flag to import existing wallet
- **Backup reminders** - Status shows reminder if wallet has balance and hasn't been exported
  - Tracks wallet creation and export timestamps
  - Reminds after 7 days without backup

### Changed
- `get_status()` now suggests using `setup` command for new users
- `export` command records timestamp for backup reminder tracking

## [0.2.6] - 2026-01-27

### Added
- **Wallet backup system** - Automatic backups before wallet overwrites
  - Backups stored in `~/.slopesniper/wallet_backups/`
  - Keeps last 10 backups with timestamps
  - Address files for easy identification
- **Backup export commands**:
  - `slopesniper export --list-backups` - List all backed up wallets
  - `slopesniper export --backup TIMESTAMP` - Export specific backup
- **Safe uninstall** - `slopesniper uninstall` with safety confirmations
  - Requires `--confirm` flag
  - Shows wallet address before removal
  - Double confirmation: type "DELETE MY WALLET"
  - `--keep-data` option to preserve wallet/config

### Changed
- `slopesniper export` now shows backup availability info

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
- Moltbot skill integration

---

[Unreleased]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.8...HEAD
[0.2.8]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.7...v0.2.8
[0.2.7]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.6...v0.2.7
[0.2.6]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.5...v0.2.6
[0.2.5]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.4...v0.2.5
[0.2.4]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/BAGWATCHER/SlopeSniper/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/BAGWATCHER/SlopeSniper/releases/tag/v0.1.0
