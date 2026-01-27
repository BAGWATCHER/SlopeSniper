# configure_rpc

Configure custom RPC endpoint for faster and more reliable transactions.

## Why Upgrade Your RPC?

The default Solana RPC endpoint is free but rate-limited and slower. Premium RPC providers offer:

- **10-100x faster transaction processing**
- **Higher rate limits** (1000s of requests/sec vs 10-20/sec)
- **Better reliability** (99.9% uptime)
- **Priority network access** (your transactions land first)
- **Advanced features** (enhanced APIs, websockets, historical data)

## Supported Providers

### Helius (Recommended)

Fast, reliable, and developer-friendly.

**Free Tier:**
- 1000 requests/sec
- 100GB bandwidth/month
- WebSocket support

**Get API Key:** https://www.helius.dev

**Setup:**
```bash
# CLI
slopesniper config --set-rpc helius YOUR_API_KEY

# Python
from slopesniper_skill.tools.config import set_rpc_config
result = set_rpc_config("helius", "YOUR_API_KEY")
```

**MCP Tool:**
```
configure_rpc("helius", "YOUR_API_KEY")
```

### Quicknode

Enterprise-grade infrastructure with global edge network.

**Free Trial:** 3M API calls/month

**Get Started:** https://www.quicknode.com

**Setup:**
```bash
# CLI - use your FULL endpoint URL
slopesniper config --set-rpc quicknode https://your-endpoint.solana-mainnet.quiknode.pro/your-token/

# Python
set_rpc_config("quicknode", "https://your-endpoint.solana-mainnet.quiknode.pro/your-token/")
```

**MCP Tool:**
```
configure_rpc("quicknode", "https://your-endpoint.solana-mainnet.quiknode.pro/your-token/")
```

### Alchemy

High-performance with excellent analytics and monitoring.

**Free Tier:**
- 300M compute units/month
- Enhanced APIs
- Real-time notifications

**Sign Up:** https://www.alchemy.com

**Setup:**
```bash
# CLI
slopesniper config --set-rpc alchemy YOUR_API_KEY

# Python
set_rpc_config("alchemy", "YOUR_API_KEY")
```

**MCP Tool:**
```
configure_rpc("alchemy", "YOUR_API_KEY")
```

### Custom

Use any Solana RPC endpoint.

**Setup:**
```bash
# CLI
slopesniper config --set-rpc custom https://your-custom-rpc.com

# Python
set_rpc_config("custom", "https://your-custom-rpc.com")
```

## Check Current Configuration

**CLI:**
```bash
slopesniper config
```

**Python:**
```python
from slopesniper_skill.tools.config import get_rpc_config_status

status = get_rpc_config_status()
print(status)
```

**MCP Tool:**
```
get_rpc_status()
```

**Example Output:**
```json
{
  "configured": true,
  "provider": "helius",
  "source": "local_config",
  "url": "https://mainnet.helius-rpc.com/?api-key=abc123...",
  "url_preview": "https://mainnet.helius-rpc.com/?api-key=****"
}
```

## Clear Configuration

Revert to the default Solana RPC endpoint:

**CLI:**
```bash
slopesniper config --clear-rpc
```

**Python:**
```python
from slopesniper_skill.tools.config import clear_rpc_config

result = clear_rpc_config()
```

**MCP Tool:**
```
clear_rpc()
```

## Priority Chain

SlopeSniper checks for RPC configuration in this order:

1. **Environment Variable** (highest priority)
   ```bash
   export SOLANA_RPC_URL=https://your-rpc.com
   ```

2. **User Configuration** (encrypted local storage)
   - Set via `slopesniper config --set-rpc`
   - Stored in `~/.slopesniper/config.enc`

3. **Default** (lowest priority)
   - `https://api.mainnet-beta.solana.com`

## Security

