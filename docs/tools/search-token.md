# solana_search_token

Search for tokens by name or symbol.

## Usage

```python
from slopesniper_skill import solana_search_token

results = await solana_search_token("bonk")
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | str | Yes | Search term (name, symbol, or partial match) |

## Returns

```python
[
    {
        "symbol": "BONK",
        "name": "Bonk",
        "mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "verified": True,
        "liquidity": 15000000.0
    },
    # ... up to 10 results
]
```

## Examples

### Basic Search

```python
results = await solana_search_token("pepe")

for token in results:
    status = "✓" if token['verified'] else "✗"
    print(f"{status} {token['symbol']}: {token['mint'][:16]}...")
```

### Find Mint Address

```python
results = await solana_search_token("BONK")

if results:
    bonk = results[0]
    print(f"BONK mint: {bonk['mint']}")
else:
    print("Token not found")
```

### Check Liquidity

```python
results = await solana_search_token("dog")

for token in results:
    if token.get('liquidity', 0) > 100000:
        print(f"{token['symbol']}: ${token['liquidity']:,.0f} liquidity")
```

## Notes

- Results are limited to top 10 matches
- Use the `verified` field to filter trusted tokens
- Higher `liquidity` generally indicates a more established token
- Always use the `mint` address for trading operations
