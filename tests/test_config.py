"""Tests for configuration functionality."""

import os
import pytest

from slopesniper_skill.tools.config import (
    PolicyConfig,
    get_policy_config,
    get_secret,
)


class TestPolicyConfigDefaults:
    """Tests for PolicyConfig default values."""

    def test_default_max_slippage(self) -> None:
        config = PolicyConfig()
        assert config.MAX_SLIPPAGE_BPS == 100

    def test_default_max_trade(self) -> None:
        config = PolicyConfig()
        assert config.MAX_TRADE_USD == 50.0

    def test_default_rugcheck_score(self) -> None:
        config = PolicyConfig()
        assert config.MIN_RUGCHECK_SCORE == 2000

    def test_default_require_mint_disabled(self) -> None:
        config = PolicyConfig()
        assert config.REQUIRE_MINT_DISABLED is True

    def test_default_require_freeze_disabled(self) -> None:
        config = PolicyConfig()
        assert config.REQUIRE_FREEZE_DISABLED is True

    def test_default_deny_mints_empty(self) -> None:
        config = PolicyConfig()
        assert config.DENY_MINTS == []

    def test_default_allow_mints_empty(self) -> None:
        config = PolicyConfig()
        assert config.ALLOW_MINTS == []


class TestPolicyConfigCustom:
    """Tests for custom PolicyConfig values."""

    def test_custom_max_slippage(self) -> None:
        config = PolicyConfig(MAX_SLIPPAGE_BPS=200)
        assert config.MAX_SLIPPAGE_BPS == 200

    def test_custom_max_trade(self) -> None:
        config = PolicyConfig(MAX_TRADE_USD=100.0)
        assert config.MAX_TRADE_USD == 100.0

    def test_custom_deny_mints(self) -> None:
        mints = ["mint1", "mint2"]
        config = PolicyConfig(DENY_MINTS=mints)
        assert config.DENY_MINTS == mints

    def test_custom_allow_mints(self) -> None:
        mints = ["mint1", "mint2"]
        config = PolicyConfig(ALLOW_MINTS=mints)
        assert config.ALLOW_MINTS == mints


class TestGetSecret:
    """Tests for get_secret function."""

    def test_get_secret_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_SECRET_KEY", "test_value")
        value = get_secret("TEST_SECRET_KEY")
        assert value == "test_value"

    def test_get_secret_missing_returns_none(self) -> None:
        # Ensure the env var doesn't exist
        key = "DEFINITELY_MISSING_SECRET_KEY_12345"
        if key in os.environ:
            del os.environ[key]
        value = get_secret(key)
        assert value is None


class TestGetPolicyConfigFromEnv:
    """Tests for loading policy config from environment."""

    def test_load_max_slippage_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POLICY_MAX_SLIPPAGE_BPS", "200")
        config = get_policy_config()
        assert config.MAX_SLIPPAGE_BPS == 200

    def test_load_max_trade_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POLICY_MAX_TRADE_USD", "100.0")
        config = get_policy_config()
        assert config.MAX_TRADE_USD == 100.0

    def test_load_deny_mints_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POLICY_DENY_MINTS", "mint1,mint2,mint3")
        config = get_policy_config()
        assert config.DENY_MINTS == ["mint1", "mint2", "mint3"]

    def test_load_allow_mints_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POLICY_ALLOW_MINTS", "safe1, safe2")
        config = get_policy_config()
        assert config.ALLOW_MINTS == ["safe1", "safe2"]

    def test_load_require_mint_disabled_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("POLICY_REQUIRE_MINT_DISABLED", "false")
        config = get_policy_config()
        assert config.REQUIRE_MINT_DISABLED is False
