# auspost-blade-mcp

Australia Post MCP server — Sidereal Blade MCP pattern.

## Build & Test

```bash
make install-dev   # install with dev + test deps
make test          # unit tests (mocked)
make test-e2e      # live API tests (requires AUSPOST_API_KEY)
make test-cov      # coverage report
make check         # ruff lint + mypy type-check
make run           # start server (stdio transport)
```

## Architecture

- `src/auspost_blade_mcp/server.py` — FastMCP tools (21 tools)
- `src/auspost_blade_mcp/client.py` — PACClient + ShippingClient (httpx async)
- `src/auspost_blade_mcp/formatters.py` — token-efficient output
- `src/auspost_blade_mcp/models.py` — config parsing, security gates
- `src/auspost_blade_mcp/auth.py` — HTTP bearer auth middleware
- `sidereal-plugin.yaml` — marketplace manifest

## Conventions

- Python 3.12+, async throughout
- FastMCP 2.0 with `@mcp.tool()` decorators
- Write operations gated behind `AUSPOST_WRITE_ENABLED=true`
- Irreversible operations require `confirm=true`
- Credentials never appear in tool output or error messages
- Tests use mocked clients (conftest.py fixtures); e2e tests hit live API
- Output: pipe-delimited, null fields omitted, no JSON wrapping
