"""Tests for API client error handling and request construction."""

from __future__ import annotations

import httpx
import pytest
import respx

from auspost_blade_mcp.client import AusPostError, PACClient, ShippingClient, _scrub_error
from auspost_blade_mcp.models import PACConfig, ShippingConfig


class TestScrubError:
    def test_api_error_format(self) -> None:
        response = httpx.Response(
            status_code=400,
            json={"errors": [{"code": "42011", "message": "Two dimensions must be >= 5cm"}]},
        )
        err = _scrub_error(response)
        assert err.status_code == 400
        assert err.code == "42011"
        assert "5cm" in str(err)

    def test_legacy_error_format(self) -> None:
        response = httpx.Response(
            status_code=401,
            json={"error": {"errorMessage": "Invalid API key"}},
        )
        err = _scrub_error(response)
        assert err.status_code == 401
        assert "Invalid API key" in str(err)

    def test_non_json_error(self) -> None:
        response = httpx.Response(status_code=500, text="Internal Server Error")
        err = _scrub_error(response)
        assert err.status_code == 500

    def test_no_credentials_in_error(self) -> None:
        """Credentials must never appear in error messages."""
        response = httpx.Response(
            status_code=401,
            json={"errors": [{"code": "API_001", "message": "Authentication failed"}]},
        )
        err = _scrub_error(response)
        assert "key" not in str(err).lower() or "api_key" not in str(err).lower()


class TestPACClient:
    @pytest.fixture
    def client(self) -> PACClient:
        return PACClient(PACConfig(api_key="test-key"))

    @respx.mock
    async def test_postcode_search(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postcode/search.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "localities": {
                        "locality": [
                            {"postcode": "7000", "location": "HOBART", "state": "TAS"},
                        ]
                    },
                },
            ),
        )
        result = await client.postcode_search("Hobart")
        assert len(result) == 1
        assert result[0]["postcode"] == "7000"

    @respx.mock
    async def test_postcode_search_single_result_wrapping(self, client: PACClient) -> None:
        """AusPost returns a dict instead of list for single results."""
        respx.get("https://digitalapi.auspost.com.au/postcode/search.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "localities": {"locality": {"postcode": "7000", "location": "HOBART", "state": "TAS"}},
                },
            ),
        )
        result = await client.postcode_search("7000")
        assert isinstance(result, list)
        assert len(result) == 1

    @respx.mock
    async def test_country_list(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postage/country.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "countries": {"country": [{"code": "AU", "name": "Australia"}]},
                },
            ),
        )
        result = await client.country_list()
        assert len(result) == 1

    @respx.mock
    async def test_domestic_services(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postage/parcel/domestic/service.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "services": {"service": [{"code": "AUS_PARCEL_REGULAR", "name": "Parcel Post", "price": "12.50"}]},
                },
            ),
        )
        result = await client.domestic_parcel_services("7000", "2000", 30, 20, 10, 2.0)
        assert result[0]["code"] == "AUS_PARCEL_REGULAR"

    @respx.mock
    async def test_api_error(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postcode/search.json").mock(
            return_value=httpx.Response(
                401,
                json={
                    "error": {"errorMessage": "Invalid API key"},
                },
            ),
        )
        with pytest.raises(AusPostError) as exc_info:
            await client.postcode_search("test")
        assert exc_info.value.status_code == 401

    @respx.mock
    async def test_domestic_calculate(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postage/parcel/domestic/calculate.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "postage_result": {"service": "Parcel Post", "total_cost": "12.50"},
                },
            ),
        )
        result = await client.domestic_parcel_calculate("7000", "2000", 30, 20, 10, 2.0, "AUS_PARCEL_REGULAR")
        assert result["total_cost"] == "12.50"

    @respx.mock
    async def test_international_services(self, client: PACClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/postage/parcel/international/service.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "services": {"service": [{"code": "INT_PARCEL_STD", "name": "Standard", "price": "35.00"}]},
                },
            ),
        )
        result = await client.international_parcel_services("US", 1.5)
        assert result[0]["code"] == "INT_PARCEL_STD"


class TestShippingClient:
    @pytest.fixture
    def client(self) -> ShippingClient:
        return ShippingClient(
            ShippingConfig(
                api_key="test-key",
                api_password="test-pass",  # noqa: S106
                account_number="1234567890",
                test_mode=False,
            )
        )

    @pytest.fixture
    def test_client(self) -> ShippingClient:
        return ShippingClient(
            ShippingConfig(
                api_key="test-key",
                api_password="test-pass",  # noqa: S106
                account_number="1234567890",
                test_mode=True,
            )
        )

    @respx.mock
    async def test_get_account(self, client: ShippingClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/shipping/v1/accounts/1234567890").mock(
            return_value=httpx.Response(200, json={"account_number": "1234567890", "name": "Test"}),
        )
        result = await client.get_account()
        assert result["account_number"] == "1234567890"

    @respx.mock
    async def test_validate_address(self, client: ShippingClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/shipping/v1/address").mock(
            return_value=httpx.Response(200, json={"found": True}),
        )
        result = await client.validate_address("HOBART", "TAS", "7000")
        assert result["found"] is True

    @respx.mock
    async def test_track(self, client: ShippingClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/shipping/v1/track").mock(
            return_value=httpx.Response(
                200,
                json={
                    "tracking_results": [{"tracking_id": "ABC123", "status": "Delivered"}],
                },
            ),
        )
        result = await client.track(["ABC123"])
        assert result["tracking_results"][0]["status"] == "Delivered"

    @respx.mock
    async def test_track_max_10_ids(self, client: ShippingClient) -> None:
        """Track should truncate to 10 IDs max."""
        ids = [f"ID{i}" for i in range(15)]
        respx.get("https://digitalapi.auspost.com.au/shipping/v1/track").mock(
            return_value=httpx.Response(200, json={"tracking_results": []}),
        )
        await client.track(ids)
        call = respx.calls.last
        assert call is not None
        params = dict(call.request.url.params)
        actual_ids = params["tracking_ids"].split(",")
        assert len(actual_ids) == 10

    def test_test_mode_url(self, test_client: ShippingClient) -> None:
        """Test mode should use the test base URL."""
        assert "test" in str(test_client._client.base_url)

    @respx.mock
    async def test_rate_limit_error(self, client: ShippingClient) -> None:
        respx.get("https://digitalapi.auspost.com.au/shipping/v1/track").mock(
            return_value=httpx.Response(
                429,
                json={
                    "errors": [{"code": "API_002", "message": "Rate limit exceeded"}],
                },
            ),
        )
        with pytest.raises(AusPostError) as exc_info:
            await client.track(["ABC123"])
        assert exc_info.value.status_code == 429
        assert exc_info.value.code == "API_002"

    @respx.mock
    async def test_create_shipment(self, client: ShippingClient) -> None:
        respx.post("https://digitalapi.auspost.com.au/shipping/v1/shipments").mock(
            return_value=httpx.Response(201, json={"shipments": [{"shipment_id": "S1"}]}),
        )
        result = await client.create_shipment([{"from": {}, "to": {}, "items": []}])
        assert result["shipments"][0]["shipment_id"] == "S1"