- API keys are stored **encrypted** in `~/.slopesniper/config.enc`
- Keys are bound to your machine (can't be stolen and used elsewhere)
- Only masked previews are shown in status output
- Environment variables take priority (for CI/CD flexibility)

## Validation

Each provider has format validation:

| Provider | Validation |
|----------|------------|
| **helius** | Alphanumeric with hyphens/underscores |
| **quicknode** | Must be `https://` URL containing `quiknode.pro` |
| **alchemy** | Alphanumeric with hyphens/underscores |
| **custom** | Must be valid `http://` or `https://` URL |

## Troubleshooting

### "Invalid API key format"

**Cause:** Key contains invalid characters or is too short

**Fix:**
- Check for extra spaces when copying
- Ensure you copied the full key from provider dashboard
- Keys must be at least 5 characters

### "Invalid Quicknode URL"

**Cause:** URL doesn't match expected format

**Fix:**
- Use the **FULL endpoint URL** from Quicknode dashboard
- Must include `https://` and `quiknode.pro`
- Example: `https://your-endpoint.solana-mainnet.quiknode.pro/your-token/`

### Transactions still slow

**Possible causes:**
1. **Wrong network:** Ensure you're using mainnet endpoint
2. **Rate limits:** Check provider dashboard for usage
3. **Network congestion:** Try switching providers
4. **Local internet:** RPC speed depends on your connection too

**Debug:**
```bash
# Check current RPC
slopesniper config

# Test connectivity
curl -X POST YOUR_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

### Environment variable not working

**Fix:**
```bash
# Verify it's set
echo $SOLANA_RPC_URL

# If empty, set it
export SOLANA_RPC_URL=https://your-rpc.com

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export SOLANA_RPC_URL=https://your-rpc.com' >> ~/.bashrc
source ~/.bashrc
```

## Examples

### Example 1: Upgrade to Helius

```bash
# 1. Get free API key at https://www.helius.dev
# 2. Configure
slopesniper config --set-rpc helius abc-123-def-456

# 3. Verify
slopesniper config

# Output:
# {
#   "rpc": {
#     "configured": true,
#     "provider": "helius",
#     "url_preview": "https://mainnet.helius-rpc.com/?api-key=****"
#   }
# }
```

### Example 2: Try Multiple Providers

```bash
# Try Helius
slopesniper config --set-rpc helius YOUR_KEY
slopesniper price SOL  # Test

# Try Alchemy
slopesniper config --set-rpc alchemy YOUR_KEY
slopesniper price SOL  # Test

# Revert to default
slopesniper config --clear-rpc
```

### Example 3: Claude MCP Integration

When using SlopeSniper through Claude:

**User:** "My transactions are slow, can you speed them up?"

**Claude:**
```
I'll check your current RPC configuration and help upgrade it.

[Calls get_rpc_status()]

You're using the default RPC endpoint. I can configure a premium provider
for faster transactions. Which provider would you like?

1. Helius (fast, free tier available)
2. Quicknode (enterprise-grade)
3. Alchemy (excellent analytics)

Once you get an API key, I can configure it with:
configure_rpc("helius", "your-key-here")
```

## Provider Comparison

| Feature | Helius | Quicknode | Alchemy | Default |
|---------|--------|-----------|---------|---------|
| **Free Tier** | 1000 req/sec | 3M calls/month | 300M compute units | Unlimited* |
| **Speed** | Excellent | Excellent | Excellent | Slow |
| **Uptime** | 99.9% | 99.99% | 99.9% | ~95% |
| **Advanced APIs** | Yes | Yes | Yes | No |
| **WebSockets** | Yes | Yes | Yes | Limited |
| **Support** | Discord | Ticket | Ticket | Community |
| **Best For** | General use | Enterprise | Analytics | Testing only |

\* Default endpoint is free but heavily rate-limited

## Getting API Keys

### Helius
1. Visit https://www.helius.dev
2. Sign up (email + GitHub)
3. Create a new API key
4. Copy the key (starts with your project name)

### Quicknode
1. Visit https://www.quicknode.com
2. Create account
3. Create endpoint → Select Solana Mainnet
4. Copy **full endpoint URL** (not just token)

### Alchemy
1. Visit https://www.alchemy.com
2. Sign up
3. Create app → Select Solana Mainnet
4. Copy API key from dashboard

## Related Tools

- `get_status` - Check overall configuration
- `setup_wallet` - Configure trading wallet
- `set_strategy` - Set trading limits
- `export_wallet` - Backup wallet key

## Best Practices

1. **Start with free tier** - All providers have generous free tiers
2. **Test multiple providers** - Speed varies by region and time
3. **Monitor usage** - Check provider dashboard regularly
4. **Keep keys secure** - Never commit keys to git
5. **Use environment variables** - For production/CI environments
6. **Backup keys** - Store API keys in password manager

## FAQ

**Q: Will this cost money?**
A: All providers have free tiers sufficient for most users. You only pay if you exceed free limits.

**Q: Can I switch providers?**
A: Yes! Just run `slopesniper config --set-rpc` again with a different provider.

**Q: Is my API key safe?**
A: Yes. Keys are encrypted with machine-specific encryption and stored in `~/.slopesniper/config.enc`.

**Q: Which provider is fastest?**
A: Speed varies by location and network load. Helius and Quicknode are both excellent. Try both!

**Q: Do I need this?**
A: If you're experiencing slow transactions or rate limiting, yes. For casual use, the default may be sufficient.

**Q: Can I use my own RPC node?**
A: Yes! Use the "custom" provider with your node's URL.
