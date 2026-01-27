# Using SlopeSniper with Claude Cowork

Claude Cowork runs in a sandboxed VM and can't access local MCP servers. Instead, deploy the SlopeSniper API and call it via WebFetch.

## Quick Deploy (Docker)

```bash
# Clone the repo
git clone https://github.com/BAGWATCHER/SlopeSniper.git
cd SlopeSniper/mcp-extension

# Set your private key
export SOLANA_PRIVATE_KEY="your_base58_key_here"

# Optional: Set API key for security
export SLOPESNIPER_API_KEY="your_secret_api_key"

# Start the API
docker-compose up -d
```

Your API is now running at `http://localhost:8420`

## Expose via Cloudflare Tunnel

```bash
# Install cloudflared if needed
brew install cloudflare/cloudflare/cloudflared

# Create tunnel
cloudflared tunnel create slopesniper
cloudflared tunnel route dns slopesniper trade.yourdomain.com

# Run tunnel
cloudflared tunnel run --url http://localhost:8420 slopesniper
```

## Using in Cowork

Once deployed, tell Cowork:

```
I have a SlopeSniper trading API at https://trade.yourdomain.com

To check my status:
WebFetch https://trade.yourdomain.com/status with header X-API-Key: YOUR_KEY

To buy tokens:
POST to https://trade.yourdomain.com/trade with body {"action":"buy","token":"BONK","amount_usd":25}

To see opportunities:
WebFetch https://trade.yourdomain.com/opportunities
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/status` | Check trading readiness |
| POST | `/trade` | Quick buy/sell |
| GET | `/price/{token}` | Get token price |
| GET | `/search/{query}` | Search tokens |
| GET | `/check/{mint}` | Safety analysis |
| GET | `/wallet` | Wallet balances |
| GET | `/strategy` | Current strategy |
| POST | `/strategy` | Set strategy |
| GET | `/opportunities` | Scan for trades |
| POST | `/natural` | Natural language request |

## Example Cowork Conversation

```
You: "I want to trade Solana tokens autonomously"

Cowork: "I'll use WebFetch to call your SlopeSniper API."
        *fetches https://trade.yourdomain.com/status*
        "Your wallet has 2.5 SOL. Strategy is balanced."

You: "Buy $20 of BONK"

Cowork: *POST to /trade with {"action":"buy","token":"BONK","amount_usd":20}*
        "Bought 1,234,567 BONK for $20. Tx: solscan.io/tx/..."
```

## Natural Language Endpoint

The `/natural` endpoint accepts plain English:

```bash
curl -X POST https://trade.yourdomain.com/natural \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"request": "buy $25 of BONK"}'
```

## Security

1. **Always use HTTPS** (Cloudflare tunnel provides this)
2. **Set an API key** - `SLOPESNIPER_API_KEY` environment variable
3. **Use a dedicated wallet** - Don't use your main holdings
4. **Limit exposure** - Only expose to trusted networks if not using API key
