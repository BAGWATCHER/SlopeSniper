"""
AI Trading Agent

Extendable AI layer for intelligent trading decisions.
Uses OpenAI API by default, but can be extended for any LLM.

Example:
    agent = TradingAgent(api_key="sk-...")

    decision = await agent.should_buy(token_info, rugcheck_data)
    if decision["buy"]:
        # execute swap
"""

import json
import aiohttp
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Base class for AI agents. Extend this to use different LLMs."""

    @abstractmethod
    async def query(self, prompt: str, system_prompt: str = None) -> str:
        """Send a query to the LLM and return the response."""
        pass


class OpenAIAgent(BaseAgent):
    """OpenAI GPT agent."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def query(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"OpenAI API error: {resp.status} - {text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]


class TradingAgent:
    """
    AI-powered trading agent for Solana tokens.

    Provides intelligent analysis for:
    - Buy/no-buy decisions
    - Risk assessment
    - Position sizing
    - Exit timing
    """

    SYSTEM_PROMPT = """You are a cryptocurrency trading analyst assistant.
You analyze token data and provide trading recommendations.
Always respond with valid JSON.
Be conservative - when in doubt, recommend NOT buying.
Consider: liquidity, holder distribution, trading volume, risk scores, and red flags."""

    def __init__(self, agent: BaseAgent):
        """
        Initialize trading agent.

        Args:
            agent: LLM agent (OpenAIAgent or custom)
        """
        self.agent = agent

    @classmethod
    def with_openai(cls, api_key: str, model: str = "gpt-4o-mini"):
        """Create agent with OpenAI backend."""
        return cls(OpenAIAgent(api_key=api_key, model=model))

    async def should_buy(
        self,
        token_info: Dict[str, Any],
        rugcheck_data: Dict[str, Any],
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze if a token is worth buying.

        Args:
            token_info: Token data from Jupiter API
            rugcheck_data: Safety data from RugCheck
            additional_context: Any extra info to consider

        Returns:
            {
                "buy": bool,
                "confidence": float (0-1),
                "reasoning": str,
                "risks": list[str],
                "suggested_amount_pct": float (0-100)
            }
        """
        prompt = f"""Analyze this Solana token for a potential buy:

TOKEN INFO:
- Symbol: {token_info.get('symbol', 'Unknown')}
- Name: {token_info.get('name', 'Unknown')}
- Price: ${token_info.get('usdPrice', 0)}
- Market Cap: ${token_info.get('mcap', 0):,.0f}
- Liquidity: ${token_info.get('liquidity', 0):,.0f}
- 24h Volume: ${token_info.get('stats24h', {}).get('buyVolume', 0) + token_info.get('stats24h', {}).get('sellVolume', 0):,.0f}
- Holder Count: {token_info.get('holderCount', 'Unknown')}
- Organic Score: {token_info.get('organicScoreLabel', 'Unknown')}

RUGCHECK DATA:
- Risk Score: {rugcheck_data.get('score', 'Unknown')} (lower is safer, <1000 is good)
- Safe: {rugcheck_data.get('is_safe', False)}
- Issues: {rugcheck_data.get('reason', 'None')}
- Critical Risks: {rugcheck_data.get('critical_risks', [])}

{f"ADDITIONAL CONTEXT: {additional_context}" if additional_context else ""}

Respond with JSON only:
{{
    "buy": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "risks": ["risk1", "risk2"],
    "suggested_amount_pct": 0-100 (percent of normal position size)
}}"""

        response = await self.agent.query(prompt, self.SYSTEM_PROMPT)

        try:
            # Clean response and parse JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "buy": False,
                "confidence": 0,
                "reasoning": f"Failed to parse AI response: {response[:200]}",
                "risks": ["AI response parsing error"],
                "suggested_amount_pct": 0
            }

    async def analyze_exit(
        self,
        entry_price: float,
        current_price: float,
        token_info: Dict[str, Any],
        hold_duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Analyze if it's a good time to exit a position.

        Args:
            entry_price: Price when bought
            current_price: Current token price
            token_info: Current token data
            hold_duration_minutes: How long position has been held

        Returns:
            {
                "sell": bool,
                "sell_percentage": float (0-100),
                "reasoning": str,
                "price_target": float (suggested exit price if holding)
            }
        """
        pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

        prompt = f"""Analyze this position for potential exit:

POSITION:
- Entry Price: ${entry_price:.8f}
- Current Price: ${current_price:.8f}
- PnL: {pnl_pct:+.2f}%
- Hold Duration: {hold_duration_minutes} minutes

CURRENT TOKEN METRICS:
- Market Cap: ${token_info.get('mcap', 0):,.0f}
- Liquidity: ${token_info.get('liquidity', 0):,.0f}
- 5m Price Change: {token_info.get('stats5m', {}).get('priceChange', 0):.2f}%
- 1h Price Change: {token_info.get('stats1h', {}).get('priceChange', 0):.2f}%
- Recent Buy/Sell Ratio: {token_info.get('stats5m', {}).get('numBuys', 0)}/{token_info.get('stats5m', {}).get('numSells', 0)}

Respond with JSON only:
{{
    "sell": true/false,
    "sell_percentage": 0-100,
    "reasoning": "brief explanation",
    "price_target": suggested_target_price_if_holding
}}"""

        response = await self.agent.query(prompt, self.SYSTEM_PROMPT)

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "sell": False,
                "sell_percentage": 0,
                "reasoning": f"Failed to parse: {response[:200]}",
                "price_target": current_price * 1.5
            }

    async def assess_market_conditions(
        self,
        recent_tokens: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze overall market conditions from recent token launches.

        Args:
            recent_tokens: List of recently launched tokens with stats

        Returns:
            {
                "market_sentiment": "bullish" | "bearish" | "neutral",
                "trading_recommended": bool,
                "reasoning": str,
                "suggested_position_size_modifier": float (0.5-2.0)
            }
        """
        # Summarize recent tokens
        summary = []
        for t in recent_tokens[:10]:
            summary.append({
                "symbol": t.get("symbol"),
                "mcap": t.get("mcap"),
                "price_change_1h": t.get("stats1h", {}).get("priceChange", 0)
            })

        prompt = f"""Analyze current Solana memecoin market conditions based on recent launches:

RECENT TOKENS:
{json.dumps(summary, indent=2)}

Assess if this is a good time to be trading memecoins.
Consider: average performance, market momentum, risk levels.

Respond with JSON only:
{{
    "market_sentiment": "bullish" | "bearish" | "neutral",
    "trading_recommended": true/false,
    "reasoning": "brief explanation",
    "suggested_position_size_modifier": 0.5-2.0 (1.0 = normal size)
}}"""

        response = await self.agent.query(prompt, self.SYSTEM_PROMPT)

        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "market_sentiment": "neutral",
                "trading_recommended": True,
                "reasoning": f"Failed to parse: {response[:200]}",
                "suggested_position_size_modifier": 1.0
            }

    async def custom_query(self, prompt: str) -> str:
        """
        Send a custom query to the AI.

        Args:
            prompt: Your question or analysis request

        Returns:
            AI response as string
        """
        return await self.agent.query(prompt, self.SYSTEM_PROMPT)
