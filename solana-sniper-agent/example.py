"""
Solana Sniper Agent - AI-Powered Trading Examples

Shows how to use the AI agent for intelligent trading decisions.
"""

import asyncio
import base58
from solders.keypair import Keypair
from jupiter_ultra_client import JupiterUltraClient
from jupiter_data_client import JupiterDataClient
from rugcheck_client import RugCheckClient
from agent import TradingAgent

# Config
OPENAI_API_KEY = "sk-your-api-key-here"
PRIVATE_KEY = "YOUR_WALLET_PRIVATE_KEY"
TOKEN = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example token


async def example_1_smart_buy():
    """Example 1: AI-assisted buy decision"""
    print("\n=== Example 1: Smart Buy Decision ===\n")

    # Initialize
    agent = TradingAgent.with_openai(OPENAI_API_KEY)
    data_client = JupiterDataClient()
    rugcheck = RugCheckClient()

    # Get token data
    print(f"Fetching data for {TOKEN[:8]}...")
    token_info = await data_client.get_token_info(TOKEN)
    rugcheck_data = await rugcheck.check_token(TOKEN)

    print(f"Token: {token_info.get('symbol')} - ${token_info.get('usdPrice', 0):.8f}")
    print(f"MCap: ${token_info.get('mcap', 0):,.0f}")
    print(f"Rugcheck: {rugcheck_data.get('score')} ({'safe' if rugcheck_data.get('is_safe') else 'risky'})")

    # Ask AI
    print("\nAsking AI for analysis...")
    decision = await agent.should_buy(token_info, rugcheck_data)

    print(f"\nAI Decision: {'BUY' if decision['buy'] else 'PASS'}")
    print(f"Confidence: {decision['confidence']*100:.0f}%")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Risks: {', '.join(decision['risks']) if decision['risks'] else 'None identified'}")
    print(f"Suggested position: {decision['suggested_amount_pct']}% of normal size")


async def example_2_exit_analysis():
    """Example 2: AI-assisted exit timing"""
    print("\n=== Example 2: Exit Timing Analysis ===\n")

    agent = TradingAgent.with_openai(OPENAI_API_KEY)
    data_client = JupiterDataClient()

    # Simulate holding a position
    entry_price = 0.00001
    token_info = await data_client.get_token_info(TOKEN)
    current_price = token_info.get('usdPrice', 0)

    print(f"Entry: ${entry_price:.8f}")
    print(f"Current: ${current_price:.8f}")
    print(f"PnL: {((current_price - entry_price) / entry_price) * 100:+.2f}%")

    # Ask AI
    print("\nAsking AI for exit analysis...")
    analysis = await agent.analyze_exit(
        entry_price=entry_price,
        current_price=current_price,
        token_info=token_info,
        hold_duration_minutes=30
    )

    print(f"\nAI Recommendation: {'SELL' if analysis['sell'] else 'HOLD'}")
    print(f"Sell amount: {analysis['sell_percentage']}%")
    print(f"Reasoning: {analysis['reasoning']}")
    if not analysis['sell']:
        print(f"Price target: ${analysis['price_target']:.8f}")


async def example_3_market_conditions():
    """Example 3: Market sentiment analysis"""
    print("\n=== Example 3: Market Conditions ===\n")

    agent = TradingAgent.with_openai(OPENAI_API_KEY)
    data_client = JupiterDataClient()

    # Get recent tokens
    print("Analyzing market conditions...")
    sample_tokens = [
        await data_client.get_token_info("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"),
        await data_client.get_token_info("EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"),
    ]
    sample_tokens = [t for t in sample_tokens if t]

    analysis = await agent.assess_market_conditions(sample_tokens)

    print(f"\nMarket Sentiment: {analysis['market_sentiment'].upper()}")
    print(f"Trading Recommended: {'Yes' if analysis['trading_recommended'] else 'No'}")
    print(f"Reasoning: {analysis['reasoning']}")
    print(f"Position size modifier: {analysis['suggested_position_size_modifier']}x")


async def example_4_full_snipe():
    """Example 4: Complete AI-powered snipe"""
    print("\n=== Example 4: Full AI Snipe ===\n")

    wallet = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
    agent = TradingAgent.with_openai(OPENAI_API_KEY)
    jupiter = JupiterUltraClient()
    data_client = JupiterDataClient()
    rugcheck = RugCheckClient()

    print(f"Wallet: {wallet.pubkey()}")

    # Get data
    print("\n[1/4] Fetching token data...")
    token_info = await data_client.get_token_info(TOKEN)
    rugcheck_data = await rugcheck.check_token(TOKEN)
    print(f"Found: {token_info.get('symbol')} @ ${token_info.get('usdPrice', 0):.8f}")

    # AI analysis
    print("\n[2/4] AI analyzing...")
    decision = await agent.should_buy(token_info, rugcheck_data)
    print(f"AI: {'BUY' if decision['buy'] else 'PASS'} ({decision['confidence']*100:.0f}%)")

    if not decision['buy']:
        print("AI says PASS. Aborting.")
        return

    # Position sizing
    base_amount = 5.0
    adjusted = base_amount * (decision['suggested_amount_pct'] / 100)
    print(f"\n[3/4] Position: ${adjusted:.2f}")

    # Execute (commented for safety)
    print("\n[4/4] Swap ready (uncomment to execute)")
    # result = await jupiter.swap_with_retry(
    #     input_mint=JupiterUltraClient.USDC_MINT,
    #     output_mint=TOKEN,
    #     amount=int(adjusted * 1_000_000),
    #     keypair=wallet
    # )


async def example_5_custom_query():
    """Example 5: Ask AI anything"""
    print("\n=== Example 5: Custom Query ===\n")

    agent = TradingAgent.with_openai(OPENAI_API_KEY)

    query = """
    Token has 500% gain in 5 min, rugcheck 1500, 50 holders, $20k liquidity.
    Ape or trap?
    """

    print("Asking AI...")
    response = await agent.custom_query(query)
    print(f"\n{response}")


if __name__ == "__main__":
    asyncio.run(example_1_smart_buy())
