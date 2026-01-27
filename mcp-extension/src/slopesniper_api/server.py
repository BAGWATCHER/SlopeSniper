"""
SlopeSniper Web API - For Claude Cowork and external access.

Deploy this to your server and call via WebFetch from Cowork.
"""

from __future__ import annotations

import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import skill functions
from slopesniper_skill import (
    solana_get_price,
    solana_search_token,
    solana_check_token,
    solana_get_wallet,
    solana_quote,
    solana_swap_confirm,
    quick_trade,
    get_status,
    setup_wallet,
    set_strategy,
    get_strategy,
    list_strategies,
    scan_opportunities,
    watch_token,
    get_watchlist,
)


# API Key authentication
API_KEY = os.environ.get("SLOPESNIPER_API_KEY", "")


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key if configured."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("🚀 SlopeSniper API starting...")
    yield
    print("👋 SlopeSniper API shutting down...")


app = FastAPI(
    title="SlopeSniper API",
    description="Solana token trading via Jupiter DEX",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class TradeRequest(BaseModel):
    action: str  # "buy" or "sell"
    token: str  # Token symbol or mint
    amount_usd: float  # USD amount


class QuoteRequest(BaseModel):
    from_mint: str
    to_mint: str
    amount: str
    slippage_bps: int = 50


class ConfirmRequest(BaseModel):
    intent_id: str


class StrategyRequest(BaseModel):
    strategy: Optional[str] = None
    max_trade_usd: Optional[float] = None
    auto_execute_under_usd: Optional[float] = None
    slippage_bps: Optional[int] = None
    require_rugcheck: Optional[bool] = None


class WatchRequest(BaseModel):
    mint: str
    alert_on: str = "10% change"


class NaturalRequest(BaseModel):
    request: str  # Natural language request


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "service": "SlopeSniper API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": [
            "/status",
            "/trade",
            "/quote",
            "/confirm",
            "/price/{token}",
            "/search/{query}",
            "/check/{mint}",
            "/wallet",
            "/strategy",
            "/opportunities",
            "/natural",
            "/config/jup",
        ],
    }


# ============================================================================
# Config Endpoints (DEPRECATED - use GitHub-hosted config)
# ============================================================================

# NOTE: Jupiter API key is now served from GitHub, not this server.
# This endpoint is kept for backwards compatibility but requires env var.
# Config URL: https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/jup.json


@app.get("/config/jup")
async def get_jupiter_config(
    x_slopesniper_client: str = Header(None, alias="X-SlopeSniper-Client")
):
    """
    DEPRECATED: Config is now hosted on GitHub.

    This endpoint redirects to the GitHub-hosted config.
    Direct your client to fetch from:
    https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/jup.json
    """
    return {
        "error": "deprecated",
        "message": "Config moved to GitHub",
        "config_url": "https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/jup.json",
    }


@app.get("/status", dependencies=[Depends(verify_api_key)])
async def api_get_status():
    """Check if SlopeSniper is ready to trade."""
    return await get_status()


@app.post("/trade", dependencies=[Depends(verify_api_key)])
async def api_trade(req: TradeRequest):
    """Execute a quick trade."""
    return await quick_trade(req.action, req.token, req.amount_usd)


@app.post("/quote", dependencies=[Depends(verify_api_key)])
async def api_quote(req: QuoteRequest):
    """Get a swap quote."""
    return await solana_quote(req.from_mint, req.to_mint, req.amount, req.slippage_bps)


@app.post("/confirm", dependencies=[Depends(verify_api_key)])
async def api_confirm(req: ConfirmRequest):
    """Confirm and execute a quoted swap."""
    return await solana_swap_confirm(req.intent_id)


@app.get("/price/{token}", dependencies=[Depends(verify_api_key)])
async def api_get_price(token: str):
    """Get current price for a token."""
    return await solana_get_price(token)


@app.get("/search/{query}", dependencies=[Depends(verify_api_key)])
async def api_search_token(query: str):
    """Search for tokens by name/symbol."""
    return await solana_search_token(query)


@app.get("/check/{mint}", dependencies=[Depends(verify_api_key)])
async def api_check_token(mint: str):
    """Run safety analysis on a token."""
    return await solana_check_token(mint)


@app.get("/wallet", dependencies=[Depends(verify_api_key)])
async def api_get_wallet(address: Optional[str] = None):
    """Get wallet balances."""
    return await solana_get_wallet(address)


@app.get("/strategy", dependencies=[Depends(verify_api_key)])
async def api_get_strategy():
    """Get current trading strategy."""
    return await get_strategy()


@app.post("/strategy", dependencies=[Depends(verify_api_key)])
async def api_set_strategy(req: StrategyRequest):
    """Set trading strategy."""
    return await set_strategy(
        strategy=req.strategy,
        max_trade_usd=req.max_trade_usd,
        auto_execute_under_usd=req.auto_execute_under_usd,
        slippage_bps=req.slippage_bps,
        require_rugcheck=req.require_rugcheck,
    )


@app.get("/strategies", dependencies=[Depends(verify_api_key)])
async def api_list_strategies():
    """List all available strategy presets."""
    return await list_strategies()


@app.get("/opportunities", dependencies=[Depends(verify_api_key)])
async def api_scan_opportunities(
    filter: str = "all",
    min_liquidity_usd: float = 50000,
    limit: int = 10,
):
    """Scan for trading opportunities."""
    return await scan_opportunities(
        filter=filter,
        min_liquidity_usd=min_liquidity_usd,
        limit=limit,
    )


@app.post("/watch", dependencies=[Depends(verify_api_key)])
async def api_watch_token(req: WatchRequest):
    """Add token to watchlist."""
    return await watch_token(req.mint, req.alert_on)


@app.get("/watchlist", dependencies=[Depends(verify_api_key)])
async def api_get_watchlist():
    """Get watchlist with current prices."""
    return await get_watchlist()


@app.post("/natural", dependencies=[Depends(verify_api_key)])
async def api_natural(req: NaturalRequest):
    """
    Process a natural language trading request.

    Examples:
    - "buy $20 of BONK"
    - "what's trending"
    - "check my wallet"
    """
    # Import the universal handler from MCP server
    from slopesniper_mcp.server import solana_trading
    return await solana_trading(req.request)


# ============================================================================
# Run with: uvicorn slopesniper_api.server:app --host 0.0.0.0 --port 8420
# ============================================================================


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8420)


if __name__ == "__main__":
    main()
