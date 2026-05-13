# Security Policy

SlopeSniper is experimental trading software that can interact with real Solana wallets. Treat every security report seriously.

## Supported versions

Security fixes target the `main` branch and the latest tagged release.

## Reporting a vulnerability

Please do **not** disclose vulnerabilities publicly until maintainers have had time to respond.

Report issues through GitHub private vulnerability reporting if available, or open a minimal public issue that says you have a security report without including exploit details.

Include:

- affected version/commit
- platform and install method
- impact summary
- reproduction steps or proof-of-concept, if safe to share privately
- whether any key, token, wallet, or funds may be exposed

## Secret handling policy

The repository must not contain:

- Solana private keys, seed phrases, or wallet backups
- Jupiter/RPC/API keys
- GitHub personal access tokens
- Discord/Slack/webhook URLs
- encoded or obfuscated versions of any secret

Use environment variables, encrypted local config, or GitHub Actions secrets. Encoding is not encryption.

## Trading risk disclaimer

SlopeSniper is not financial advice. Meme coins and on-chain swaps are high risk. Bugs, bad routes, RPC failures, malicious tokens, or user error can cause irreversible loss. Use a dedicated wallet and only deposit funds you can afford to lose.
