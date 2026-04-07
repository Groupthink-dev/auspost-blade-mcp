"""Tests for token-efficient output formatters."""

from __future__ import annotations

from auspost_blade_mcp.formatters import (
    format_account,
    format_address_validation,
    format_calculation,
    format_countries,
    format_labels,
    format_locations,
    format_order,
    format_parcel_sizes,
    format_postcodes,
    format_prices,
    format_services,
    format_shipment,
    format_shipments,
    format_tracking,
)


class TestFormatPostcodes:
    def test_empty(self) -> None:
        assert format_postcodes([]) == "No results found."

    def test_single(self) -> None:
        result = format_postcodes(
            [
                {
                    "postcode": "7000",
                    "location": "HOBART",
                    "state": "TAS",
                    "category": "Delivery Area",
                    "latitude": "-42.88",
                    "longitude": "147.33",
                }
            ]
        )
        assert "7000 HOBART, TAS" in result
        assert "[-42.88,147.33]" in result
        assert "Delivery Area" not in result  # filtered out as default category

    def test_multiple(self) -> None:
        result = format_postcodes(
            [
                {"postcode": "2000", "location": "SYDNEY", "state": "NSW", "category": "Delivery Area"},
                {"postcode": "2001", "location": "SYDNEY", "state": "NSW", "category": "PO Boxes"},
            ]
        )
        assert "2000" in result
        assert "2001" in result
        assert "(PO Boxes)" in result


class TestFormatCountries:
    def test_empty(self) -> None:
        assert format_countries([]) == "No countries found."

    def test_list(self) -> None:
        result = format_countries(
            [
                {"code": "AU", "name": "Australia"},
                {"code": "NZ", "name": "New Zealand"},
            ]
        )
        assert "2 countries" in result
        assert "AU | Australia" in result


class TestFormatParcelSizes:
    def test_empty(self) -> None:
        assert format_parcel_sizes([]) == "No size data available."

    def test_sizes(self) -> None:
        result = format_parcel_sizes([{"name": "Bx1", "length": "22", "width": "16", "height": "7.7"}])
        assert "Bx1: 22x16x7.7cm" in result


class TestFormatServices:
    def test_empty(self) -> None:
        assert format_services([]) == "No services available for these parameters."

    def test_service_with_options(self) -> None:
        result = format_services(
            [
                {
                    "code": "AUS_PARCEL_REGULAR",
                    "name": "Parcel Post",
                    "price": "12.50",
                    "max_extra_cover": "5000",
                    "options": {
                        "option": [
                            {
                                "code": "AUS_SERVICE_OPTION_SIGNATURE_ON_DELIVERY",
                                "name": "Signature",
                                "suboptions": {},
                            }
                        ]
                    },
                }
            ]
        )
        assert "AUS_PARCEL_REGULAR" in result
        assert "$12.50" in result
        assert "cover up to $5000" in result
        assert "+AUS_SERVICE_OPTION_SIGNATURE_ON_DELIVERY" in result


class TestFormatCalculation:
    def test_basic(self) -> None:
        result = format_calculation(
            {
                "service": "Parcel Post",
                "total_cost": "12.50",
                "delivery_time": "2-4 business days",
                "costs": {"cost": [{"item": "Parcel Post", "cost": "12.50"}]},
            }
        )
        assert "Service: Parcel Post" in result
        assert "Total: $12.50" in result
        assert "Delivery: 2-4 business days" in result


class TestFormatAccount:
    def test_basic(self) -> None:
        result = format_account(
            {
                "account_number": "1234567890",
                "name": "Test Co",
                "valid_from": "2026-01-01",
                "valid_to": "2027-01-01",
                "expired": False,
                "details": {"abn": "12345678901"},
                "postage_products": [{"type": "Parcel Post"}],
            }
        )
        assert "Account: 1234567890" in result
        assert "Name: Test Co" in result
        assert "ABN: 12345678901" in result
        assert "Products: Parcel Post" in result


