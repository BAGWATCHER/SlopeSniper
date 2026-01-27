#!/usr/bin/env python3
"""
Encode tokens for SlopeSniper config files.

Usage:
    python encode_token.py <token> [key_suffix]

Examples:
    # Encode GitHub token for callback.json (gh field)
    python encode_token.py ghp_xxxx github

    # Encode API callback token (t field)
    python encode_token.py my_token contrib

    # Encode Jupiter API key
    python encode_token.py jup_key jup
"""

import base64
import sys


def encode_token(token: str, key_suffix: str = "github") -> str:
    """XOR encode a token with the SlopeSniper key."""
    key = f"slopesniper{key_suffix}"
    key_bytes = (key * ((len(token) // len(key)) + 1))[:len(token)]
    xored = bytes(a ^ b for a, b in zip(token.encode(), key_bytes.encode()))
    return base64.b64encode(xored).decode()


def decode_token(encoded: str, key_suffix: str = "github") -> str:
    """XOR decode a token (for verification)."""
    key = f"slopesniper{key_suffix}"
    xored = base64.b64decode(encoded)
    key_bytes = (key * ((len(xored) // len(key)) + 1))[:len(xored)]
    return bytes(a ^ b for a, b in zip(xored, key_bytes.encode())).decode()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = sys.argv[1]
    key_suffix = sys.argv[2] if len(sys.argv) > 2 else "github"

    encoded = encode_token(token, key_suffix)
    print(f"Encoded ({key_suffix}): {encoded}")

    # Verify
    decoded = decode_token(encoded, key_suffix)
    assert decoded == token, "Verification failed!"
    print("Verified OK")
