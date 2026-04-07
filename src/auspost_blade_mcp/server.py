"""AusPost Blade MCP server — 21 tools across PAC, Locations, and Shipping tiers."""

from __future__ import annotations

import asyncio
import os
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from auspost_blade_mcp.client import AusPostError, PACClient, ShippingClient
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
from auspost_blade_mcp.models import PACConfig, ShippingConfig, require_pac, require_shipping, require_write

mcp = FastMCP(
    "AusPostBlade",
    instructions=(
        "Australia Post MCP server. Postage calculator, shipping, tracking, and locations "
        "via official AusPost APIs. Free tier (PAC + Locations) requires AUSPOST_API_KEY only. "
        "Shipping & Tracking requires eParcel contract credentials. "
        "Write operations require AUSPOST_WRITE_ENABLED=true."
    ),
)

# --- Client singletons (lazy init) ---

_pac_client: PACClient | None = None
_shipping_client: ShippingClient | None = None
_lock = asyncio.Lock()


async def _get_pac() -> PACClient:
    global _pac_client  # noqa: PLW0603
    async with _lock:
        if _pac_client is None:
            config = PACConfig.from_env()
            if config is None:
                msg = "AUSPOST_API_KEY not configured"
                raise ValueError(msg)
            _pac_client = PACClient(config)
        return _pac_client


async def _get_shipping() -> ShippingClient:
    global _shipping_client  # noqa: PLW0603
    async with _lock:
        if _shipping_client is None:
            config = ShippingConfig.from_env()
            if config is None:
                msg = "Shipping API credentials not configured"
                raise ValueError(msg)
            _shipping_client = ShippingClient(config)
        return _shipping_client


def _error(e: Exception) -> str:
    if isinstance(e, AusPostError):
        parts = [f"Error ({e.status_code})"]
        if e.code:
            parts.append(f"[{e.code}]")
        parts.append(str(e))
        return ": ".join(parts)
    return f"Error: {e}"


# ============================================================
# TIER 1 — Free API (PAC + Locations) — AUSPOST_API_KEY only
# ============================================================


