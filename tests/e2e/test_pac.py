"""End-to-end tests against live AusPost PAC API.

Requires AUSPOST_API_KEY environment variable.
Run with: make test-e2e
"""

from __future__ import annotations

import pytest

from auspost_blade_mcp.client import PACClient
from auspost_blade_mcp.models import PACConfig

pytestmark = pytest.mark.e2e


@pytest.fixture
def client() -> PACClient | None:
    config = PACConfig.from_env()
    if config is None:
        pytest.skip("AUSPOST_API_KEY not set")
        return None
    return PACClient(config)


async def test_postcode_search(client: PACClient) -> None:
    results = await client.postcode_search("Hobart", state="TAS")
    assert len(results) > 0
    assert any(r["postcode"] == "7000" for r in results)


async def test_country_list(client: PACClient) -> None:
    countries = await client.country_list()
    assert len(countries) > 100
    codes = [c["code"] for c in countries]
    assert "AU" in codes
    assert "US" in codes
    assert "NZ" in codes


async def test_parcel_sizes(client: PACClient) -> None:
    sizes = await client.parcel_sizes()
    assert len(sizes) > 0
    names = [s["name"] for s in sizes]
    assert any("Bx" in n for n in names)


async def test_domestic_services(client: PACClient) -> None:
    services = await client.domestic_parcel_services("7000", "2000", 30, 20, 10, 2.0)
    assert len(services) > 0
    codes = [s["code"] for s in services]
    assert "AUS_PARCEL_REGULAR" in codes


async def test_domestic_calculate(client: PACClient) -> None:
    result = await client.domestic_parcel_calculate(
        "7000",
        "2000",
        30,
        20,
        10,
        2.0,
        "AUS_PARCEL_REGULAR",
    )
    assert "total_cost" in result
    cost = float(result["total_cost"])
    assert cost > 0


async def test_international_services(client: PACClient) -> None:
    services = await client.international_parcel_services("US", 1.5)
    assert len(services) > 0


async def test_domestic_letter_services(client: PACClient) -> None:
    services = await client.domestic_letter_services()
    assert len(services) > 0
