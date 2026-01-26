"""
Policy Gates for Safe Trading.

Deterministic safety checks that run BEFORE any swap execution.
All checks must pass for a trade to be allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import PolicyConfig, get_policy_config


@dataclass
class PolicyResult:
    """Result of policy check."""

    allowed: bool
    reason: str | None = None
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)


# Well-known safe tokens that skip rugcheck
KNOWN_SAFE_MINTS: set[str] = {
    "So11111111111111111111111111111111111111112",  # SOL (wrapped)
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",  # mSOL
    "7dHbWXmci3dT8UFYWYZweBLXgycu7Y3iL6trKn1Y7ARj",  # stSOL
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  # JUP
}


def check_policy(
    from_mint: str,
    to_mint: str,
    amount_usd: float,
    slippage_bps: int,
    rugcheck_result: dict[str, Any] | None = None,
    config: PolicyConfig | None = None,
) -> PolicyResult:
    """
    Run all policy gates on a proposed trade.

    Args:
        from_mint: Token to sell (mint address)
        to_mint: Token to buy (mint address)
        amount_usd: Trade amount in USD
        slippage_bps: Slippage tolerance in basis points
        rugcheck_result: Result from rugcheck API (for to_mint)
        config: Policy configuration (defaults to env config)

    Returns:
        PolicyResult with allowed status and reason if blocked
    """
    if config is None:
        config = get_policy_config()

    checks_passed: list[str] = []
    checks_failed: list[str] = []

    # 1. Check slippage limit
    if slippage_bps > config.MAX_SLIPPAGE_BPS:
        checks_failed.append(
            f"slippage ({slippage_bps}bps > max {config.MAX_SLIPPAGE_BPS}bps)"
        )
    else:
        checks_passed.append(f"slippage ({slippage_bps}bps)")

    # 2. Check trade size limit
    if amount_usd > config.MAX_TRADE_USD:
        checks_failed.append(
            f"trade_size (${amount_usd:.2f} > max ${config.MAX_TRADE_USD:.2f})"
        )
    else:
        checks_passed.append(f"trade_size (${amount_usd:.2f})")

    # 3. Check deny list
    if from_mint in config.DENY_MINTS:
        checks_failed.append("from_mint in DENY_MINTS")
    else:
        checks_passed.append("from_mint not in DENY_MINTS")

    if to_mint in config.DENY_MINTS:
        checks_failed.append("to_mint in DENY_MINTS")
    else:
        checks_passed.append("to_mint not in DENY_MINTS")

    # 4. Check allow list (if set, acts as whitelist)
    if config.ALLOW_MINTS:
        if from_mint not in config.ALLOW_MINTS and from_mint not in KNOWN_SAFE_MINTS:
            checks_failed.append("from_mint not in ALLOW_MINTS")
        else:
            checks_passed.append("from_mint in ALLOW_MINTS")

        if to_mint not in config.ALLOW_MINTS and to_mint not in KNOWN_SAFE_MINTS:
            checks_failed.append("to_mint not in ALLOW_MINTS")
        else:
            checks_passed.append("to_mint in ALLOW_MINTS")

    # 5. Check rugcheck results (skip for known safe tokens)
    if to_mint not in KNOWN_SAFE_MINTS:
        if rugcheck_result:
            score = rugcheck_result.get("score")
            summary = rugcheck_result.get("summary", {})

            # Check score
            if score is not None and score > config.MIN_RUGCHECK_SCORE:
                checks_failed.append(
                    f"rugcheck_score ({score} > max {config.MIN_RUGCHECK_SCORE})"
                )
            elif score is not None:
                checks_passed.append(f"rugcheck_score ({score})")

            # Check mint authority
            if config.REQUIRE_MINT_DISABLED:
                mint_disabled = summary.get("mintAuthority") is None
                if not mint_disabled:
                    checks_failed.append("mint_authority still active")
                else:
                    checks_passed.append("mint_authority disabled")

            # Check freeze authority
            if config.REQUIRE_FREEZE_DISABLED:
                freeze_disabled = summary.get("freezeAuthority") is None
                if not freeze_disabled:
                    checks_failed.append("freeze_authority still active")
                else:
                    checks_passed.append("freeze_authority disabled")
        else:
            # No rugcheck result and not a known safe token
            checks_failed.append("rugcheck required for unknown token")

    # Determine final result
    if checks_failed:
        return PolicyResult(
            allowed=False,
            reason=f"Policy blocked: {', '.join(checks_failed)}",
            checks_passed=checks_passed,
            checks_failed=checks_failed,
        )

    return PolicyResult(
        allowed=True,
        reason=None,
        checks_passed=checks_passed,
        checks_failed=[],
    )


def is_known_safe_mint(mint: str) -> bool:
    """Check if a mint is in the known safe list."""
    return mint in KNOWN_SAFE_MINTS


def format_policy_result(result: PolicyResult) -> str:
    """Format policy result for display."""
    lines = []

    if result.allowed:
        lines.append("Policy Check: PASSED")
    else:
        lines.append(f"Policy Check: BLOCKED - {result.reason}")

    if result.checks_passed:
        lines.append(f"  Passed: {', '.join(result.checks_passed)}")

    if result.checks_failed:
        lines.append(f"  Failed: {', '.join(result.checks_failed)}")

    return "\n".join(lines)
