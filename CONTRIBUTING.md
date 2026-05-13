# Contributing to SlopeSniper

Thanks for helping improve SlopeSniper. This project touches real wallets and volatile assets, so contributions should favor safety, clear UX, and test coverage over speed.

## Development setup

```bash
git clone https://github.com/optimizedwf/SlopeSniper.git
cd SlopeSniper
python -m pip install --upgrade pip
python -m pip install -e "mcp-extension[dev]"

# Run the test suite
pytest

# Lint and format
ruff check mcp-extension/src tests
ruff format mcp-extension/src tests

# Build the package
python -m build mcp-extension
```

## Pull request checklist

- Open a focused feature branch from `main`.
- Add or update tests for behavior changes.
- Do not commit private keys, wallet files, API keys, webhook URLs, RPC tokens, or generated local config.
- Keep trading changes conservative by default; risky behavior must require explicit opt-in.
- Update README/docs when commands, config, security behavior, or user-visible output changes.
- Run `pytest`, `ruff check`, and `python -m build mcp-extension` before opening a PR.

## Security-sensitive changes

Please be extra careful with:

- wallet creation/import/export
- transaction signing and swap confirmation
- token safety/rugcheck logic
- RPC/Jupiter API key handling
- contribution callbacks, webhooks, and GitHub automation

Never hide secrets in source using encoding, obfuscation, or remote public config. If a feature needs a credential, load it from environment variables, encrypted local user config, or GitHub Actions secrets.

## Reporting vulnerabilities

Do **not** open a public issue for vulnerabilities involving key leakage, fund loss, auth bypass, or unsafe trade execution. Follow [SECURITY.md](SECURITY.md).
