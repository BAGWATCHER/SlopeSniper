#!/usr/bin/env python3
"""
SlopeSniper CLI - Simple command interface for Clawdbot agents.

Usage:
    slopesniper status              Check wallet and trading readiness
    slopesniper price <token>       Get token price (symbol or mint)
    slopesniper buy <token> <usd>   Buy tokens
    slopesniper sell <token> <usd>  Sell tokens
    slopesniper check <token>       Safety check (symbol or mint)
    slopesniper search <query>      Search for tokens (returns mint addresses)
    slopesniper resolve <token>     Get mint address from symbol
    slopesniper strategy [name]     View or set strategy
    slopesniper scan [filter]       Scan for opportunities (trending/new/graduated/pumping)
    slopesniper config              View current configuration
    slopesniper config --set-jupiter-key KEY   Set your Jupiter API key
    slopesniper config --set-rpc PROVIDER VALUE   Set custom RPC endpoint
    slopesniper config --clear-rpc             Clear custom RPC (use default)
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
    """Check trading status."""
    from . import get_status
    result = await get_status()
    print_json(result)


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
    set_jupiter_key: str | None = None,
    set_rpc_provider: str | None = None,
    set_rpc_value: str | None = None,
    clear_rpc: bool = False,
) -> None:
    """View or update configuration."""
    from .tools.config import (
        get_config_status,
        set_jupiter_api_key,
        set_rpc_config,
        clear_rpc_config,
    )

    if set_jupiter_key:
        result = set_jupiter_api_key(set_jupiter_key)
        print_json(result)
    elif set_rpc_provider and set_rpc_value:
        result = set_rpc_config(set_rpc_provider, set_rpc_value)
        print_json(result)
    elif clear_rpc:
        result = clear_rpc_config()
        print_json(result)
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
            # Parse config flags
            jupiter_key = None
            rpc_provider = None
            rpc_value = None
            clear_rpc = False

            i = 0
            while i < len(args):
                arg = args[i]
                if arg == "--set-jupiter-key" and i + 1 < len(args):
                    jupiter_key = args[i + 1]
                    i += 2
                elif arg == "--set-rpc" and i + 2 < len(args):
                    rpc_provider = args[i + 1]
                    rpc_value = args[i + 2]
                    i += 3
                elif arg == "--clear-rpc":
                    clear_rpc = True
                    i += 1
                else:
                    i += 1

            cmd_config(
                set_jupiter_key=jupiter_key,
                set_rpc_provider=rpc_provider,
                set_rpc_value=rpc_value,
                clear_rpc=clear_rpc,
            )

        elif cmd == "version":
            check_latest = "--check" in args or "-c" in args
            cmd_version(check_latest=check_latest)

        elif cmd == "update":
            cmd_update()

        else:
            print(f"Unknown command: {cmd}")
            print_help()
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
