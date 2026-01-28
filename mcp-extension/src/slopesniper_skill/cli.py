#!/usr/bin/env python3
"""
SlopeSniper CLI - Simple command interface for Clawdbot agents.

Usage:
    slopesniper setup               Create new wallet (interactive, recommended)
    slopesniper setup --import-key KEY   Import existing private key
    slopesniper status              Full status: wallet, holdings, strategy, config
    slopesniper wallet              Show wallet address and all token holdings
    slopesniper export              Export private key for backup/recovery
    slopesniper export --list-backups    List all backed up wallets
    slopesniper export --backup TIMESTAMP    Export a specific backup
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
    slopesniper uninstall           Clean uninstall (removes CLI and optionally data)
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
    from . import get_status, get_strategy, solana_get_wallet
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


def cmd_setup(import_key: str | None = None) -> None:
    """Interactive wallet setup with confirmation."""
    from .tools.config import load_local_wallet
    from .tools.onboarding import create_wallet_explicit, setup_wallet

    # Check if wallet already exists
    existing = load_local_wallet()
    if existing and not import_key:
        print("")
        print("Wallet already configured!")
        print(f"  Address: {existing['address']}")
        print("")
        print("To import a different wallet (current will be backed up):")
        print("  slopesniper setup --import-key YOUR_PRIVATE_KEY")
        print("")
        print("To view/export your current key:")
        print("  slopesniper export")
        print("")
        return

    print("")
    print("=" * 60)
    print("  SlopeSniper Wallet Setup")
    print("=" * 60)
    print("")

    if import_key:
        # Import existing private key
        result = asyncio.run(setup_wallet(private_key=import_key))
        if result.get("success"):
            print("Wallet imported successfully!")
            print(f"  Address: {result['wallet_address']}")
            print("")
            print("Send SOL to this address to start trading.")
        else:
            print(f"Error: {result.get('error')}")
            if result.get("hint"):
                print(f"Hint: {result['hint']}")
        print("")
        return

    # New wallet creation - get user confirmation
    print("This will create a new Solana trading wallet.")
    print("")
    print("IMPORTANT:")
    print("  - You will receive a PRIVATE KEY")
    print("  - Anyone with this key can access your funds")
    print("  - You MUST save it securely - it cannot be recovered")
    print("")

    try:
        confirm = input("Create new wallet? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("")
            print("Setup cancelled.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.")
        return

    # Generate wallet
    result = asyncio.run(create_wallet_explicit())

    # Display with emphasis
    print("")
    print("=" * 60)
    print("  WALLET CREATED - SAVE YOUR PRIVATE KEY NOW!")
    print("=" * 60)
    print("")
    print(f"  Address: {result['address']}")
    print("")
    print("  Private Key:")
    print(f"  {result['private_key']}")
    print("")
    print("=" * 60)
    print("")

    # Require confirmation they saved it
    try:
        print("To confirm you saved your key, type your wallet address:")
        user_addr = input("> ").strip()
        if user_addr != result["address"]:
            print("")
            print("WARNING: Address doesn't match!")
            print(f"Your address is: {result['address']}")
            print("Make sure you saved your private key correctly.")
            print("")
            return
    except (EOFError, KeyboardInterrupt):
        print("\nPlease make sure you saved your private key!")
        print("")
        return

    print("")
    print("Setup complete! Send SOL to your address to start trading.")
    print("")
    print("Next steps:")
    print("  slopesniper status   - Check balance")
    print("  slopesniper export   - Backup key anytime")
    print("")


async def cmd_wallet() -> None:
    """Show wallet address and holdings."""
    from . import solana_get_wallet

    result = await solana_get_wallet()
    print_json(result)


async def cmd_export(
    list_backups: bool = False,
    backup_timestamp: str | None = None,
) -> None:
    """Export private key for backup/recovery."""
    if list_backups:
        from .tools.onboarding import list_backup_wallets

        result = await list_backup_wallets()
        print_json(result)
    elif backup_timestamp:
        from .tools.onboarding import export_backup

        result = await export_backup(backup_timestamp)
        print_json(result)
    else:
        from . import export_wallet
        from .tools.config import record_backup_export

        result = await export_wallet(include_backups=True)
        # Record that user exported their wallet (for backup reminder tracking)
        if result.get("success"):
            record_backup_export()
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
        clear_rpc_config,
        get_config_status,
        set_jupiter_api_key,
        set_rpc_config,
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
            result = {
                "error": f"Unknown config key: {set_key}",
                "valid_keys": ["jupiter-key", "rpc-url", "helius", "quicknode", "alchemy"],
            }
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
        "repo": "https://github.com/BAGWATCHER/SlopeSniper",
        "changelog": "https://github.com/BAGWATCHER/SlopeSniper/blob/main/CHANGELOG.md",
    }

    if check_latest:
        try:
            import re
            import urllib.request

            # Fetch pyproject.toml from GitHub to get latest version
            url = "https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/mcp-extension/pyproject.toml"
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
    import re
    import subprocess
    import urllib.request

    from . import __version__

    old_version = __version__

    print("Updating SlopeSniper...")
    print(f"Current version: {old_version}")
    print("")

    success = False
    method = ""

    # Try uv tool first (preferred for CLI tools)
    try:
        result = subprocess.run(
            [
                "uv",
                "tool",
                "install",
                "slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension",
                "--force",
                "--refresh",  # Bust git cache
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            success = True
            method = "uv tool"
    except FileNotFoundError:
        pass

    # Fallback to uv pip
    if not success:
        try:
            result = subprocess.run(
                [
                    "uv",
                    "pip",
                    "install",
                    "--force-reinstall",
                    "--refresh",  # Bust git cache
                    "slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                success = True
                method = "uv pip"
        except FileNotFoundError:
            pass

    # Final fallback to pip
    if not success:
        try:
            result = subprocess.run(
                [
                    "pip",
                    "install",
                    "--force-reinstall",
                    "--no-cache-dir",  # Bust pip cache
                    "slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                success = True
                method = "pip"
        except FileNotFoundError:
            pass

    if not success:
        print_json(
            {
                "error": "Update failed",
                "suggestion": "Try manually: uv tool install 'slopesniper-mcp @ git+https://github.com/BAGWATCHER/SlopeSniper.git#subdirectory=mcp-extension' --force",
            }
        )
        return

    # Fetch new version from GitHub
    new_version = "unknown"
    changelog_summary = []
    try:
        # Get version
        version_url = "https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/mcp-extension/pyproject.toml"
        req = urllib.request.Request(version_url, headers={"User-Agent": "SlopeSniper"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                new_version = match.group(1)

        # Get recent changelog
        changelog_url = "https://raw.githubusercontent.com/BAGWATCHER/SlopeSniper/main/CHANGELOG.md"
        req = urllib.request.Request(changelog_url, headers={"User-Agent": "SlopeSniper"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            changelog = resp.read().decode()
            # Extract first version section (after [Unreleased])
            lines = changelog.split("\n")
            in_section = False
            section_count = 0
            for line in lines:
                if line.startswith("## [") and "Unreleased" not in line:
                    if section_count == 0:
                        in_section = True
                        changelog_summary.append(line)
                        section_count += 1
                    else:
                        break
                elif in_section:
                    if line.startswith("## ["):
                        break
                    if line.strip():
                        changelog_summary.append(line)
    except Exception:
        pass

    # Print success message
    print("=" * 50)
    print(f"  Updated successfully via {method}!")
    print("=" * 50)
    print("")
    print(f"  {old_version} → {new_version}")
    print("")

    if changelog_summary:
        print("What's new:")
        print("-" * 50)
        for line in changelog_summary[:15]:  # Limit to 15 lines
            print(line)
        print("-" * 50)
        print("")

    print("Full changelog: https://github.com/BAGWATCHER/SlopeSniper/blob/main/CHANGELOG.md")
    print("")


def cmd_uninstall(keep_data: bool = False, confirm: bool = False) -> None:
    """Clean uninstall SlopeSniper."""
    import shutil
    import subprocess

    from .tools.config import SLOPESNIPER_DIR

    print("")
    print("=" * 50)
    print("  SlopeSniper Uninstall")
    print("=" * 50)
    print("")

    # Check for wallet
    wallet_exists = (SLOPESNIPER_DIR / "wallet.enc").exists()

    if wallet_exists:
        print("WARNING: You have a wallet configured!")
        print("")
        # Try to show the address
        try:
            from .tools.config import load_local_wallet

            wallet = load_local_wallet()
            if wallet:
                print(f"  Wallet address: {wallet['address']}")
                print("")
        except Exception:
            pass

        print("IMPORTANT: Before uninstalling, make sure you have:")
        print("  1. Exported your private key: slopesniper export")
        print("  2. Saved it in a secure location")
        print("  3. Transferred any remaining funds")
        print("")
        print("If you lose your private key, YOUR FUNDS WILL BE LOST FOREVER.")
        print("")

    if not confirm:
        print("To proceed with uninstall, add --confirm flag:")
        print("")
        print("  slopesniper uninstall --confirm            # Remove everything")
        print("  slopesniper uninstall --confirm --keep-data  # Keep wallet/config")
        print("")
        return

    # Double-check if wallet exists and not keeping data
    if wallet_exists and not keep_data:
        print("=" * 50)
        print("  FINAL WARNING: WALLET WILL BE DELETED")
        print("=" * 50)
        print("")
        try:
            response = input("Type 'DELETE MY WALLET' to confirm: ")
            if response.strip() != "DELETE MY WALLET":
                print("")
                print("Uninstall cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("")
            print("Uninstall cancelled.")
            return

    # Remove CLI tool
    print("Removing SlopeSniper CLI...")
    success = False

    # Try uv tool uninstall
    try:
        result = subprocess.run(
            ["uv", "tool", "uninstall", "slopesniper-mcp"], capture_output=True, text=True
        )
        if result.returncode == 0:
            success = True
            print("   Removed via uv tool")
    except FileNotFoundError:
        pass

    # Fallback to pip
    if not success:
        try:
            result = subprocess.run(
                ["pip", "uninstall", "-y", "slopesniper-mcp"], capture_output=True, text=True
            )
            if result.returncode == 0:
                success = True
                print("   Removed via pip")
        except FileNotFoundError:
            pass

    if not success:
        print("   Warning: Could not remove CLI package")

    print("")

    # Handle data directory
    if SLOPESNIPER_DIR.exists():
        if keep_data:
            print(f"Keeping data directory: {SLOPESNIPER_DIR}")
            print("Your wallet and config are preserved.")
        else:
            print(f"Removing data directory: {SLOPESNIPER_DIR}")
            try:
                shutil.rmtree(SLOPESNIPER_DIR)
                print("   Removed successfully")
            except Exception as e:
                print(f"   Error: {e}")

    print("")
    print("=" * 50)
    print("  Uninstall complete!")
    print("=" * 50)
    print("")


def cmd_contribute(
    enable: bool = False,
    disable: bool = False,
) -> None:
    """Manage contribution callbacks and check for improvements."""
    from .integrity import (
        check_and_report,
        disable_contribution_callbacks,
        enable_contribution_callbacks,
    )
    from .tools.config import load_user_config

    if enable:
        # No URL needed - contributions go to GitHub Issues
        result = enable_contribution_callbacks()
        result["method"] = "GitHub Issues"
        result["repo"] = "BAGWATCHER/SlopeSniper"
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
        if cmd == "setup":
            import_key = None
            if "--import-key" in args:
                idx = args.index("--import-key")
                if idx + 1 < len(args):
                    import_key = args[idx + 1]
            cmd_setup(import_key=import_key)

        elif cmd == "status":
            asyncio.run(cmd_status())

        elif cmd == "wallet":
            asyncio.run(cmd_wallet())

        elif cmd == "export":
            list_backups = "--list-backups" in args or "-l" in args
            backup_timestamp = None
            if "--backup" in args:
                idx = args.index("--backup")
                if idx + 1 < len(args):
                    backup_timestamp = args[idx + 1]
            asyncio.run(cmd_export(list_backups=list_backups, backup_timestamp=backup_timestamp))

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

        elif cmd == "uninstall":
            confirm = "--confirm" in args or "-y" in args
            keep_data = "--keep-data" in args
            cmd_uninstall(keep_data=keep_data, confirm=confirm)

        else:
            print(f"Unknown command: {cmd}")
            print_help()
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