@mcp.tool()
async def auspost_postcode_search(
    query: Annotated[str, Field(description="Suburb name or postcode to search")],
    state: Annotated[str | None, Field(description="Filter by state (ACT/NSW/NT/QLD/SA/TAS/VIC/WA)")] = None,
) -> str:
    """Search Australian postcodes and suburbs. Returns postcode, suburb name, state, and coordinates."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        results = await client.postcode_search(query, state)
        return format_postcodes(results)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_domestic_services(
    from_postcode: Annotated[str, Field(description="Sender postcode (4 digits)")],
    to_postcode: Annotated[str, Field(description="Recipient postcode (4 digits)")],
    length: Annotated[float, Field(description="Length in cm")],
    width: Annotated[float, Field(description="Width in cm")],
    height: Annotated[float, Field(description="Height in cm")],
    weight: Annotated[float, Field(description="Weight in kg")],
) -> str:
    """List available domestic parcel services with prices for given dimensions and route."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        services = await client.domestic_parcel_services(from_postcode, to_postcode, length, width, height, weight)
        return format_services(services)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_domestic_calculate(
    from_postcode: Annotated[str, Field(description="Sender postcode (4 digits)")],
    to_postcode: Annotated[str, Field(description="Recipient postcode (4 digits)")],
    length: Annotated[float, Field(description="Length in cm")],
    width: Annotated[float, Field(description="Width in cm")],
    height: Annotated[float, Field(description="Height in cm")],
    weight: Annotated[float, Field(description="Weight in kg")],
    service_code: Annotated[str, Field(description="Service code (e.g. AUS_PARCEL_REGULAR, AUS_PARCEL_EXPRESS)")],
    option_code: Annotated[str | None, Field(description="Optional add-on code")] = None,
    suboption_code: Annotated[str | None, Field(description="Optional sub-option code")] = None,
    extra_cover: Annotated[float | None, Field(description="Extra cover amount in AUD")] = None,
) -> str:
    """Calculate domestic parcel postage for a specific service.

    Use auspost_domestic_services first to find available service codes.
    """
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        result = await client.domestic_parcel_calculate(
            from_postcode,
            to_postcode,
            length,
            width,
            height,
            weight,
            service_code,
            option_code,
            suboption_code,
            extra_cover,
        )
        return format_calculation(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_international_services(
    country_code: Annotated[str, Field(description="2-letter ISO country code (e.g. US, GB, NZ)")],
    weight: Annotated[float, Field(description="Weight in kg")],
) -> str:
    """List available international parcel services with prices for a given country and weight."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        services = await client.international_parcel_services(country_code, weight)
        return format_services(services)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_international_calculate(
    country_code: Annotated[str, Field(description="2-letter ISO country code")],
    weight: Annotated[float, Field(description="Weight in kg")],
    service_code: Annotated[str, Field(description="Service code from auspost_international_services")],
    option_code: Annotated[str | None, Field(description="Optional add-on code")] = None,
    extra_cover: Annotated[float | None, Field(description="Extra cover amount in AUD")] = None,
) -> str:
    """Calculate international parcel postage cost for a specific service."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        result = await client.international_parcel_calculate(
            country_code,
            weight,
            service_code,
            option_code,
            extra_cover,
        )
        return format_calculation(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_letter_services(
    scope: Annotated[str, Field(description="'domestic' or 'international'")] = "domestic",
    country_code: Annotated[
        str | None,
        Field(description="2-letter ISO country code (required for international)"),
    ] = None,
    weight: Annotated[float, Field(description="Weight in kg")] = 0.25,
) -> str:
    """List available letter services. Use 'domestic' or 'international' scope."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        if scope == "international":
            if not country_code:
                return "Error: country_code required for international letters"
            services = await client.international_letter_services(country_code, weight)
        else:
            services = await client.domestic_letter_services()
        return format_services(services)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_letter_calculate(
    service_code: Annotated[str, Field(description="Service code from auspost_letter_services")],
    weight: Annotated[float, Field(description="Weight in kg")],
    country_code: Annotated[str | None, Field(description="2-letter ISO country code (for international)")] = None,
    option_code: Annotated[str | None, Field(description="Optional add-on code")] = None,
    extra_cover: Annotated[float | None, Field(description="Extra cover amount in AUD")] = None,
) -> str:
    """Calculate letter postage cost. Omit country_code for domestic."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        if country_code:
            result = await client.international_letter_calculate(
                country_code,
                weight,
                service_code,
                option_code,
                extra_cover,
            )
        else:
            result = await client.domestic_letter_calculate(service_code, weight)
        return format_calculation(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_parcel_sizes() -> str:
    """List standard Australia Post parcel box sizes (dimensions reference data)."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        sizes = await client.parcel_sizes()
        return format_parcel_sizes(sizes)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_country_list() -> str:
    """List all countries with 2-letter ISO codes for international postage."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        countries = await client.country_list()
        return format_countries(countries)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_locations(
    postcode: Annotated[str, Field(description="Postcode to search near (4 digits)")],
    types: Annotated[
        str | None,
        Field(description="Comma-separated: POST_OFFICE,PARCEL_LOCKER,PARCEL_COLLECT,RED_BOX,BUSINESS_HUB"),
    ] = None,
) -> str:
    """Find Australia Post locations (post offices, parcel lockers) near a postcode."""
    gate = require_pac()
    if gate:
        return gate
    try:
        client = await _get_pac()
        type_list = [t.strip() for t in types.split(",")] if types else None
        results = await client.locations_by_postcode(postcode, type_list)
        return format_locations(results)
    except Exception as e:
        return _error(e)


# ============================================================
# TIER 2 — Shipping & Tracking (eParcel contract required)
# ============================================================


@mcp.tool()
async def auspost_account() -> str:
    """Get eParcel account details, products, and status."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        account = await client.get_account()
        return format_account(account)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_validate_address(
    suburb: Annotated[str, Field(description="Suburb name")],
    state: Annotated[str, Field(description="State code (ACT/NSW/NT/QLD/SA/TAS/VIC/WA)")],
    postcode: Annotated[str, Field(description="Postcode (4 digits)")],
) -> str:
    """Validate an Australian suburb/state/postcode combination."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        result = await client.validate_address(suburb, state, postcode)
        return format_address_validation(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_create_shipment(
    from_name: Annotated[str, Field(description="Sender name")],
    from_lines: Annotated[list[str], Field(description="Sender address lines")],
    from_suburb: Annotated[str, Field(description="Sender suburb")],
    from_state: Annotated[str, Field(description="Sender state")],
    from_postcode: Annotated[str, Field(description="Sender postcode")],
    to_name: Annotated[str, Field(description="Recipient name")],
    to_lines: Annotated[list[str], Field(description="Recipient address lines")],
    to_suburb: Annotated[str, Field(description="Recipient suburb")],
    to_state: Annotated[str, Field(description="Recipient state")],
    to_postcode: Annotated[str, Field(description="Recipient postcode")],
    product_id: Annotated[str, Field(description="Product ID (e.g. T28, E34, T28S, E34S)")],
    weight: Annotated[float, Field(description="Item weight in kg")],
    length: Annotated[float | None, Field(description="Length in cm")] = None,
    width: Annotated[float | None, Field(description="Width in cm")] = None,
    height: Annotated[float | None, Field(description="Height in cm")] = None,
    shipment_reference: Annotated[str | None, Field(description="Your reference for this shipment")] = None,
    email_tracking: Annotated[bool, Field(description="Send tracking emails")] = False,
) -> str:
    """Create a domestic shipment. Requires AUSPOST_WRITE_ENABLED=true."""
    gate = require_write()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        item: dict = {"product_id": product_id, "weight": weight}
        if length:
            item["length"] = length
        if width:
            item["width"] = width
        if height:
            item["height"] = height
        shipment: dict = {
            "from": {
                "name": from_name,
                "lines": from_lines,
                "suburb": from_suburb,
                "state": from_state.upper(),
                "postcode": from_postcode,
            },
            "to": {
                "name": to_name,
                "lines": to_lines,
                "suburb": to_suburb,
                "state": to_state.upper(),
                "postcode": to_postcode,
            },
            "items": [item],
            "email_tracking_enabled": email_tracking,
        }
        if shipment_reference:
            shipment["shipment_reference"] = shipment_reference
        result = await client.create_shipment([shipment])
        shipments = result.get("shipments", [])
        if shipments:
            return format_shipment(shipments[0])
        return "Shipment created (no details returned)"
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_get_shipments(
    shipment_ids: Annotated[str | None, Field(description="Comma-separated shipment IDs")] = None,
    status: Annotated[str | None, Field(description="Filter by status")] = None,
    limit: Annotated[int, Field(description="Max results")] = 10,
) -> str:
    """List or retrieve shipments by ID or status."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        ids = [i.strip() for i in shipment_ids.split(",")] if shipment_ids else None
        result = await client.get_shipments(ids, status, limit=limit)
        return format_shipments(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_create_order(
    order_reference: Annotated[str, Field(description="Your reference for this order")],
    shipment_ids: Annotated[list[str], Field(description="Shipment IDs to include in the order")],
    confirm: Annotated[bool, Field(description="Must be true — orders cannot be cancelled after creation")] = False,
) -> str:
    """Finalise shipments into an order for despatch. IRREVERSIBLE — orders cannot be cancelled or deleted."""
    gate = require_write()
    if gate:
        return gate
    if not confirm:
        return (
            "Error: Set confirm=true to create the order. "
            "WARNING: Orders cannot be cancelled, deleted, or voided after creation."
        )
    try:
        client = await _get_shipping()
        result = await client.create_order(order_reference, shipment_ids)
        return format_order(result.get("order", result))
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_get_order(
    order_id: Annotated[str, Field(description="Order ID to retrieve")],
) -> str:
    """Get order details by ID."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        result = await client.get_order(order_id)
        return format_order(result.get("order", result))
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_create_labels(
    shipment_ids: Annotated[list[str], Field(description="Shipment IDs to generate labels for")],
    layout: Annotated[
        str,
        Field(description="Layout: A4-1pp, A4-3pp, A4-4pp, A6-1pp, THERMAL-LABEL-A6-1PP"),
    ] = "A4-1pp",
    branded: Annotated[bool, Field(description="Include Australia Post branding")] = True,
) -> str:
    """Generate shipping labels for shipments. Requires AUSPOST_WRITE_ENABLED=true."""
    gate = require_write()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        result = await client.create_labels(shipment_ids, layout, branded)
        return format_labels(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_get_labels(
    request_id: Annotated[str, Field(description="Label request ID from auspost_create_labels")],
) -> str:
    """Check label generation status and get download URL."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        result = await client.get_labels(request_id)
        return format_labels(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_get_prices(
    from_postcode: Annotated[str, Field(description="Sender postcode")],
    to_postcode: Annotated[str, Field(description="Recipient postcode")],
    items: Annotated[list[dict], Field(description="Items: [{weight, length, width, height, item_reference}]")],
) -> str:
    """Get contract-rate pricing for items (eParcel rates, not retail)."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        result = await client.get_item_prices(from_postcode, to_postcode, items)
        return format_prices(result)
    except Exception as e:
        return _error(e)


@mcp.tool()
async def auspost_track(
    tracking_ids: Annotated[
        str,
        Field(description="Comma-separated tracking/article IDs (max 10). No mixed AusPost/StarTrack."),
    ],
) -> str:
    """Track parcels by tracking ID. Rate limited to 10 requests/minute, max 10 IDs per call."""
    gate = require_shipping()
    if gate:
        return gate
    try:
        client = await _get_shipping()
        ids = [i.strip() for i in tracking_ids.split(",")][:10]
        result = await client.track(ids)
        return format_tracking(result)
    except Exception as e:
        return _error(e)


# ============================================================
# Entry point
# ============================================================


def main() -> None:
    """Run the AusPost Blade MCP server."""
    transport = os.environ.get("AUSPOST_MCP_TRANSPORT", "stdio")
    if transport == "http":
        from auspost_blade_mcp.auth import BearerAuthMiddleware

        mcp.settings.http_app_kwargs = {"middleware": [BearerAuthMiddleware]}
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8810)
    else:
        mcp.run(transport="stdio")
