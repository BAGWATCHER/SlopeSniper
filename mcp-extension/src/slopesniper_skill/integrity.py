"""
Integrity & Contribution Tracking Module.

This module provides mechanisms to:
1. Verify codebase integrity against official releases
2. Detect and report improvements made by users/AI
3. Enable contribution callbacks for non-GitHub workflows

Contribution callbacks allow improvements to be reported back
to maintainers via webhook (Discord, Slack, or custom endpoint).
This enables community improvements even from users who don't use GitHub.

Configuration:
- SLOPESNIPER_CALLBACK_URL: Webhook URL for contribution reports
- SLOPESNIPER_CALLBACK_ENABLED: Set to "1" to enable callbacks
- SLOPESNIPER_SKIP_INTEGRITY_CHECK: Set to "1" to disable checks
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

# Files to check for modifications (relative to package root)
MONITORED_FILES = [
    "sdk/jupiter_data_client.py",
    "sdk/jupiter_ultra_client.py",
    "tools/solana_tools.py",
    "tools/config.py",
    "tools/policy.py",
]

# How often to check (don't spam on every import)
CHECK_INTERVAL_HOURS = 24

# Where to store check results
INTEGRITY_CACHE_FILE = Path.home() / ".slopesniper" / "integrity_cache.json"


def _get_package_root() -> Path:
    """Get the package root directory."""
    return Path(__file__).parent


def _hash_file(filepath: Path) -> str:
    """Generate SHA256 hash of a file."""
    if not filepath.exists():
        return "MISSING"

    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]  # First 16 chars is enough


def _get_local_hashes() -> dict[str, str]:
    """Get hashes of all monitored files."""
    package_root = _get_package_root()
    hashes = {}

    for rel_path in MONITORED_FILES:
        filepath = package_root / rel_path
        hashes[rel_path] = _hash_file(filepath)

    return hashes


def _should_check() -> bool:
    """Determine if we should run integrity check (rate limited)."""
    if not INTEGRITY_CACHE_FILE.exists():
        return True

    try:
        cache = json.loads(INTEGRITY_CACHE_FILE.read_text())
        last_check = datetime.fromisoformat(cache.get("last_check", "2000-01-01"))
        return datetime.now() - last_check > timedelta(hours=CHECK_INTERVAL_HOURS)
    except Exception:
        return True


def _update_cache(result: dict) -> None:
    """Update the integrity check cache."""
    try:
        INTEGRITY_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache = {
            "last_check": datetime.now().isoformat(),
            "result": result,
        }
        INTEGRITY_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass  # Non-critical


def _fetch_expected_hashes() -> Optional[dict[str, str]]:
    """Fetch expected file hashes from GitHub."""
    try:
        import urllib.request

        # Fetch integrity manifest from GitHub
        url = os.environ.get(
            "SLOPESNIPER_INTEGRITY_URL",
            "https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/integrity.json"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "SlopeSniper/integrity"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def check_integrity(force: bool = False) -> dict:
    """
    Check if local files match expected hashes.

    Args:
        force: If True, run check even if recently checked

    Returns:
        Dict with status, modified_files list, and action_required
    """
    logger = logging.getLogger("SlopeSniper.Integrity")

    if not force and not _should_check():
        # Return cached result
        try:
            cache = json.loads(INTEGRITY_CACHE_FILE.read_text())
            return cache.get("result", {"status": "unknown"})
        except Exception:
            pass

    result = {
        "status": "ok",
        "modified_files": [],
        "action_required": None,
        "checked_at": datetime.now().isoformat(),
    }

    # Get expected hashes from GitHub
    expected = _fetch_expected_hashes()
    if expected is None:
        result["status"] = "skip"
        result["reason"] = "Could not fetch integrity manifest"
        _update_cache(result)
        return result

    # Compare with local
    local = _get_local_hashes()

    for filepath, expected_hash in expected.items():
        local_hash = local.get(filepath, "UNKNOWN")
        if local_hash != expected_hash:
            result["modified_files"].append({
                "file": filepath,
                "expected": expected_hash,
                "actual": local_hash,
            })

    if result["modified_files"]:
        result["status"] = "modified"
        result["action_required"] = (
            "Local modifications detected. If these are improvements, "
            "please contribute them back via GitHub issue or PR. "
            "See AI_CONTRIBUTION_POLICY.md for guidelines."
        )
        logger.warning(
            f"[IntegrityCheck] {len(result['modified_files'])} file(s) modified: "
            f"{[f['file'] for f in result['modified_files']]}"
        )
    else:
        logger.debug("[IntegrityCheck] All files match expected hashes")

    _update_cache(result)
    return result


def generate_integrity_manifest() -> dict:
    """
    Generate integrity manifest for the current codebase.

    This should be run by maintainers before release to update
    the config/integrity.json file on GitHub.

    Returns:
        Dict of file paths to hashes
    """
    return _get_local_hashes()


# Run check on import (rate-limited)
def _run_startup_check() -> None:
    """Run integrity check on module import."""
    # Only run in production-like environments
    if os.environ.get("SLOPESNIPER_SKIP_INTEGRITY_CHECK"):
        return

    try:
        result = check_integrity()
        if result.get("status") == "modified":
            logger = logging.getLogger("SlopeSniper.Integrity")
            logger.warning(
                "=== SlopeSniper Integrity Warning ===\n"
                "Local code modifications detected.\n"
                "Please contribute improvements back via GitHub.\n"
                f"Modified files: {[f['file'] for f in result['modified_files']]}\n"
                "See AI_CONTRIBUTION_POLICY.md for guidelines.\n"
                "=== End Warning ==="
            )
    except Exception:
        pass  # Never break normal operation


# Uncomment to enable startup checks:
# _run_startup_check()


# =============================================================================
# CONTRIBUTION CALLBACK SYSTEM
# =============================================================================

# Default callback URL (can be overridden via env var or config)
DEFAULT_CALLBACK_URL = os.environ.get(
    "SLOPESNIPER_CALLBACK_URL",
    "https://slopesniper-contributions.maddefientist.workers.dev/report"
)

# Callback cache to avoid duplicate reports
CALLBACK_CACHE_FILE = Path.home() / ".slopesniper" / "callback_cache.json"


def _get_instance_id() -> str:
    """
    Get a stable anonymous instance ID for this installation.

    Used to correlate multiple reports from the same instance
    without identifying the user.
    """
    id_file = Path.home() / ".slopesniper" / ".instance_id"

    if id_file.exists():
        try:
            return id_file.read_text().strip()
        except Exception:
            pass

    # Generate new ID
    instance_id = str(uuid.uuid4())[:8]
    try:
        id_file.parent.mkdir(parents=True, exist_ok=True)
        id_file.write_text(instance_id)
    except Exception:
        pass

    return instance_id


def _get_file_diff_summary(filepath: Path) -> Optional[dict]:
    """
    Get a summary of changes in a file (not the full content).

    Returns line count changes and a brief description,
    NOT the actual code (for privacy).
    """
    if not filepath.exists():
        return {"status": "missing"}

    try:
        content = filepath.read_text()
        lines = content.split("\n")

        # Extract docstring/description if present
        description = ""
        if '"""' in content:
            start = content.find('"""') + 3
            end = content.find('"""', start)
            if end > start:
                description = content[start:end].strip()[:100]

        return {
            "line_count": len(lines),
            "has_async": "async def" in content,
            "has_class": "class " in content,
            "function_count": content.count("def "),
            "description_preview": description,
        }
    except Exception:
        return {"status": "error"}


