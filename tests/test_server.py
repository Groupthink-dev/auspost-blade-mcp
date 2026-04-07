"""Tests for MCP tool functions with mocked API clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

from auspost_blade_mcp.server import (
    auspost_account,
    auspost_country_list,
    auspost_create_labels,
    auspost_create_order,
    auspost_create_shipment,
    auspost_domestic_calculate,
    auspost_domestic_services,
    auspost_get_labels,
    auspost_get_order,
    auspost_get_prices,
    auspost_get_shipments,
    auspost_international_calculate,
    auspost_international_services,
    auspost_letter_calculate,
    auspost_letter_services,
    auspost_locations,
    auspost_parcel_sizes,
    auspost_postcode_search,
    auspost_track,
    auspost_validate_address,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    import pytest

# ============================================================
# PAC tools (Tier 1 — free)
# ============================================================


class TestPostcodeSearch:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.postcode_search.return_value = [
            {"postcode": "7000", "location": "HOBART", "state": "TAS", "category": "Delivery Area"},
        ]
        result = await auspost_postcode_search("Hobart")
        assert "7000 HOBART" in result
        patch_pac.postcode_search.assert_awaited_once_with("Hobart", None)

    async def test_with_state(self, patch_pac: MagicMock) -> None:
        patch_pac.postcode_search.return_value = []
        result = await auspost_postcode_search("Sydney", state="NSW")
        assert "No results" in result
        patch_pac.postcode_search.assert_awaited_once_with("Sydney", "NSW")

    async def test_gate_no_key(self) -> None:
        result = await auspost_postcode_search("test")
        assert "AUSPOST_API_KEY" in result


class TestDomesticServices:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.domestic_parcel_services.return_value = [
            {"code": "AUS_PARCEL_REGULAR", "name": "Parcel Post", "price": "12.50"},
        ]
        result = await auspost_domestic_services("7000", "2000", 30, 20, 10, 2.0)
        assert "AUS_PARCEL_REGULAR" in result
        assert "$12.50" in result


class TestDomesticCalculate:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.domestic_parcel_calculate.return_value = {
            "service": "Parcel Post",
            "total_cost": "12.50",
            "delivery_time": "2-4 business days",
            "costs": {"cost": []},
        }
        result = await auspost_domestic_calculate("7000", "2000", 30, 20, 10, 2.0, "AUS_PARCEL_REGULAR")
        assert "Total: $12.50" in result


class TestInternationalServices:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.international_parcel_services.return_value = [
            {"code": "INT_PARCEL_STD_OWN_PACKAGING", "name": "International Standard", "price": "35.00"},
        ]
        result = await auspost_international_services("US", 1.5)
        assert "INT_PARCEL_STD_OWN_PACKAGING" in result


class TestInternationalCalculate:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.international_parcel_calculate.return_value = {
            "service": "International Standard",
            "total_cost": "35.00",
            "costs": {"cost": []},
        }
        result = await auspost_international_calculate("US", 1.5, "INT_PARCEL_STD_OWN_PACKAGING")
        assert "Total: $35.00" in result


class TestLetterServices:
    async def test_domestic(self, patch_pac: MagicMock) -> None:
        patch_pac.domestic_letter_services.return_value = [
            {"code": "AUS_LETTER_REGULAR_SMALL", "name": "Regular Letter", "price": "1.20"},
        ]
        result = await auspost_letter_services("domestic")
        assert "AUS_LETTER_REGULAR_SMALL" in result

    async def test_international_requires_country(self, patch_pac: MagicMock) -> None:  # noqa: ARG002
        result = await auspost_letter_services("international")
        assert "country_code required" in result


class TestLetterCalculate:
    async def test_domestic(self, patch_pac: MagicMock) -> None:
        patch_pac.domestic_letter_calculate.return_value = {
            "service": "Regular Letter",
            "total_cost": "1.20",
            "costs": {"cost": []},
        }
        result = await auspost_letter_calculate("AUS_LETTER_REGULAR_SMALL", 0.05)
        assert "Total: $1.20" in result


class TestParcelSizes:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.parcel_sizes.return_value = [
            {"name": "Bx1", "length": "22", "width": "16", "height": "7.7"},
        ]
        result = await auspost_parcel_sizes()
        assert "Bx1: 22x16x7.7cm" in result


class TestCountryList:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.country_list.return_value = [
            {"code": "AU", "name": "Australia"},
            {"code": "NZ", "name": "New Zealand"},
        ]
        result = await auspost_country_list()
        assert "2 countries" in result


class TestLocations:
    async def test_success(self, patch_pac: MagicMock) -> None:
        patch_pac.locations_by_postcode.return_value = [
            {"location": "HOBART GPO", "state": "TAS", "postcode": "7000", "category": "Post Office"},
        ]
        result = await auspost_locations("7000")
        assert "HOBART GPO" in result


# ============================================================
# Shipping tools (Tier 2 — eParcel contract)
# ============================================================


class TestAccount:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.get_account.return_value = {
            "account_number": "1234567890",
            "name": "Test Co",
            "valid_from": "2026-01-01",
            "valid_to": "2027-01-01",
            "expired": False,
            "details": {},
            "postage_products": [],
        }
        result = await auspost_account()
        assert "Account: 1234567890" in result

    async def test_gate_no_creds(self) -> None:
        result = await auspost_account()
        assert "Shipping API" in result


class TestValidateAddress:
    async def test_valid(self, patch_shipping: MagicMock) -> None:
        patch_shipping.validate_address.return_value = {"found": True}
        result = await auspost_validate_address("HOBART", "TAS", "7000")
        assert "Valid" in result


class TestCreateShipment:
    async def test_write_gate(self, patch_shipping: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG002
        monkeypatch.delenv("AUSPOST_WRITE_ENABLED", raising=False)
        result = await auspost_create_shipment(
            "Sender",
            ["1 Test St"],
            "HOBART",
            "TAS",
            "7000",
            "Recipient",
            ["2 Test St"],
            "SYDNEY",
            "NSW",
            "2000",
            "T28",
            2.0,
        )
        assert "AUSPOST_WRITE_ENABLED" in result

    async def test_success(self, patch_shipping: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "true")
        patch_shipping.create_shipment.return_value = {
            "shipments": [
                {
                    "shipment_id": "SHIP-001",
                    "shipment_reference": "",
                    "shipment_summary": {"status": "Created", "total_cost": "12.00"},
                    "items": [],
                }
            ],
        }
        result = await auspost_create_shipment(
            "Sender",
            ["1 Test St"],
            "HOBART",
            "TAS",
            "7000",
            "Recipient",
            ["2 Test St"],
            "SYDNEY",
            "NSW",
            "2000",
            "T28",
            2.0,
        )
        assert "SHIP-001" in result
        assert "Created" in result


class TestCreateOrder:
    async def test_confirm_gate(self, patch_shipping: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG002
        monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "true")
        result = await auspost_create_order("REF-1", ["SHIP-1"], confirm=False)
        assert "confirm=true" in result

    async def test_success(self, patch_shipping: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AUSPOST_WRITE_ENABLED", "true")
        patch_shipping.create_order.return_value = {
            "order": {
                "order_id": "ORD-1",
                "order_reference": "REF-1",
                "order_creation_date": "2026-04-07",
                "order_summary": {
                    "total_cost": "12.00",
                    "status": "Initiated",
                    "number_of_shipments": 1,
                    "number_of_items": 1,
                },
                "shipments": [],
            },
        }
        result = await auspost_create_order("REF-1", ["SHIP-1"], confirm=True)
        assert "ORD-1" in result


class TestGetShipments:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.get_shipments.return_value = {"shipments": [], "pagination": {}}
        result = await auspost_get_shipments()
        assert "No shipments" in result


class TestGetOrder:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.get_order.return_value = {
            "order": {
                "order_id": "ORD-1",
                "order_reference": "REF",
                "order_creation_date": "2026-04-07",
                "order_summary": {},
                "shipments": [],
            },
        }
        result = await auspost_get_order("ORD-1")
        assert "ORD-1" in result


class TestCreateLabels:
    async def test_write_gate(self, patch_shipping: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG002
        monkeypatch.delenv("AUSPOST_WRITE_ENABLED", raising=False)
        result = await auspost_create_labels(["SHIP-1"])
        assert "AUSPOST_WRITE_ENABLED" in result


class TestGetLabels:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.get_labels.return_value = {
            "labels": [{"request_id": "LBL-1", "status": "AVAILABLE", "url": "https://example.com/label.pdf"}],
        }
        result = await auspost_get_labels("LBL-1")
        assert "AVAILABLE" in result


class TestGetPrices:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.get_item_prices.return_value = {
            "items": [
                {
                    "product_id": "T28",
                    "product_type": "Parcel Post",
                    "calculated_price": "8.95",
                    "calculated_gst": "0.81",
                }
            ],
        }
        result = await auspost_get_prices("7000", "2000", [{"weight": 2.0}])
        assert "T28" in result
        assert "$8.95" in result


class TestTrack:
    async def test_success(self, patch_shipping: MagicMock) -> None:
        patch_shipping.track.return_value = {
            "tracking_results": [
                {
                    "tracking_id": "ABC123",
                    "status": "Delivered",
                    "trackable_items": [
                        {
                            "article_id": "ART1",
                            "product_type": "Parcel Post",
                            "status": "Delivered",
                            "events": [{"date": "2026-04-07", "location": "HOBART", "description": "Delivered"}],
                        }
                    ],
                }
            ],
        }
        result = await auspost_track("ABC123")
        assert "ABC123" in result
        assert "Delivered" in result
