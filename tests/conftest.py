"""Shared fixtures for auspost-blade-mcp tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_clients():
    """Reset client singletons between tests."""
    import auspost_blade_mcp.server as srv

    srv._pac_client = None
    srv._shipping_client = None
    yield
    srv._pac_client = None
    srv._shipping_client = None


@pytest.fixture
def pac_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set PAC API key in environment."""
    monkeypatch.setenv("AUSPOST_API_KEY", "test-pac-key-12345")


@pytest.fixture
def shipping_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set Shipping API credentials in environment."""
    monkeypatch.setenv("AUSPOST_SHIPPING_API_KEY", "test-shipping-key")
    monkeypatch.setenv("AUSPOST_SHIPPING_API_PASSWORD", "test-shipping-pass")
    monkeypatch.setenv("AUSPOST_ACCOUNT_NUMBER", "1234567890")


@pytest.fixture
def write_env(monkeypatch: pytest.MonkeyPatch, shipping_env: None) -> None:  # noqa: ARG001
    """Enable write operations."""
    monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "true")


@pytest.fixture
def mock_pac_client() -> MagicMock:
    """Mock PACClient with AsyncMock methods."""
    client = MagicMock()
    client.postcode_search = AsyncMock()
    client.country_list = AsyncMock()
    client.parcel_sizes = AsyncMock()
    client.domestic_parcel_services = AsyncMock()
    client.domestic_parcel_calculate = AsyncMock()
    client.international_parcel_services = AsyncMock()
    client.international_parcel_calculate = AsyncMock()
    client.domestic_letter_services = AsyncMock()
    client.domestic_letter_calculate = AsyncMock()
    client.international_letter_services = AsyncMock()
    client.international_letter_calculate = AsyncMock()
    client.locations_by_postcode = AsyncMock()
    return client


@pytest.fixture
def mock_shipping_client() -> MagicMock:
    """Mock ShippingClient with AsyncMock methods."""
    client = MagicMock()
    client.get_account = AsyncMock()
    client.validate_address = AsyncMock()
    client.create_shipment = AsyncMock()
    client.get_shipments = AsyncMock()
    client.update_items = AsyncMock()
    client.delete_item = AsyncMock()
    client.create_order = AsyncMock()
    client.get_order = AsyncMock()
    client.create_labels = AsyncMock()
    client.get_labels = AsyncMock()
    client.get_item_prices = AsyncMock()
    client.track = AsyncMock()
    return client


@pytest.fixture
def patch_pac(mock_pac_client: MagicMock, pac_env: None):  # noqa: ARG001
    """Patch _get_pac to return mock client."""
    with patch("auspost_blade_mcp.server._get_pac", return_value=mock_pac_client):
        yield mock_pac_client


@pytest.fixture
def patch_shipping(mock_shipping_client: MagicMock, shipping_env: None):  # noqa: ARG001
    """Patch _get_shipping to return mock client."""
    with patch("auspost_blade_mcp.server._get_shipping", return_value=mock_shipping_client):
        yield mock_shipping_client
