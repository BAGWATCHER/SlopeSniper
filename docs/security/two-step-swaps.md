# Two-Step Swaps

SlopeSniper uses a two-step swap flow for safety.

## Why Two Steps?

1. **Prevents accidental trades** - User must explicitly confirm
2. **Policy enforcement** - Checks run before intent creation
3. **Price visibility** - User sees exact amounts before confirming
4. **Time-bounded** - Stale quotes expire automatically

## The Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     STEP 1: QUOTE                           │
├─────────────────────────────────────────────────────────────┤
│ User calls: solana_quote(from, to, amount)                  │
│                                                             │
│ 1. Validate inputs (mint addresses required)                │
│ 2. Get USD value of trade                                   │
│ 3. Run rugcheck on destination token                        │
│ 4. Run policy checks                                        │
│    - Slippage ≤ limit                                       │
│    - Trade size ≤ limit                                     │
│    - Token not in deny list                                 │
│    - Rugcheck passes                                        │
│ 5. Get quote from Jupiter                                   │
│ 6. Create intent (stored locally)                           │
│ 7. Return intent_id + quote details                         │
│                                                             │
│ Intent expires in 2 minutes                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                   User reviews quote
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    STEP 2: CONFIRM                          │
├─────────────────────────────────────────────────────────────┤
│ User calls: solana_swap_confirm(intent_id)                  │
│                                                             │
│ 1. Load intent from storage                                 │
│ 2. Check not expired (2 min TTL)                            │
│ 3. Check not already executed                               │
│ 4. Sign transaction with user's keypair                     │
│ 5. Submit to Jupiter                                        │
│ 6. Mark intent as executed                                  │
│ 7. Return result with tx signature                          │
└─────────────────────────────────────────────────────────────┘
```

## Intent Storage

Intents are stored in a local SQLite database:

```sql
CREATE TABLE intents (
    intent_id TEXT PRIMARY KEY,
    from_mint TEXT NOT NULL,
    to_mint TEXT NOT NULL,
    amount TEXT NOT NULL,
    slippage_bps INTEGER NOT NULL,
    out_amount_est TEXT NOT NULL,
    unsigned_tx TEXT NOT NULL,
    request_id TEXT NOT NULL,
    created_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    executed INTEGER DEFAULT 0
);
```

Location: `~/.slopesniper/intents.db`

## Time-to-Live (TTL)

Intents expire after **2 minutes**.

Why 2 minutes?
- Crypto prices move fast
- Stale quotes could execute at bad prices
- Forces user to get fresh quote if delayed

## One-Time Execution

Each intent can only be executed once:

```python
# First confirm succeeds
result1 = await solana_swap_confirm(intent_id)
# {"success": True, ...}

# Second confirm fails
result2 = await solana_swap_confirm(intent_id)
# {"error": "Intent already executed. Each quote can only be used once."}
```

## Example Flow

```python
from slopesniper_skill import solana_quote, solana_swap_confirm

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Step 1: Get quote
quote = await solana_quote(
    from_mint=SOL,
    to_mint=USDC,
    amount="0.1",
)

print(f"Quote: {quote['in_amount']} SOL -> {quote['out_amount_est']} USDC")
print(f"Price impact: {quote['price_impact_pct']:.2f}%")
print(f"Expires: {quote['expires_at']}")

# User decides...
if input("Confirm? (y/n): ").lower() == 'y':
    # Step 2: Execute
    result = await solana_swap_confirm(quote['intent_id'])

    if result.get('success'):
        print(f"Done! {result['explorer_url']}")
    else:
        print(f"Failed: {result['error']}")
else:
    print("Cancelled")
```

## Benefits

| Feature | Benefit |
|---------|---------|
| Policy at quote time | Bad trades blocked early |
| User sees amounts | No surprises |
| 2-min expiry | Always fresh prices |
| One-time use | No accidental replays |
| Local storage | Fast, no network needed |
