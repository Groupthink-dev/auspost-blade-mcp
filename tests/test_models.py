"""Tests for config parsing and security gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from auspost_blade_mcp.models import (
    PACConfig,
    ShippingConfig,
    is_shipping_enabled,
    is_write_enabled,
    require_pac,
    require_shipping,
    require_write,
)

if TYPE_CHECKING:
    import pytest


class TestPACConfig:
    def test_from_env_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_API_KEY", "my-key")
        config = PACConfig.from_env()
        assert config is not None
        assert config.api_key == "my-key"

    def test_from_env_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUSPOST_API_KEY", raising=False)
        assert PACConfig.from_env() is None

    def test_from_env_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_API_KEY", "  ")
        assert PACConfig.from_env() is None


class TestShippingConfig:
    def test_from_env_all_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_SHIPPING_API_KEY", "key")
        monkeypatch.setenv("AUSPOST_SHIPPING_API_PASSWORD", "pass")
        monkeypatch.setenv("AUSPOST_ACCOUNT_NUMBER", "1234567890")
        config = ShippingConfig.from_env()
        assert config is not None
        assert config.api_key == "key"
        assert config.api_password == "pass"
        assert config.account_number == "1234567890"
        assert config.test_mode is False

    def test_from_env_test_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_SHIPPING_API_KEY", "key")
        monkeypatch.setenv("AUSPOST_SHIPPING_API_PASSWORD", "pass")
        monkeypatch.setenv("AUSPOST_ACCOUNT_NUMBER", "1234567890")
        monkeypatch.setenv("AUSPOST_SHIPPING_TEST_MODE", "true")
        config = ShippingConfig.from_env()
        assert config is not None
        assert config.test_mode is True

    def test_from_env_partial(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_SHIPPING_API_KEY", "key")
        monkeypatch.delenv("AUSPOST_SHIPPING_API_PASSWORD", raising=False)
        monkeypatch.delenv("AUSPOST_ACCOUNT_NUMBER", raising=False)
        assert ShippingConfig.from_env() is None


class TestGates:
    def test_require_pac_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUSPOST_API_KEY", raising=False)
        result = require_pac()
        assert result is not None
        assert "AUSPOST_API_KEY" in result

    def test_require_pac_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_API_KEY", "key")
        assert require_pac() is None

    def test_require_shipping_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUSPOST_SHIPPING_API_KEY", raising=False)
        result = require_shipping()
        assert result is not None
        assert "Shipping API" in result

    def test_require_shipping_present(self, shipping_env: None) -> None:  # noqa: ARG002
        assert require_shipping() is None

    def test_is_shipping_enabled(self, shipping_env: None) -> None:  # noqa: ARG002
        assert is_shipping_enabled() is True

    def test_require_write_no_shipping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AUSPOST_SHIPPING_API_KEY", raising=False)
        result = require_write()
        assert result is not None
        assert "Shipping API" in result

    def test_require_write_disabled(self, shipping_env: None) -> None:  # noqa: ARG002
        result = require_write()
        assert result is not None
        assert "AUSPOST_WRITE_ENABLED" in result

    def test_require_write_enabled(self, write_env: None) -> None:  # noqa: ARG002
        assert require_write() is None

    def test_is_write_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "true")
        assert is_write_enabled() is True
        monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "false")
        assert is_write_enabled() is False
