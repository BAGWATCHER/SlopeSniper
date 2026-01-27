#!/usr/bin/env python3
"""
SlopeSniper CLI - Simple command interface for Clawdbot agents.

Usage:
    slopesniper status              Full status: wallet, holdings, strategy, config
    slopesniper wallet              Show wallet address and all token holdings
    slopesniper export              Export private key for backup/recovery
    slopesniper pnl                 Show profit/loss for your portfolio
    slopesniper history [limit]     Show trade history (default: 20 trades)
    slopesniper price <token>       Get token price (symbol or mint)
    slopesniper buy <token> <usd>   Buy tokens
    slopesniper sell <token> <usd>  Sell tokens
    slopesniper check <token>       Safety check (symbol or mint)
    slopesniper search <query>      Search for tokens (returns mint addresses)
    slopesniper resolve <token>     Get mint address from symbol
    slopesniper strategy [name]     View or set strategy
    slopesniper scan [filter]       Scan for opportunities (trending/new/graduated/pumping)
    slopesniper config              View current configuration
    slopesniper config --set KEY VALUE   Set config (jupiter-key, rpc-provider, rpc-url)
    slopesniper config --clear KEY       Clear config (rpc)
    slopesniper contribute          Check for improvements and report to GitHub
    slopesniper contribute --enable       Enable contribution callbacks
    slopesniper contribute --disable      Disable contribution callbacks
    slopesniper update              Update to latest version
    slopesniper version [--check]   Show version (--check for update availability)
"""

from __future__ import annotations

import asyncio
import json
import sys


def print_json(data: dict) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


async def cmd_status() -> None:
    """Full status: wallet, holdings, strategy, and config."""
    from . import get_status, solana_get_wallet, get_strategy
    from .tools.config import get_config_status

    # Get all status info
    status = await get_status()
    wallet = await solana_get_wallet() if status.get("wallet_configured") else {}
    strategy = await get_strategy()
    config = get_config_status()

    result = {
        "wallet": {
            "configured": status.get("wallet_configured", False),
            "address": status.get("wallet_address"),
            "sol_balance": wallet.get("sol_balance"),
            "sol_value_usd": wallet.get("sol_value_usd"),
            "tokens": wallet.get("tokens", []),
        },
        "strategy": {
            "name": strategy.get("name"),
            "max_trade_usd": strategy.get("max_trade_usd"),
            "auto_execute_under_usd": strategy.get("auto_execute_under_usd"),
            "slippage_bps": strategy.get("slippage_bps"),
            "require_rugcheck": strategy.get("require_rugcheck"),
        },
        "config": {
            "jupiter_api_key": config.get("jupiter_api_key_status"),
            "rpc": config.get("rpc"),
        },
        "ready_to_trade": status.get("ready_to_trade", False),
    }
    print_json(result)


async def cmd_wallet() -> None:
    """Show wallet address and holdings."""
    from . import solana_get_wallet
    result = await solana_get_wallet()
    print_json(result)


async def cmd_export() -> None:
    """Export private key for backup/recovery."""
    from . import export_wallet
    result = await export_wallet()
    print_json(result)


async def cmd_pnl() -> None:
    """Show portfolio profit/loss."""
    from . import get_portfolio_pnl
    result = await get_portfolio_pnl()
    print_json(result)


def cmd_history(limit: int = 20) -> None:
    """Show trade history."""
    from . import get_trade_history
    result = get_trade_history(limit=limit)
    print_json({"trades": result, "count": len(result)})


async def cmd_price(token: str) -> None:
    """Get token price."""
    from . import solana_get_price
    result = await solana_get_price(token)
    print_json(result)


async def cmd_buy(token: str, amount_usd: float) -> None:
    """Buy tokens."""
    from . import quick_trade
    result = await quick_trade("buy", token, amount_usd)
    print_json(result)


async def cmd_sell(token: str, amount_usd: float) -> None:
    """Sell tokens."""
    from . import quick_trade
    result = await quick_trade("sell", token, amount_usd)
    print_json(result)


async def cmd_check(token: str) -> None:
    """Run safety check on token."""
    from . import solana_check_token
    result = await solana_check_token(token)
    print_json(result)


async def cmd_search(query: str) -> None:
    """Search for tokens."""
    from . import solana_search_token
    result = await solana_search_token(query)
    print_json(result)


