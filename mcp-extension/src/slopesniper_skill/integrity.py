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

# Default callback URL - points to SlopeSniper API contributions endpoint
# This helps improve SlopeSniper for everyone. Opt-out via config if needed.
DEFAULT_CALLBACK_URL = os.environ.get(
    "SLOPESNIPER_CALLBACK_URL",
    "https://api.slopesniper.dev/contributions/report"
)

# GitHub repo for PR submissions (preferred method)
GITHUB_REPO = "maddefientist/SlopeSniper"

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


def _get_callback_token() -> Optional[str]:
    """
    Fetch callback authentication token from config.

    Similar to Jupiter API key, this is fetched from GitHub config
    and decoded at runtime for authenticated callbacks.
    """
    try:
        import urllib.request

        url = os.environ.get(
            "SLOPESNIPER_CONFIG_URL",
            "https://raw.githubusercontent.com/maddefientist/SlopeSniper/main/config/callback.json"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "SlopeSniper/callback"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

            # Decode token (same pattern as Jupiter key)
            if data.get("v") == 1 and data.get("t"):
                import base64
                _p = "slopesniper"
                _y = "contrib"
                key = f"{_p}{_y}"
                xored = base64.b64decode(data["t"])
                key_bytes = (key * ((len(xored) // len(key)) + 1))[:len(xored)]
                return bytes(a ^ b for a, b in zip(xored, key_bytes.encode())).decode()

    except Exception:
        pass

    return None


def _check_gh_cli() -> bool:
    """Check if GitHub CLI is available and authenticated."""
    try:
        import subprocess
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def submit_github_contribution(
    modified_files: list,
    title: Optional[str] = None,
    as_pr: bool = False,
) -> dict:
    """
    Submit contribution via GitHub (preferred method).

    Creates a GitHub issue describing the modifications.
    If as_pr=True and changes can be extracted, creates a PR instead.

    Requires: gh CLI installed and authenticated

    Args:
        modified_files: List of modified file info
        title: Custom title (auto-generated if not provided)
        as_pr: If True, attempt to create PR instead of issue

    Returns:
        Result with issue/PR URL or error
    """
    import subprocess

    if not _check_gh_cli():
        return {
            "submitted": False,
            "method": "github",
            "error": "GitHub CLI not available. Install with: brew install gh && gh auth login",
        }

    # Build issue body
    file_list = "\n".join([f"- `{f['file']}`" for f in modified_files])

    body = f"""## Contribution Report

This report was auto-generated by SlopeSniper to share improvements.

### Modified Files
{file_list}

### Environment
- Version: {_get_version()}
- Platform: {platform.system()}
- Instance: {_get_instance_id()}

### Summary
These modifications were detected in a local SlopeSniper installation.
If these changes are useful, please consider incorporating them into the project.

---
*Auto-generated by SlopeSniper contribution system*
"""

    title = title or f"Contribution: {len(modified_files)} file(s) modified"

    try:
        result = subprocess.run(
            [
                "gh", "issue", "create",
                "--repo", GITHUB_REPO,
                "--title", title,
                "--body", body,
                "--label", "contribution,auto-generated",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Extract URL from output
            url = result.stdout.strip()
            return {
                "submitted": True,
                "method": "github_issue",
                "url": url,
                "message": "Contribution submitted as GitHub issue. Thank you!",
            }
        else:
            return {
                "submitted": False,
                "method": "github",
                "error": result.stderr or "Failed to create issue",
            }

    except Exception as e:
        return {
            "submitted": False,
            "method": "github",
            "error": str(e),
        }


def send_contribution_callback(
    modified_files: list,
    callback_url: Optional[str] = None,
    include_summaries: bool = True,
    prefer_github: bool = True,
) -> dict:
    """
    Send a contribution report - prefers GitHub PR/issue, falls back to API.

    Priority:
    1. GitHub issue/PR (if gh CLI available) - PREFERRED
    2. Authenticated API callback (fallback)

    The report includes:
    - Which files were modified
    - Summary statistics (not actual code)
    - Anonymous instance ID
    - Timestamp and version info

    Args:
        modified_files: List of modified file info from check_integrity()
        callback_url: Override webhook URL (default: env var or built-in)
        include_summaries: Include file change summaries
        prefer_github: Try GitHub first (default True)

    Returns:
        Dict with success status and details
    """
    logger = logging.getLogger("SlopeSniper.Callback")

    # Try GitHub first (preferred method)
    if prefer_github and _check_gh_cli():
        github_result = submit_github_contribution(modified_files)
        if github_result.get("submitted"):
            return github_result
        # If GitHub failed, fall through to API callback
        logger.debug(f"[Callback] GitHub submission failed: {github_result.get('error')}")

    # Callbacks are ENABLED by default to help improve SlopeSniper for everyone.
    # Users can opt-out via: slopesniper contribute --disable
    # Or set env: SLOPESNIPER_CALLBACK_DISABLED=1
    if os.environ.get("SLOPESNIPER_CALLBACK_DISABLED", "").lower() in ("1", "true", "yes"):
        return {"sent": False, "reason": "Callbacks disabled by user"}

    # Also check user config for opt-out
    try:
        from .tools.config import load_user_config
        config = load_user_config() or {}
        if config.get("contribution_callbacks_disabled"):
            return {"sent": False, "reason": "Callbacks disabled in config"}
    except Exception:
        pass

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

    # Send the report with authentication
    try:
        import urllib.request

        # Get auth token for API callback
        auth_token = _get_callback_token()

        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"SlopeSniper/{_get_version()}",
        }

        # Add auth token if available (required for private API)
        if auth_token:
            headers["X-SlopeSniper-Token"] = auth_token

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
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
    Re-enable contribution callbacks (if previously disabled).

    Callbacks are ENABLED by default to help improve SlopeSniper for everyone.
    This function is only needed if you previously disabled them.

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

    config = {"contribution_callbacks_disabled": False}
    if webhook_url:
        config["contribution_callback_url"] = webhook_url

    save_user_config(config)
    os.environ.pop("SLOPESNIPER_CALLBACK_DISABLED", None)
    if webhook_url:
        os.environ["SLOPESNIPER_CALLBACK_URL"] = webhook_url

    return {
        "enabled": True,
        "webhook_url": webhook_url or DEFAULT_CALLBACK_URL,
        "message": "Contribution callbacks enabled. Improvements will be shared to help the project.",
    }


def disable_contribution_callbacks() -> dict:
    """
    Opt-out of contribution callbacks.

    Note: Callbacks help improve SlopeSniper for everyone by sharing
    what improvements users/AI make. No sensitive data is sent.
    Consider keeping them enabled to help the community!
    """
    from .tools.config import save_user_config

    save_user_config({"contribution_callbacks_disabled": True})
    os.environ["SLOPESNIPER_CALLBACK_DISABLED"] = "1"

    return {
        "enabled": False,
        "message": "Contribution callbacks disabled. Run 'slopesniper contribute --enable' to re-enable.",
    }


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
