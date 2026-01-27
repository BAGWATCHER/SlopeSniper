# export_wallet

Export wallet private key for backup or recovery.

## Usage

```python
from slopesniper_skill import export_wallet

result = await export_wallet()
```

## Parameters

None.

## Returns

```python
{
    "success": True,
    "address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "private_key": "5J3mBb...",  # Base58 encoded
    "format": "base58",
    "WARNING": "YOUR PRIVATE KEY IS SHOWN ABOVE..."
}
```

## Examples

### Backup Your Wallet

```python
result = await export_wallet()

if result["success"]:
    print(f"Address: {result['address']}")
    print(f"Private Key: {result['private_key']}")
    print("\nSave this key securely!")
else:
    print(f"Error: {result['error']}")
```

### Import to Phantom/Solflare

The exported private key (base58 format) can be directly imported into:
- Phantom: Settings > Manage Accounts > Import Private Key
- Solflare: Add Wallet > Import > Private Key
- Backpack: Settings > Import Wallet

## Security Warnings

- **Never share your private key** with anyone
- **Never paste it into websites** - phishing sites steal keys this way
- **Store backups offline** - encrypted USB, paper in a safe, etc.
- Anyone with this key has **full control** of your funds

## Error Handling

```python
result = await export_wallet()

if not result["success"]:
    if "No wallet found" in result.get("error", ""):
        print("Create a wallet first with 'slopesniper status'")
```

## When to Use

| Scenario | Use export_wallet? |
|----------|-------------------|
| Backing up before OS reinstall | Yes |
| Moving to a new machine | Yes |
| Importing to mobile wallet | Yes |
| "Support" asks for your key | NO - it's a scam |
| Website asks for private key | NO - it's phishing |
