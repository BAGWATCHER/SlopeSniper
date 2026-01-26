# Configuration

## Required: Wallet Setup

Set your Solana private key as an environment variable:

```bash
export SOLANA_PRIVATE_KEY="your-base58-private-key"
```

!!! warning "Security"
    Never commit your private key to version control. Use environment variables or a secrets manager.

### Private Key Formats

The skill accepts two formats:

**Base58 (recommended):**
```bash
export SOLANA_PRIVATE_KEY="5abc123..."
```

**JSON Array:**
```bash
export SOLANA_PRIVATE_KEY="[1,2,3,4,...]"
```

## Optional: Jupiter API Key

For higher rate limits, set a Jupiter API key:

```bash
export JUPITER_API_KEY="your-api-key"
```

## Optional: Custom RPC

Use a custom RPC endpoint:

```bash
export SOLANA_RPC_URL="https://your-rpc-provider.com"
```

Default: `https://api.mainnet-beta.solana.com`

## Policy Configuration

Control trading limits via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POLICY_MAX_SLIPPAGE_BPS` | 100 | Max slippage (1%) |
| `POLICY_MAX_TRADE_USD` | 50.0 | Max trade size ($50) |
| `POLICY_MIN_RUGCHECK_SCORE` | 2000 | Max acceptable risk score |
| `POLICY_REQUIRE_MINT_DISABLED` | true | Block if mint authority active |
| `POLICY_REQUIRE_FREEZE_DISABLED` | true | Block if freeze authority active |
| `POLICY_DENY_MINTS` | "" | Comma-separated blocked mints |
| `POLICY_ALLOW_MINTS` | "" | Comma-separated whitelist |

### Example: Conservative Settings

```bash
export POLICY_MAX_SLIPPAGE_BPS=50      # 0.5% max
export POLICY_MAX_TRADE_USD=25.0       # $25 max
export POLICY_MIN_RUGCHECK_SCORE=1000  # Stricter safety
```

### Example: Whitelist Mode

Only allow specific tokens:

```bash
export POLICY_ALLOW_MINTS="So11111111111111111111111111111111111111112,EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
```

## Programmatic Configuration

You can also configure policy in code:

```python
from slopesniper_skill import PolicyConfig, check_policy

config = PolicyConfig(
    MAX_SLIPPAGE_BPS=100,
    MAX_TRADE_USD=50.0,
    DENY_MINTS=["risky-token-mint-address"],
)

result = check_policy(
    from_mint="...",
    to_mint="...",
    amount_usd=25.0,
    slippage_bps=50,
    config=config,
)
```
