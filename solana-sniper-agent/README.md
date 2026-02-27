# Solana Sniper Agent

AI-powered Solana token trading with Jupiter swaps.

Adds an extendable AI layer (OpenAI/GPT) for intelligent buy/sell decisions.

## Install

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from jupiter_ultra_client import JupiterUltraClient
from jupiter_data_client import JupiterDataClient
from rugcheck_client import RugCheckClient
from agent import TradingAgent

# Initialize
agent = TradingAgent.with_openai("sk-your-api-key")
data = JupiterDataClient()
rugcheck = RugCheckClient()

# Get token data
token_info = await data.get_token_info("TOKEN_ADDRESS")
safety = await rugcheck.check_token("TOKEN_ADDRESS")

# Ask AI if we should buy
decision = await agent.should_buy(token_info, safety)

if decision["buy"]:
    print(f"AI says BUY ({decision['confidence']*100:.0f}% confident)")
    print(f"Reasoning: {decision['reasoning']}")
    # Execute swap...
```

## AI Agent Features

### 1. Buy Analysis
```python
decision = await agent.should_buy(token_info, rugcheck_data)
# Returns:
# {
#     "buy": True/False,
#     "confidence": 0.85,
#     "reasoning": "Strong liquidity, low risk score...",
#     "risks": ["Low holder count"],
#     "suggested_amount_pct": 75
# }
```

### 2. Exit Timing
```python
analysis = await agent.analyze_exit(
    entry_price=0.001,
    current_price=0.002,
    token_info=token_info,
    hold_duration_minutes=30
)
# Returns:
# {
#     "sell": True/False,
#     "sell_percentage": 50,
#     "reasoning": "Good profit, momentum slowing...",
#     "price_target": 0.003
# }
```

### 3. Market Conditions
```python
analysis = await agent.assess_market_conditions(recent_tokens)
# Returns:
# {
#     "market_sentiment": "bullish",
#     "trading_recommended": True,
#     "reasoning": "Recent launches performing well...",
#     "suggested_position_size_modifier": 1.5
# }
```

### 4. Custom Queries
```python
response = await agent.custom_query("Should I ape this 500% gainer?")
```

## Extending the Agent

Use a different LLM by implementing `BaseAgent`:

```python
from agent import BaseAgent, TradingAgent

class ClaudeAgent(BaseAgent):
    async def query(self, prompt: str, system_prompt: str = None) -> str:
        # Call Claude API
        return response

agent = TradingAgent(ClaudeAgent())
```

## Files

| File | Description |
|------|-------------|
| `agent.py` | AI trading agent (extendable) |
| `jupiter_ultra_client.py` | Jupiter swaps |
| `jupiter_data_client.py` | Prices, token info |
| `rugcheck_client.py` | Token safety |
| `example.py` | Usage examples |

## Example Flow

```python
# Full AI-powered snipe
token = "NEW_TOKEN_ADDRESS"

# 1. Gather data
info = await data.get_token_info(token)
safety = await rugcheck.check_token(token)

# 2. AI decision
decision = await agent.should_buy(info, safety)

if decision["buy"]:
    # 3. Size position based on AI confidence
    amount = 10.0 * (decision["suggested_amount_pct"] / 100)

    # 4. Execute
    result = await jupiter.swap_with_retry(
        input_mint=JupiterUltraClient.USDC_MINT,
        output_mint=token,
        amount=int(amount * 1_000_000),
        keypair=wallet
    )
```

## License

MIT
