# solana_get_wallet

Get wallet balances and token holdings.

## Usage

```python
from slopesniper_skill import solana_get_wallet

# Use configured wallet
wallet = await solana_get_wallet()

# Or specify an address
wallet = await solana_get_wallet("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | str | No | Wallet address (defaults to configured wallet) |

## Returns

```python
{
    "address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "sol_balance": 2.5,
    "sol_value_usd": 245.50,
    "tokens": [
        {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "symbol": "USDC",
            "amount": 100.0,
            "value_usd": 100.0
        }
    ]
}
```

## Examples

### View Own Wallet

```python
wallet = await solana_get_wallet()

print(f"Wallet: {wallet['address'][:8]}...")
print(f"SOL: {wallet['sol_balance']:.4f} (${wallet.get('sol_value_usd', 0):.2f})")

for token in wallet.get('tokens', []):
    print(f"  {token['symbol']}: {token['amount']:.4f}")
```

### Check Any Wallet

```python
whale_address = "SomeWhaleAddress123456789012345678901234567"
wallet = await solana_get_wallet(whale_address)

print(f"Whale has {wallet['sol_balance']:.2f} SOL")
```

### Calculate Total Value

```python
wallet = await solana_get_wallet()

total_usd = wallet.get('sol_value_usd', 0)
for token in wallet.get('tokens', []):
    total_usd += token.get('value_usd', 0)

print(f"Total portfolio value: ${total_usd:.2f}")
```

## Error Handling

```python
wallet = await solana_get_wallet()

if "error" in wallet:
    if "No wallet configured" in wallet['error']:
        print("Set SOLANA_PRIVATE_KEY environment variable")
    else:
        print(f"Error: {wallet['error']}")
```

## Requirements

To use the default wallet (no address parameter), you must set:

```bash
export SOLANA_PRIVATE_KEY="your-base58-private-key"
```