class TestFormatAddressValidation:
    def test_valid(self) -> None:
        assert "Valid" in format_address_validation({"found": True})

    def test_invalid_with_suggestions(self) -> None:
        result = format_address_validation({"found": False, "results": ["SYDNEY NSW 2000"]})
        assert "Invalid" in result
        assert "SYDNEY NSW 2000" in result

    def test_invalid_no_suggestions(self) -> None:
        result = format_address_validation({"found": False, "results": []})
        assert "Invalid" in result


class TestFormatShipment:
    def test_basic(self) -> None:
        result = format_shipment(
            {
                "shipment_id": "abc123",
                "shipment_reference": "ORDER-001",
                "shipment_summary": {"status": "Created", "total_cost": "15.00"},
                "items": [
                    {
                        "item_id": "item1",
                        "product_id": "T28",
                        "weight": 2.5,
                        "tracking_details": {"article_id": "ART001"},
                    }
                ],
            }
        )
        assert "Shipment: abc123" in result
        assert "Status: Created" in result
        assert "Cost: $15.00" in result
        assert "T28 2.5kg" in result


class TestFormatShipments:
    def test_empty(self) -> None:
        assert format_shipments({"shipments": []}) == "No shipments found."


class TestFormatOrder:
    def test_basic(self) -> None:
        result = format_order(
            {
                "order_id": "ORD-001",
                "order_reference": "MY-ORDER",
                "order_creation_date": "2026-04-07",
                "order_summary": {
                    "total_cost": "30.00",
                    "status": "Initiated",
                    "number_of_shipments": 2,
                    "number_of_items": 3,
                },
                "shipments": [],
            }
        )
        assert "Order: ORD-001" in result
        assert "Cost: $30.00" in result


class TestFormatLabels:
    def test_empty(self) -> None:
        assert format_labels({"labels": []}) == "No labels generated."

    def test_with_url(self) -> None:
        result = format_labels(
            {"labels": [{"request_id": "LBL-1", "status": "AVAILABLE", "url": "https://example.com/label.pdf"}]}
        )
        assert "AVAILABLE" in result
        assert "https://example.com/label.pdf" in result


class TestFormatPrices:
    def test_empty(self) -> None:
        assert format_prices({"items": []}) == "No pricing data returned."

    def test_item(self) -> None:
        result = format_prices(
            {
                "items": [
                    {
                        "product_id": "T28",
                        "product_type": "Parcel Post",
                        "calculated_price": "8.95",
                        "calculated_gst": "0.81",
                        "item_reference": "ITEM-1",
                    }
                ]
            }
        )
        assert "T28 (Parcel Post): $8.95" in result
        assert "ITEM-1" in result


class TestFormatTracking:
    def test_empty(self) -> None:
        assert format_tracking({"tracking_results": []}) == "No tracking data returned."

    def test_with_events(self) -> None:
        result = format_tracking(
            {
                "tracking_results": [
                    {
                        "tracking_id": "ABC123",
                        "status": "Delivered",
                        "trackable_items": [
                            {
                                "article_id": "ART1",
                                "product_type": "Parcel Post",
                                "status": "Delivered",
                                "events": [
                                    {
                                        "date": "2026-04-07T10:00:00",
                                        "location": "HOBART TAS",
                                        "description": "Delivered",
                                    },
                                    {
                                        "date": "2026-04-06T08:00:00",
                                        "location": "HOBART TAS",
                                        "description": "With driver",
                                    },
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        assert "Track: ABC123" in result
        assert "Delivered" in result
        assert "HOBART TAS" in result

    def test_error_tracking(self) -> None:
        result = format_tracking(
            {
                "tracking_results": [
                    {
                        "tracking_id": "BAD123",
                        "status": "Error",
                        "errors": [{"message": "Invalid tracking ID"}],
                    }
                ]
            }
        )
        assert "Error: Invalid tracking ID" in result


class TestFormatLocations:
    def test_empty(self) -> None:
        assert format_locations([]) == "No locations found."

    def test_locations(self) -> None:
        result = format_locations(
            [
                {
                    "location": "HOBART",
                    "state": "TAS",
                    "postcode": "7000",
                    "category": "Post Office",
                    "latitude": "-42.88",
                    "longitude": "147.33",
                }
            ]
        )
        assert "1 locations" in result
        assert "HOBART, TAS 7000" in result
        assert "(Post Office)" in result
