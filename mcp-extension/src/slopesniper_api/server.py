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


class ContributionReport(BaseModel):
    type: str = "contribution_report"
    instance_id: str
    timestamp: str
    version: str
    platform: str
    files_modified: int
    modifications: list


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
# Contribution Tracking Endpoints (NO AUTH - public for community reports)
# ============================================================================


# In-memory store for contributions (replace with DB in production)
_contributions: list[dict] = []


@app.post("/contributions/report")
async def receive_contribution_report(report: ContributionReport):
    """
    Receive improvement reports from SlopeSniper instances.

    This endpoint collects information about modifications users/AI
    make to SlopeSniper, enabling the maintainers to:
    - Track common improvements
    - Identify bugs being fixed
    - Incorporate popular changes back into the project

    No sensitive data is collected - only file names and change summaries.
    """
    import json
    from datetime import datetime
    from pathlib import Path

    # Store the report
    report_data = {
        "received_at": datetime.now().isoformat(),
        **report.model_dump(),
    }

    _contributions.append(report_data)

    # Also persist to disk for durability
    contributions_file = Path.home() / ".slopesniper" / "received_contributions.jsonl"
    try:
        contributions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(contributions_file, "a") as f:
            f.write(json.dumps(report_data) + "\n")
    except Exception:
        pass

    return {
        "status": "received",
        "message": "Thank you for contributing to SlopeSniper!",
        "report_id": f"{report.instance_id}-{len(_contributions)}",
    }


@app.get("/contributions/stats")
async def get_contribution_stats():
    """Get aggregate statistics about received contributions."""
    from collections import Counter

    if not _contributions:
        return {"total_reports": 0, "unique_instances": 0}

    file_modifications = Counter()
    instances = set()

    for contrib in _contributions:
        instances.add(contrib.get("instance_id"))
        for mod in contrib.get("modifications", []):
            file_modifications[mod.get("file")] += 1

    return {
        "total_reports": len(_contributions),
        "unique_instances": len(instances),
        "most_modified_files": dict(file_modifications.most_common(10)),
    }


# ============================================================================
# Run with: uvicorn slopesniper_api.server:app --host 0.0.0.0 --port 8420
# ============================================================================


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8420)


if __name__ == "__main__":
    main()
