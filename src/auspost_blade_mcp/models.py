"""Configuration, constants, and security gates."""

from __future__ import annotations

import os
from dataclasses import dataclass

# Australian states for validation
VALID_STATES = frozenset({"ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"})

# Location types for Locations API
LOCATION_TYPES = frozenset(
    {
        "POST_OFFICE",
        "PARCEL_LOCKER",
        "PARCEL_COLLECT",
        "RED_BOX",
        "EXPRESS_POST_BOX",
        "BUSINESS_HUB",
    }
)


@dataclass(frozen=True)
class PACConfig:
    """PAC (Postage Assessment Calculator) API config — free tier."""

    api_key: str

    @classmethod
    def from_env(cls) -> PACConfig | None:
        key = os.environ.get("AUSPOST_API_KEY", "").strip()
        if not key:
            return None
        return cls(api_key=key)


@dataclass(frozen=True)
class ShippingConfig:
    """Shipping & Tracking API config — requires eParcel contract."""

    api_key: str
    api_password: str
    account_number: str
    test_mode: bool = False

    @classmethod
    def from_env(cls) -> ShippingConfig | None:
        key = os.environ.get("AUSPOST_SHIPPING_API_KEY", "").strip()
        password = os.environ.get("AUSPOST_SHIPPING_API_PASSWORD", "").strip()
        account = os.environ.get("AUSPOST_ACCOUNT_NUMBER", "").strip()
        if not all([key, password, account]):
            return None
        test_mode = os.environ.get("AUSPOST_SHIPPING_TEST_MODE", "").lower() == "true"
        return cls(api_key=key, api_password=password, account_number=account, test_mode=test_mode)


def is_shipping_enabled() -> bool:
    """Check if Shipping & Tracking API credentials are configured."""
    return ShippingConfig.from_env() is not None


def is_write_enabled() -> bool:
    """Check if write operations (create shipments, orders, labels) are enabled."""
    return os.environ.get("AUSPOST_WRITE_ENABLED", "").lower() == "true"


def require_pac() -> str | None:
    """Gate: return error string if PAC API key is not configured."""
    if PACConfig.from_env() is None:
        return "Error: AUSPOST_API_KEY not configured. Get a free key at https://developers.auspost.com.au"
    return None


def require_shipping() -> str | None:
    """Gate: return error string if Shipping API is not configured."""
    if not is_shipping_enabled():
        return (
            "Error: Shipping API not configured. "
            "Set AUSPOST_SHIPPING_API_KEY, AUSPOST_SHIPPING_API_PASSWORD, and AUSPOST_ACCOUNT_NUMBER. "
            "Requires an eParcel or StarTrack contract with Australia Post."
        )
    return None


def require_write() -> str | None:
    """Gate: return error string if write operations are disabled."""
    shipping_gate = require_shipping()
    if shipping_gate:
        return shipping_gate
    if not is_write_enabled():
        return "Error: Write operations disabled. Set AUSPOST_WRITE_ENABLED=true to enable."
    return None
