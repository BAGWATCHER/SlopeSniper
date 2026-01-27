#!/usr/bin/env python3
"""
Encode a GitHub token for SlopeSniper callback.json

Usage:
    python3 scripts/encode-github-token.py YOUR_GITHUB_TOKEN

The token needs 'repo' scope to create issues.
Generate one at: https://github.com/settings/tokens
"""

import base64
import sys
import json
from pathlib import Path


def encode_token(token: str) -> str:
    """Encode token using XOR obfuscation (same as integrity.py)."""
    key = "slopesniper2024"
    key_bytes = (key * ((len(token) // len(key)) + 1))[:len(token)]
    xored = bytes(a ^ b for a, b in zip(token.encode(), key_bytes.encode()))
    return base64.b64encode(xored).decode()


def decode_token(encoded: str) -> str:
    """Decode token (for verification)."""
    key = "slopesniper2024"
    try:
        xored = base64.b64decode(encoded)
        key_bytes = (key * ((len(xored) // len(key)) + 1))[:len(xored)]
        return bytes(a ^ b for a, b in zip(xored, key_bytes.encode())).decode()
    except Exception:
        return ""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: Please provide a GitHub token as argument")
        sys.exit(1)

    token = sys.argv[1]

    # Validate token format
    if not token.startswith("ghp_") and not token.startswith("github_pat_"):
        print("Warning: Token doesn't look like a GitHub token (expected ghp_* or github_pat_*)")
        print("Continuing anyway...")
        print()

    # Encode
    encoded = encode_token(token)

    # Verify roundtrip
    decoded = decode_token(encoded)
    if decoded != token:
        print("Error: Encoding verification failed!")
        sys.exit(1)

    print("=" * 60)
    print("GitHub Token Encoded Successfully")
    print("=" * 60)
    print()
    print(f"Original token: {token[:10]}...{token[-4:]}")
    print(f"Token length: {len(token)}")
    print()
    print("Encoded value (for callback.json 'gh' field):")
    print()
    print(encoded)
    print()
    print("=" * 60)
    print()

    # Optionally update callback.json
    config_path = Path(__file__).parent.parent / "config" / "callback.json"
    if config_path.exists():
        print(f"Found: {config_path}")
        response = input("Update callback.json with this token? (y/N) ")
        if response.lower() == 'y':
            with open(config_path, 'r') as f:
                config = json.load(f)
            config['gh'] = encoded
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print("Updated callback.json!")
        else:
            print("Skipped. You can manually update config/callback.json")
    else:
        print("To use this token, update config/callback.json:")
        print(f'  "gh": "{encoded}"')


if __name__ == "__main__":
    main()
