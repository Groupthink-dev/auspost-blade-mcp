"""Bearer token authentication middleware for HTTP transport."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

if TYPE_CHECKING:
    from collections.abc import Callable

    from starlette.requests import Request


def get_bearer_token() -> str | None:
    """Read bearer token from environment. None means auth is disabled."""
    token = os.environ.get("AUSPOST_MCP_API_TOKEN", "").strip()
    return token if token else None


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Validates Authorization: Bearer <token> on HTTP transport requests."""

    async def dispatch(self, request: Request, call_next: Callable[..., Response]) -> Response:
        expected = get_bearer_token()
        if expected is None:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Missing or malformed Authorization header"}, status_code=401)

        token = auth_header[7:]
        if token != expected:
            return JSONResponse({"error": "Invalid bearer token"}, status_code=401)

        return await call_next(request)