async def cmd_resolve(token: str) -> None:
    """Resolve token symbol to mint address."""
    from . import solana_resolve_token
    result = await solana_resolve_token(token)
    print_json(result)


async def cmd_strategy(name: str | None = None) -> None:
    """View or set trading strategy."""
    if name:
        from . import set_strategy
        result = await set_strategy(name)
    else:
        from . import get_strategy
        result = await get_strategy()
    print_json(result)


async def cmd_scan(filter_type: str = "all") -> None:
    """Scan for trading opportunities."""
    from . import scan_opportunities
    result = await scan_opportunities(filter_type)
    print_json(result)


def cmd_config(
    set_key: str | None = None,
    set_value: str | None = None,
    clear_key: str | None = None,
) -> None:
    """View or update configuration."""
    from .tools.config import (
        get_config_status,
        set_jupiter_api_key,
        set_rpc_config,
        clear_rpc_config,
    )

    if set_key and set_value:
        key_lower = set_key.lower().replace("-", "_").replace(" ", "_")

        if key_lower in ("jupiter_key", "jupiter_api_key", "jup_key", "jup"):
            result = set_jupiter_api_key(set_value)
        elif key_lower in ("rpc_provider", "rpc_type"):
            # For provider, we need a second value - assume custom URL
            result = set_rpc_config(set_value, set_value)
        elif key_lower in ("rpc_url", "rpc", "solana_rpc"):
            result = set_rpc_config("custom", set_value)
        elif key_lower in ("helius", "quicknode", "alchemy"):
            result = set_rpc_config(key_lower, set_value)
        else:
            result = {"error": f"Unknown config key: {set_key}", "valid_keys": [
                "jupiter-key", "rpc-url", "helius", "quicknode", "alchemy"
            ]}
        print_json(result)

    elif clear_key:
        key_lower = clear_key.lower()
        if key_lower in ("rpc", "rpc_url", "rpc_provider"):
            result = clear_rpc_config()
            print_json(result)
        else:
            print_json({"error": f"Cannot clear: {clear_key}", "clearable": ["rpc"]})

    else:
        result = get_config_status()
        print_json(result)


