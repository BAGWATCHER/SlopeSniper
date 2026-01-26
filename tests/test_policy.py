"""Tests for policy gate functionality."""

import pytest

from slopesniper_skill.tools.policy import (
    PolicyResult,
    check_policy,
    is_known_safe_mint,
    KNOWN_SAFE_MINTS,
)
from slopesniper_skill.tools.config import PolicyConfig


# Known mints for testing
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
RANDOM_MINT = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # BONK


class TestKnownSafeMints:
    """Tests for known safe mint detection."""

    def test_sol_is_known_safe(self) -> None:
        assert is_known_safe_mint(SOL_MINT) is True

    def test_usdc_is_known_safe(self) -> None:
        assert is_known_safe_mint(USDC_MINT) is True

    def test_random_address_not_known_safe(self) -> None:
        fake_mint = "1111111111111111111111111111111111111111111"
        assert is_known_safe_mint(fake_mint) is False


class TestPolicySlippage:
    """Tests for slippage policy checks."""

    def test_slippage_within_limit_passes(self) -> None:
        config = PolicyConfig(MAX_SLIPPAGE_BPS=100)
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is True
        assert "slippage (50bps)" in result.checks_passed

    def test_slippage_at_limit_passes(self) -> None:
        config = PolicyConfig(MAX_SLIPPAGE_BPS=100)
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=100,
            config=config,
        )
        assert result.allowed is True

    def test_slippage_over_limit_fails(self) -> None:
        config = PolicyConfig(MAX_SLIPPAGE_BPS=100)
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=150,
            config=config,
        )
        assert result.allowed is False
        assert "slippage" in result.reason


class TestPolicyTradeSize:
    """Tests for trade size policy checks."""

    def test_trade_within_limit_passes(self) -> None:
        config = PolicyConfig(MAX_TRADE_USD=50.0)
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=25.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is True
        assert "trade_size ($25.00)" in result.checks_passed

    def test_trade_over_limit_fails(self) -> None:
        config = PolicyConfig(MAX_TRADE_USD=50.0)
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=75.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is False
        assert "trade_size" in result.reason


class TestPolicyDenyList:
    """Tests for deny list functionality."""

    def test_from_mint_in_deny_list_fails(self) -> None:
        config = PolicyConfig(DENY_MINTS=[SOL_MINT])
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is False
        assert "DENY_MINTS" in result.reason

    def test_to_mint_in_deny_list_fails(self) -> None:
        config = PolicyConfig(DENY_MINTS=[USDC_MINT])
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is False
        assert "DENY_MINTS" in result.reason


class TestPolicyAllowList:
    """Tests for allow list (whitelist) functionality."""

    def test_mints_in_allow_list_passes(self) -> None:
        config = PolicyConfig(ALLOW_MINTS=[SOL_MINT, USDC_MINT])
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is True

    def test_known_safe_mints_bypass_allow_list(self) -> None:
        # Even with a restrictive allow list, known safe mints should work
        config = PolicyConfig(ALLOW_MINTS=["SomeOtherMint123456789012345678901234567890"])
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            config=config,
        )
        assert result.allowed is True


class TestPolicyRugcheck:
    """Tests for rugcheck policy checks."""

    def test_known_safe_token_skips_rugcheck(self) -> None:
        config = PolicyConfig()
        # No rugcheck result provided, but should pass for known safe token
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=USDC_MINT,
            amount_usd=10.0,
            slippage_bps=50,
            rugcheck_result=None,
            config=config,
        )
        assert result.allowed is True

    def test_unknown_token_without_rugcheck_fails(self) -> None:
        config = PolicyConfig()
        unknown_mint = "UnknownToken1234567890123456789012345678901"
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=unknown_mint,
            amount_usd=10.0,
            slippage_bps=50,
            rugcheck_result=None,
            config=config,
        )
        assert result.allowed is False
        assert "rugcheck required" in result.reason

    def test_rugcheck_high_score_fails(self) -> None:
        config = PolicyConfig(MIN_RUGCHECK_SCORE=2000)
        unknown_mint = "UnknownToken1234567890123456789012345678901"
        rugcheck = {"score": 5000, "summary": {}}
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=unknown_mint,
            amount_usd=10.0,
            slippage_bps=50,
            rugcheck_result=rugcheck,
            config=config,
        )
        assert result.allowed is False
        assert "rugcheck_score" in result.reason

    def test_rugcheck_passing_score_allowed(self) -> None:
        config = PolicyConfig(
            MIN_RUGCHECK_SCORE=2000,
            REQUIRE_MINT_DISABLED=False,
            REQUIRE_FREEZE_DISABLED=False,
        )
        unknown_mint = "UnknownToken1234567890123456789012345678901"
        rugcheck = {"score": 500, "summary": {}}
        result = check_policy(
            from_mint=SOL_MINT,
            to_mint=unknown_mint,
            amount_usd=10.0,
            slippage_bps=50,
            rugcheck_result=rugcheck,
            config=config,
        )
        assert result.allowed is True


class TestPolicyResult:
    """Tests for PolicyResult dataclass."""

    def test_policy_result_defaults(self) -> None:
        result = PolicyResult(allowed=True)
        assert result.allowed is True
        assert result.reason is None
        assert result.checks_passed == []
        assert result.checks_failed == []

    def test_policy_result_with_checks(self) -> None:
        result = PolicyResult(
            allowed=False,
            reason="Test failure",
            checks_passed=["check1"],
            checks_failed=["check2"],
        )
        assert result.allowed is False
        assert result.reason == "Test failure"
        assert "check1" in result.checks_passed
        assert "check2" in result.checks_failed