def _should_send_callback(modified_files: list) -> bool:
    """Check if we should send a callback (avoid duplicates)."""
    if not modified_files:
        return False

    # Create a signature of the current modifications
    sig = hashlib.md5(
        json.dumps(sorted([f["file"] for f in modified_files])).encode()
    ).hexdigest()[:8]

    # Check cache
    if CALLBACK_CACHE_FILE.exists():
        try:
            cache = json.loads(CALLBACK_CACHE_FILE.read_text())
            if cache.get("last_signature") == sig:
                last_sent = datetime.fromisoformat(cache.get("last_sent", "2000-01-01"))
                # Don't re-send same modifications within 7 days
                if datetime.now() - last_sent < timedelta(days=7):
                    return False
        except Exception:
            pass

    return True


def _update_callback_cache(signature: str) -> None:
    """Update the callback cache after sending."""
    try:
        CALLBACK_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache = {
            "last_signature": signature,
            "last_sent": datetime.now().isoformat(),
        }
        CALLBACK_CACHE_FILE.write_text(json.dumps(cache))
    except Exception:
        pass


def send_contribution_callback(
    modified_files: list,
    callback_url: Optional[str] = None,
    include_summaries: bool = True,
) -> dict:
    """
    Send a contribution report to the callback webhook.

    This allows improvements to be tracked even without GitHub.
    The report includes:
    - Which files were modified
    - Summary statistics (not actual code)
    - Anonymous instance ID
    - Timestamp and version info

    Args:
        modified_files: List of modified file info from check_integrity()
        callback_url: Override webhook URL (default: env var or built-in)
        include_summaries: Include file change summaries

    Returns:
        Dict with success status and details
    """
    logger = logging.getLogger("SlopeSniper.Callback")

    # Check if callbacks are enabled
    if not os.environ.get("SLOPESNIPER_CALLBACK_ENABLED", "").lower() in ("1", "true", "yes"):
        return {"sent": False, "reason": "Callbacks not enabled"}

    if not modified_files:
        return {"sent": False, "reason": "No modifications to report"}

    if not _should_send_callback(modified_files):
        return {"sent": False, "reason": "Already reported recently"}

    url = callback_url or DEFAULT_CALLBACK_URL

    # Build the report payload
    package_root = _get_package_root()

    file_reports = []
    for mod in modified_files:
        report = {
            "file": mod["file"],
            "expected_hash": mod.get("expected", "unknown"),
            "actual_hash": mod.get("actual", "unknown"),
        }

        if include_summaries:
            filepath = package_root / mod["file"]
            summary = _get_file_diff_summary(filepath)
            if summary:
                report["summary"] = summary

        file_reports.append(report)

    payload = {
        "type": "contribution_report",
        "instance_id": _get_instance_id(),
        "timestamp": datetime.now().isoformat(),
        "version": _get_version(),
        "platform": platform.system(),
        "files_modified": len(modified_files),
        "modifications": file_reports,
    }

    # Send the report
    try:
        import urllib.request

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"SlopeSniper/{_get_version()}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            response_data = resp.read().decode()

            # Update cache on success
            sig = hashlib.md5(
                json.dumps(sorted([f["file"] for f in modified_files])).encode()
            ).hexdigest()[:8]
            _update_callback_cache(sig)

            logger.info(f"[Callback] Contribution report sent successfully")
            return {
                "sent": True,
                "files_reported": len(modified_files),
                "response": response_data[:100],
            }

    except Exception as e:
        logger.debug(f"[Callback] Failed to send report: {e}")
        return {"sent": False, "error": str(e)}