def cmd_version(check_latest: bool = False) -> None:
    """Show current version and optionally check for updates."""
    from . import __version__

    result = {
        "version": __version__,
        "package": "slopesniper-mcp",
        "repo": "https://github.com/maddefientist/SlopeSniper",
        "changelog": "https://github.com/maddefientist/SlopeSniper/blob/main/CHANGELOG.md",
    }

    if check_latest:
        try:
            import urllib.request
            import re

            # Fetch pyproject.toml from GitHub to get latest version
            url = "https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/mcp-extension/pyproject.toml"
            req = urllib.request.Request(url, headers={"User-Agent": "SlopeSniper"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                content = resp.read().decode()
                match = re.search(r'version\s*=\s*"([^"]+)"', content)
                if match:
                    latest = match.group(1)
                    result["latest_version"] = latest
                    result["update_available"] = latest != __version__
                    if latest != __version__:
                        result["update_command"] = "slopesniper update"
        except Exception:
            result["latest_version"] = "unknown (couldn't check)"

    print_json(result)


def cmd_update() -> None:
    """Update to latest version from GitHub."""
    import subprocess

    print("Updating SlopeSniper...")
    print("")

    # Try uv tool first (preferred for CLI tools)
    try:
        result = subprocess.run(
            [
                "uv", "tool", "install",
                "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension",
                "--force",
                "--refresh",  # Bust git cache
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Updated successfully via uv tool!")
            print("")
            print("Run 'slopesniper version' to verify.")
            return
    except FileNotFoundError:
        pass

    # Fallback to uv pip
    try:
        result = subprocess.run(
            [
                "uv", "pip", "install",
                "--force-reinstall",
                "--refresh",  # Bust git cache
                "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension"
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Updated successfully via uv pip!")
            print("")
            print("Run 'slopesniper version' to verify.")
            return
    except FileNotFoundError:
        pass

    # Final fallback to pip
    try:
        result = subprocess.run(
            [
                "pip", "install",
                "--force-reinstall",
                "--no-cache-dir",  # Bust pip cache
                "slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension"
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Updated successfully via pip!")
            print("")
            print("Run 'slopesniper version' to verify.")
            return
    except FileNotFoundError:
        pass

    print_json({
        "error": "Update failed",
        "suggestion": "Try manually: uv tool install 'slopesniper-mcp @ git+https://github.com/maddefientist/SlopeSniper.git#subdirectory=mcp-extension' --force"
    })


def cmd_contribute(
    enable: bool = False,
    disable: bool = False,
) -> None:
    """Manage contribution callbacks and check for improvements."""
    from .integrity import (
        check_and_report,
        enable_contribution_callbacks,
        disable_contribution_callbacks,
    )
    from .tools.config import load_user_config

    if enable:
        # No URL needed - contributions go to GitHub Issues
        result = enable_contribution_callbacks()
        result["method"] = "GitHub Issues"
        result["repo"] = "maddefientist/SlopeSniper"
        print_json(result)
    elif disable:
        result = disable_contribution_callbacks()
        print_json(result)
    else:
        # Run check and report
        result = check_and_report(force=True)

        # Add callback config status
        config = load_user_config() or {}
        result["contribution_method"] = "GitHub Issues"
        result["callbacks_enabled"] = not config.get("contribution_callbacks_disabled", False)

        print_json(result)


def print_help() -> None:
    """Print usage help."""
    print(__doc__)


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print_help()
        return

    cmd = args[0].lower()

    try:
        if cmd == "status":
            asyncio.run(cmd_status())

        elif cmd == "wallet":
            asyncio.run(cmd_wallet())

        elif cmd == "export":
            asyncio.run(cmd_export())

        elif cmd == "pnl":
            asyncio.run(cmd_pnl())

        elif cmd == "history":
            limit = int(args[1]) if len(args) > 1 else 20
            cmd_history(limit)

        elif cmd == "price":
            if len(args) < 2:
                print("Error: price requires <token>")
                sys.exit(1)
            asyncio.run(cmd_price(args[1]))

        elif cmd == "buy":
            if len(args) < 3:
                print("Error: buy requires <token> <usd_amount>")
                sys.exit(1)
            asyncio.run(cmd_buy(args[1], float(args[2])))

        elif cmd == "sell":
            if len(args) < 3:
                print("Error: sell requires <token> <usd_amount>")
                sys.exit(1)
            asyncio.run(cmd_sell(args[1], float(args[2])))

        elif cmd == "check":
            if len(args) < 2:
                print("Error: check requires <token>")
                sys.exit(1)
            asyncio.run(cmd_check(args[1]))

        elif cmd == "search":
            if len(args) < 2:
                print("Error: search requires <query>")
                sys.exit(1)
            asyncio.run(cmd_search(args[1]))

        elif cmd == "resolve":
            if len(args) < 2:
                print("Error: resolve requires <token>")
                sys.exit(1)
            asyncio.run(cmd_resolve(args[1]))

        elif cmd == "strategy":
            name = args[1] if len(args) > 1 else None
            asyncio.run(cmd_strategy(name))

        elif cmd == "scan":
            filter_type = args[1] if len(args) > 1 else "all"
            asyncio.run(cmd_scan(filter_type))

        elif cmd == "config":
            # Parse config flags: --set KEY VALUE or --clear KEY
            set_key = None
            set_value = None
            clear_key = None

            i = 1  # Skip 'config'
            while i < len(args):
                arg = args[i]
                if arg == "--set" and i + 2 < len(args):
                    set_key = args[i + 1]
                    set_value = args[i + 2]
                    i += 3
                elif arg == "--clear" and i + 1 < len(args):
                    clear_key = args[i + 1]
                    i += 2
                # Legacy support
                elif arg == "--set-jupiter-key" and i + 1 < len(args):
                    set_key = "jupiter-key"
                    set_value = args[i + 1]
                    i += 2
                elif arg == "--set-rpc" and i + 2 < len(args):
                    set_key = args[i + 1]  # provider name
                    set_value = args[i + 2]
                    i += 3
                elif arg == "--clear-rpc":
                    clear_key = "rpc"
                    i += 1
                else:
                    i += 1

            cmd_config(set_key=set_key, set_value=set_value, clear_key=clear_key)

        elif cmd == "version":
            check_latest = "--check" in args or "-c" in args
            cmd_version(check_latest=check_latest)

        elif cmd == "update":
            cmd_update()

        elif cmd == "contribute":
            enable = "--enable" in args
            disable = "--disable" in args
            cmd_contribute(enable=enable, disable=disable)

        else:
            print(f"Unknown command: {cmd}")
            print_help()
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
