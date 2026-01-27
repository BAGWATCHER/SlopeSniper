"""
Integrity Check Module - Detect unauthorized code modifications.

This module provides mechanisms to verify that the SlopeSniper codebase
hasn't been modified from the official release. This ensures:
1. Security - No malicious modifications
2. Quality - No untested changes
3. Community benefit - Improvements should be contributed back

See AI_CONTRIBUTION_POLICY.md for the full contribution guidelines.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
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