def _get_version() -> str:
    """Get package version."""
    try:
        from . import __version__
        return __version__
    except Exception:
        return "unknown"


def enable_contribution_callbacks(
    webhook_url: Optional[str] = None,
) -> dict:
    """
    Enable contribution callbacks for this installation.

    Call this to opt-in to sending modification reports.

    Args:
        webhook_url: Custom webhook URL (Discord, Slack, or any endpoint)
                    If not provided, uses the default SlopeSniper endpoint.

    Returns:
        Configuration status

    Example webhook URLs:
        Discord: https://discord.com/api/webhooks/xxx/yyy
        Slack: https://hooks.slack.com/services/xxx/yyy/zzz
        Custom: https://your-server.com/contributions
    """
    from .tools.config import save_user_config

    config = {"contribution_callbacks_enabled": True}
    if webhook_url:
        config["contribution_callback_url"] = webhook_url

    save_user_config(config)
    os.environ["SLOPESNIPER_CALLBACK_ENABLED"] = "1"
    if webhook_url:
        os.environ["SLOPESNIPER_CALLBACK_URL"] = webhook_url

    return {
        "enabled": True,
        "webhook_url": webhook_url or DEFAULT_CALLBACK_URL,
        "message": "Contribution callbacks enabled. Modifications will be reported.",
    }


def disable_contribution_callbacks() -> dict:
    """Disable contribution callbacks."""
    from .tools.config import save_user_config

    save_user_config({"contribution_callbacks_enabled": False})
    os.environ.pop("SLOPESNIPER_CALLBACK_ENABLED", None)

    return {"enabled": False, "message": "Contribution callbacks disabled."}


def check_and_report(force: bool = False) -> dict:
    """
    Run integrity check and send callback if modifications detected.

    This is the main entry point for the contribution tracking system.
    Combines check_integrity() with send_contribution_callback().

    Args:
        force: Force check even if recently run

    Returns:
        Combined result of check and callback
    """
    result = check_integrity(force=force)

    if result.get("status") == "modified":
        callback_result = send_contribution_callback(result["modified_files"])
        result["callback"] = callback_result

    return result
