# solana_swap_confirm

Execute a previously quoted swap intent.

## Usage

```python
from slopesniper_skill import solana_swap_confirm

result = await solana_swap_confirm("550e8400-e29b-41d4-a716-446655440000")
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `intent_id` | str | Yes | UUID from `solana_quote` |

## Returns

### Success

```python
{
    "success": True,
    "signature": "5xyz123abc...",
    "from_mint": "So11111111111111111111111111111111111111112",
    "to_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "in_amount": "0.1",
    "out_amount_actual": "9.82",
    "explorer_url": "https://solscan.io/tx/5xyz123abc..."
}
```

### Failure

```python
{
    "success": False,
    "error": "Slippage exceeded",
    "signature": "5xyz123abc...",
    "from_mint": "So11111111111111111111111111111111111111112",
    "to_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "in_amount": "0.1"
}
```

### Intent Expired

```python
{
    "error": "Intent not found or expired. Please create a new quote."
}
```

### Already Executed

```python
{
    "error": "Intent already executed. Each quote can only be used once."
}
```

## Examples

### Basic Execution

```python
# Step 1: Get a quote
quote = await solana_quote(
    from_mint="So11111111111111111111111111111111111111112",
    to_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    amount="0.1",
)

if "error" in quote:
    print(f"Quote failed: {quote['error']}")
    exit()

# Step 2: Confirm the swap
result = await solana_swap_confirm(quote['intent_id'])

if result.get('success'):
    print(f"Swapped {result['in_amount']} for {result['out_amount_actual']}")
    print(f"Tx: {result['explorer_url']}")
else:
    print(f"Failed: {result.get('error')}")
```

### With User Confirmation

```python
quote = await solana_quote(...)

print(f"Quote: {quote['in_amount']} -> {quote['out_amount_est']}")
print(f"Impact: {quote['price_impact_pct']:.2f}%")

confirm = input("Execute swap? (y/n): ")
if confirm.lower() != 'y':
    print("Cancelled")
    exit()

result = await solana_swap_confirm(quote['intent_id'])
```

### Error Handling

```python
result = await solana_swap_confirm(intent_id)

if "error" in result:
    error = result['error']

    if "expired" in error:
        print("Quote expired. Getting new quote...")
        quote = await solana_quote(...)

    elif "already executed" in error:
        print("This swap was already completed")

    else:
        print(f"Swap failed: {error}")

elif result.get('success'):
    print(f"Success! {result['explorer_url']}")

else:
    print(f"Transaction failed: {result.get('error')}")
```

## Security Notes

1. **One-Time Use** - Each intent can only be executed once
2. **2-Minute Expiry** - Intents expire quickly to prevent stale executions
3. **Signature Required** - Your private key signs the transaction
4. **No Replay** - Executed intents are marked and cannot be reused

## What Happens

1. Intent is retrieved from local storage
2. Intent validity is checked (not expired, not executed)
3. Transaction is signed with your private key
4. Transaction is submitted to Jupiter
5. Intent is marked as executed
6. Result is returned
