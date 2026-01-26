# Policy Gates

Policy gates are deterministic safety checks that run **before** any swap execution.

## How It Works

When you call `solana_quote()`, the following checks run automatically:

```
┌─────────────────────────────────────────┐
│           POLICY CHECK FLOW             │
├─────────────────────────────────────────┤
│ 1. Check slippage ≤ MAX_SLIPPAGE_BPS    │
│ 2. Check trade USD ≤ MAX_TRADE_USD      │
│ 3. Check from_mint not in DENY_MINTS    │
│ 4. Check to_mint not in DENY_MINTS      │
│ 5. If ALLOW_MINTS set, check whitelist  │
│ 6. If unknown token, run rugcheck       │
│    - Check score ≤ MIN_RUGCHECK_SCORE   │
│    - Check mint authority disabled      │
│    - Check freeze authority disabled    │
├─────────────────────────────────────────┤
│ All pass? → Create intent               │
│ Any fail? → Return error                │
└─────────────────────────────────────────┘
```

## Configuration

Set via environment variables:

```bash
# Slippage limit (basis points, 100 = 1%)
export POLICY_MAX_SLIPPAGE_BPS=100

# Trade size limit (USD)
export POLICY_MAX_TRADE_USD=50.0

# Rugcheck score limit (lower = safer)
export POLICY_MIN_RUGCHECK_SCORE=2000

# Require authorities disabled
export POLICY_REQUIRE_MINT_DISABLED=true
export POLICY_REQUIRE_FREEZE_DISABLED=true

# Token lists
export POLICY_DENY_MINTS="scam1,scam2"
export POLICY_ALLOW_MINTS="sol,usdc,usdt"
```

Or configure programmatically:

```python
from slopesniper_skill import PolicyConfig, check_policy

config = PolicyConfig(
    MAX_SLIPPAGE_BPS=50,        # 0.5%
    MAX_TRADE_USD=25.0,         # $25
    MIN_RUGCHECK_SCORE=1000,    # Stricter
    DENY_MINTS=["bad-token"],
)

result = check_policy(
    from_mint="...",
    to_mint="...",
    amount_usd=20.0,
    slippage_bps=30,
    rugcheck_result={"score": 500},
    config=config,
)

print(f"Allowed: {result.allowed}")
print(f"Passed: {result.checks_passed}")
print(f"Failed: {result.checks_failed}")
```

## Check Details

### Slippage

Prevents excessive slippage that could result in bad trades.

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_SLIPPAGE_BPS` | 100 | Max 1% slippage |

### Trade Size

Limits maximum USD value per trade.

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_TRADE_USD` | 50.0 | Max $50 per trade |

### Token Lists

Control which tokens can be traded:

- **DENY_MINTS** - Blocked tokens (comma-separated mint addresses)
- **ALLOW_MINTS** - Whitelist mode (if set, only these tokens allowed)

Known safe tokens (SOL, USDC, etc.) bypass the allow list.

### Rugcheck

For unknown tokens, rugcheck analysis runs:

| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_RUGCHECK_SCORE` | 2000 | Max acceptable risk score |
| `REQUIRE_MINT_DISABLED` | true | Block if mint authority active |
| `REQUIRE_FREEZE_DISABLED` | true | Block if freeze authority active |

## PolicyResult

The `check_policy()` function returns a `PolicyResult`:

```python
@dataclass
class PolicyResult:
    allowed: bool              # True if all checks pass
    reason: Optional[str]      # Why blocked (if blocked)
    checks_passed: list[str]   # Checks that passed
    checks_failed: list[str]   # Checks that failed
```

## Example Errors

### Slippage Too High

```python
{
    "error": "Policy blocked",
    "reason": "Policy blocked: slippage (150bps > max 100bps)",
    "checks_passed": ["trade_size ($25.00)"],
    "checks_failed": ["slippage (150bps > max 100bps)"]
}
```

### Trade Too Large

```python
{
    "error": "Policy blocked",
    "reason": "Policy blocked: trade_size ($75.00 > max $50.00)",
    "checks_passed": ["slippage (50bps)"],
    "checks_failed": ["trade_size ($75.00 > max $50.00)"]
}
```

### Token Blocked

```python
{
    "error": "Policy blocked",
    "reason": "Policy blocked: to_mint in DENY_MINTS",
    "checks_passed": ["slippage (50bps)", "trade_size ($25.00)"],
    "checks_failed": ["to_mint in DENY_MINTS"]
}
```
