"""API clients for Australia Post PAC, Locations, and Shipping & Tracking APIs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from auspost_blade_mcp.models import PACConfig, ShippingConfig


class AusPostError(Exception):
    """Raised when an AusPost API call fails."""

    def __init__(self, status_code: int, message: str, code: str | None = None) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(message)


def _scrub_error(response: httpx.Response) -> AusPostError:
    """Parse error response without leaking credentials."""
    try:
        body = response.json()
        if "errors" in body:
            errs = body["errors"]
            if isinstance(errs, list) and errs:
                err = errs[0]
                return AusPostError(
                    status_code=response.status_code,
                    message=err.get("message", response.reason_phrase or "Unknown error"),
                    code=err.get("code"),
                )
        if "error" in body:
            return AusPostError(
                status_code=response.status_code,
                message=body["error"].get("errorMessage", str(body["error"])),
            )
    except Exception:  # noqa: S110
        pass
    return AusPostError(
        status_code=response.status_code,
        message=response.reason_phrase or f"HTTP {response.status_code}",
    )


class PACClient:
    """Postage Assessment Calculator + Locations API client (free tier)."""

    BASE_URL = "https://digitalapi.auspost.com.au"

    def __init__(self, config: PACConfig) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"AUTH-KEY": config.api_key},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None) -> dict:
        """GET request with JSON response."""
        url = f"{path}.json"
        resp = await self._client.get(url, params=params)
        if resp.status_code != 200:
            raise _scrub_error(resp)
        return resp.json()  # type: ignore[no-any-return]

    # --- Postcode ---

    async def postcode_search(self, query: str, state: str | None = None) -> list[dict]:
        params: dict[str, str] = {"q": query}
        if state:
            params["state"] = state.upper()
        data = await self._get("/postcode/search", params)
        localities = data.get("localities", {})
        result = localities.get("locality", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]

    # --- Country ---

    async def country_list(self) -> list[dict]:
        data = await self._get("/postage/country")
        countries = data.get("countries", {})
        return countries.get("country", [])

    # --- Parcel sizes ---

    async def parcel_sizes(self) -> list[dict]:
        data = await self._get("/postage/parcel/domestic/size")
        sizes = data.get("sizes", {})
        return sizes.get("size", [])

    # --- Domestic parcel ---

    async def domestic_parcel_services(
        self,
        from_postcode: str,
        to_postcode: str,
        length: float,
        width: float,
        height: float,
        weight: float,
    ) -> list[dict]:
        params = {
            "from_postcode": from_postcode,
            "to_postcode": to_postcode,
            "length": str(length),
            "width": str(width),
            "height": str(height),
            "weight": str(weight),
        }
        data = await self._get("/postage/parcel/domestic/service", params)
        services = data.get("services", {})
        result = services.get("service", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]

    async def domestic_parcel_calculate(
        self,
        from_postcode: str,
        to_postcode: str,
        length: float,
        width: float,
        height: float,
        weight: float,
        service_code: str,
        option_code: str | None = None,
        suboption_code: str | None = None,
        extra_cover: float | None = None,
    ) -> dict:
        params: dict[str, str] = {
            "from_postcode": from_postcode,
            "to_postcode": to_postcode,
            "length": str(length),
            "width": str(width),
            "height": str(height),
            "weight": str(weight),
            "service_code": service_code,
        }
        if option_code:
            params["option_code"] = option_code
        if suboption_code:
            params["suboption_code"] = suboption_code
        if extra_cover is not None:
            params["extra_cover"] = str(extra_cover)
        data = await self._get("/postage/parcel/domestic/calculate", params)
        return data.get("postage_result", data)  # type: ignore[no-any-return]

    # --- International parcel ---

    async def international_parcel_services(
        self,
        country_code: str,
        weight: float,
    ) -> list[dict]:
        params = {"country_code": country_code.upper(), "weight": str(weight)}
        data = await self._get("/postage/parcel/international/service", params)
        services = data.get("services", {})
        result = services.get("service", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]

    async def international_parcel_calculate(
        self,
        country_code: str,
        weight: float,
        service_code: str,
        option_code: str | None = None,
        extra_cover: float | None = None,
    ) -> dict:
        params: dict[str, str] = {
            "country_code": country_code.upper(),
            "weight": str(weight),
            "service_code": service_code,
        }
        if option_code:
            params["option_code"] = option_code
        if extra_cover is not None:
            params["extra_cover"] = str(extra_cover)
        data = await self._get("/postage/parcel/international/calculate", params)
        return data.get("postage_result", data)  # type: ignore[no-any-return]

    # --- Letters ---

    async def domestic_letter_services(self) -> list[dict]:
        data = await self._get("/postage/letter/domestic/service")
        services = data.get("services", {})
        result = services.get("service", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]

    async def domestic_letter_calculate(
        self,
        service_code: str,
        weight: float,
    ) -> dict:
        params = {"service_code": service_code, "weight": str(weight)}
        data = await self._get("/postage/letter/domestic/calculate", params)
        return data.get("postage_result", data)  # type: ignore[no-any-return]

    async def international_letter_services(
        self,
        country_code: str,
        weight: float,
    ) -> list[dict]:
        params = {"country_code": country_code.upper(), "weight": str(weight)}
        data = await self._get("/postage/letter/international/service", params)
        services = data.get("services", {})
        result = services.get("service", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]

    async def international_letter_calculate(
        self,
        country_code: str,
        weight: float,
        service_code: str,
        option_code: str | None = None,
        extra_cover: float | None = None,
    ) -> dict:
        params: dict[str, str] = {
            "country_code": country_code.upper(),
            "weight": str(weight),
            "service_code": service_code,
        }
        if option_code:
            params["option_code"] = option_code
        if extra_cover is not None:
            params["extra_cover"] = str(extra_cover)
        data = await self._get("/postage/letter/international/calculate", params)
        return data.get("postage_result", data)  # type: ignore[no-any-return]

    # --- Locations ---

    async def locations_by_postcode(
        self,
        postcode: str,
        types: list[str] | None = None,
    ) -> list[dict]:
        headers = {**self._client.headers, "Accept": "application/json"}
        params: dict[str, str] = {}
        if types:
            params["types"] = ",".join(t.upper() for t in types)
        resp = await self._client.get(
            "/postcode/search.json",
            params={"q": postcode},
            headers=headers,
        )
        # Locations API uses a different base path in the new portal.
        # Fall back to postcode search for now — documented endpoint may require
        # partner API key. The PAC postcode search returns geo data we can use.
        if resp.status_code != 200:
            raise _scrub_error(resp)
        data = resp.json()
        localities = data.get("localities", {})
        result = localities.get("locality", [])
        if isinstance(result, dict):
            result = [result]
        return result  # type: ignore[no-any-return]


class ShippingClient:
    """Shipping & Tracking API client (requires eParcel contract)."""

    BASE_URL = "https://digitalapi.auspost.com.au/shipping/v1"
    TEST_URL = "https://digitalapi.auspost.com.au/test/shipping/v1"

    def __init__(self, config: ShippingConfig) -> None:
        base = self.TEST_URL if config.test_mode else self.BASE_URL
        self._client = httpx.AsyncClient(
            base_url=base,
            auth=httpx.BasicAuth(config.api_key, config.api_password),
            headers={
                "Account-Number": config.account_number,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )
        self._account_number = config.account_number

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None) -> dict:
        resp = await self._client.get(path, params=params)
        if resp.status_code not in {200, 201}:
            raise _scrub_error(resp)
        return resp.json()  # type: ignore[no-any-return]

    async def _post(self, path: str, json: dict) -> dict:
        resp = await self._client.post(path, json=json)
        if resp.status_code not in {200, 201}:
            raise _scrub_error(resp)
        return resp.json()  # type: ignore[no-any-return]

    async def _put(self, path: str, json: dict) -> dict:
        resp = await self._client.put(path, json=json)
        if resp.status_code not in {200, 201}:
            raise _scrub_error(resp)
        return resp.json()  # type: ignore[no-any-return]

    async def _delete(self, path: str) -> None:
        resp = await self._client.delete(path)
        if resp.status_code not in {200, 204}:
            raise _scrub_error(resp)

    # --- Account ---

    async def get_account(self) -> dict:
        return await self._get(f"/accounts/{self._account_number}")

    # --- Address validation ---

    async def validate_address(self, suburb: str, state: str, postcode: str) -> dict:
        params = {"suburb": suburb, "state": state.upper(), "postcode": postcode}
        return await self._get("/address", params)

    # --- Shipments ---

    async def create_shipment(self, shipments: list[dict]) -> dict:
        return await self._post("/shipments", {"shipments": shipments})

    async def get_shipments(
        self,
        shipment_ids: list[str] | None = None,
        status: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> dict:
        params: dict[str, str] = {}
        if shipment_ids:
            params["shipment_ids"] = ",".join(shipment_ids)
        if status:
            params["status"] = status
        if offset is not None:
            params["offset"] = str(offset)
        if limit is not None:
            params["number_of_shipments"] = str(limit)
        return await self._get("/shipments", params)

    async def update_items(self, shipment_id: str, items: list[dict]) -> dict:
        return await self._put(f"/shipments/{shipment_id}/items", {"items": items})

    async def delete_item(self, shipment_id: str, article_id: str) -> None:
        await self._delete(f"/shipments/{shipment_id}/articles/{article_id}")

    # --- Orders ---

    async def create_order(
        self,
        order_reference: str,
        shipment_ids: list[str],
    ) -> dict:
        shipments = [{"shipment_id": sid} for sid in shipment_ids]
        return await self._post(
            "/orders",
            {
                "order_reference": order_reference,
                "payment_method": "CHARGE_TO_ACCOUNT",
                "shipments": shipments,
            },
        )

    async def get_order(self, order_id: str) -> dict:
        return await self._get(f"/orders/{order_id}")

    # --- Labels ---

    async def create_labels(
        self,
        shipment_ids: list[str],
        layout: str = "A4-1pp",
        branded: bool = True,
    ) -> dict:
        # Determine group from layout
        shipments = [{"shipment_id": sid} for sid in shipment_ids]
        body: dict = {
            "preferences": [
                {
                    "type": "PRINT",
                    "groups": [
                        {
                            "group": "Parcel Post",
                            "layout": layout,
                            "branded": branded,
                        }
                    ],
                }
            ],
            "shipments": shipments,
            "wait_for_label_url": True,
        }
        return await self._post("/labels", body)

    async def get_labels(self, request_id: str) -> dict:
        return await self._get(f"/labels/{request_id}")

    # --- Pricing ---

    async def get_item_prices(
        self,
        from_postcode: str,
        to_postcode: str,
        items: list[dict],
    ) -> dict:
        body = {
            "from": {"postcode": from_postcode},
            "to": {"postcode": to_postcode},
            "items": items,
        }
        return await self._post("/prices/items", body)

    # --- Tracking ---

    async def track(self, tracking_ids: list[str]) -> dict:
        ids = ",".join(tracking_ids[:10])
        return await self._get("/track", {"tracking_ids": ids})
