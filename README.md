# auspost-blade-mcp

Australia Post MCP server built against the **official AusPost APIs** — postage calculator, shipping, tracking, and locations in 21 tools.

## Why another AusPost MCP?

Every existing Australia Post MCP has the same problem: **none of them use the actual Australia Post API.**

| Existing MCP | What it actually does |
|---|---|
| australian-postcodes-mcp | Reads a community CSV file into SQLite. No API calls. |
| Ninja.ai "Australia Post" | No public source code. Unverifiable. |
| Shipi MCP | Commercial SaaS wrapper. AusPost is one of 15 carriers behind a proxy. |

**auspost-blade-mcp** calls AusPost's `digitalapi.auspost.com.au` endpoints directly. No intermediaries, no proxies, no CSV files. You bring your own API key and get the full API surface.

### What you get

- **Free tier (10 tools)** — postcode search, domestic/international parcel and letter pricing, service lookup, standard box sizes, country list, post office/parcel locker locations. Requires only a free API key.
- **eParcel tier (11 tools)** — create shipments, generate labels, track parcels, validate addresses, get contract pricing, manage orders. Requires an eParcel or StarTrack business contract.
- **Security by default** — write operations are gated behind `AUSPOST_WRITE_ENABLED=true`. Irreversible operations (order creation) require explicit `confirm=true`. Credentials are never logged or returned in error messages.

## Quick Start

### 1. Get an API key

Register free at [developers.auspost.com.au](https://developers.auspost.com.au) for a PAC API key.

### 2. Install

```bash
uv tool install auspost-blade-mcp
```

### 3. Configure

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "auspost": {
      "command": "auspost-blade-mcp",
      "env": {
        "AUSPOST_API_KEY": "your-pac-api-key"
      }
    }
  }
}
```

**Claude Code** (`~/.claude.json`):

```json
{
  "mcpServers": {
    "auspost": {
      "command": "auspost-blade-mcp",
      "env": {
        "AUSPOST_API_KEY": "your-pac-api-key"
      }
    }
  }
}
```

**With eParcel contract** (full shipping capabilities):

```json
{
  "mcpServers": {
    "auspost": {
      "command": "auspost-blade-mcp",
      "env": {
        "AUSPOST_API_KEY": "your-pac-api-key",
        "AUSPOST_SHIPPING_API_KEY": "your-shipping-uuid",
        "AUSPOST_SHIPPING_API_PASSWORD": "your-shipping-password",
        "AUSPOST_ACCOUNT_NUMBER": "1234567890",
        "AUSPOST_WRITE_ENABLED": "true"
      }
    }
  }
}
```

## Tool Catalog

### Free Tier (PAC + Locations) — `AUSPOST_API_KEY` only

| Tool | Purpose |
|------|---------|
| `auspost_postcode_search` | Search postcodes and suburbs with state filtering |
| `auspost_domestic_services` | List available domestic parcel services for a route and parcel size |
| `auspost_domestic_calculate` | Calculate domestic parcel postage for a specific service |
| `auspost_international_services` | List international parcel services for a country and weight |
| `auspost_international_calculate` | Calculate international parcel postage |
| `auspost_letter_services` | List domestic or international letter services |
| `auspost_letter_calculate` | Calculate letter postage (domestic or international) |
| `auspost_parcel_sizes` | Standard Australia Post box dimensions (reference data) |
| `auspost_country_list` | All countries with 2-letter ISO codes |
| `auspost_locations` | Find post offices, parcel lockers near a postcode |

### eParcel Tier (Shipping & Tracking) — requires contract

| Tool | Purpose | Gate |
|------|---------|------|
| `auspost_account` | Account details, products, and status | read |
| `auspost_validate_address` | Validate suburb/state/postcode combination | read |
| `auspost_get_shipments` | List or retrieve shipments | read |
| `auspost_get_order` | Get order details | read |
| `auspost_get_labels` | Check label status and get download URL | read |
| `auspost_get_prices` | Get contract-rate pricing for items | read |
| `auspost_track` | Track parcels by ID (max 10, rate limited 10/min) | read |
| `auspost_create_shipment` | Create a domestic shipment | **write** |
| `auspost_create_order` | Finalise shipments into an order (**irreversible**) | **write + confirm** |
| `auspost_create_labels` | Generate shipping labels (PDF) | **write** |

## Security Model

### Credential scrubbing

API keys and passwords are never included in tool output or error messages. Errors return AusPost error codes and human-readable messages only.

### Write gates

Shipping write operations (`create_shipment`, `create_order`, `create_labels`) require:
1. Shipping API credentials configured
2. `AUSPOST_WRITE_ENABLED=true` in environment

### Confirm gates

`auspost_create_order` requires `confirm=true` parameter. Orders cannot be cancelled, deleted, or voided after creation per AusPost API constraints.

### Bearer auth (HTTP transport)

When running in HTTP mode (`AUSPOST_MCP_TRANSPORT=http`), set `AUSPOST_MCP_API_TOKEN` to require `Authorization: Bearer <token>` on all requests.

### Test sandbox

Set `AUSPOST_SHIPPING_TEST_MODE=true` to use AusPost's test environment. Test requests return sample data and do not create real shipments.

## Configuration Reference

| Variable | Required | Secret | Default | Purpose |
|----------|----------|--------|---------|---------|
| `AUSPOST_API_KEY` | Yes | Yes | — | PAC + Locations API key (free) |
| `AUSPOST_SHIPPING_API_KEY` | No | Yes | — | Shipping API key (eParcel contract) |
| `AUSPOST_SHIPPING_API_PASSWORD` | No | Yes | — | Shipping API password |
| `AUSPOST_ACCOUNT_NUMBER` | No | No | — | 10-digit eParcel account number |
| `AUSPOST_WRITE_ENABLED` | No | No | `false` | Enable write operations |
| `AUSPOST_SHIPPING_TEST_MODE` | No | No | `false` | Use AusPost test sandbox |
| `AUSPOST_MCP_TRANSPORT` | No | No | `stdio` | Transport: `stdio` or `http` |
| `AUSPOST_MCP_API_TOKEN` | No | Yes | — | Bearer token for HTTP transport |

## Architecture

```
src/auspost_blade_mcp/
├── server.py       FastMCP instance, 21 @mcp.tool definitions
├── client.py       PACClient + ShippingClient (httpx async)
├── formatters.py   Token-efficient output (pipe-delimited, null-omitted)
├── models.py       Config parsing, security gates, constants
├── auth.py         Bearer token middleware for HTTP transport
└── __main__.py     python -m entry point
```

### API coverage

| AusPost API | Tier | Endpoints | Auth |
|-------------|------|-----------|------|
| PAC (Postage Assessment Calculator) | Free | 10 endpoints | `AUTH-KEY` header |
| Locations | Free | Postcode-based search | `AUTH-KEY` header |
| Shipping & Tracking | Contract | 12 endpoints | HTTP Basic + Account-Number |

### Token efficiency

Output is designed for LLM consumption, not human reading:
- Pipe-delimited compact format for lists
- Null fields omitted entirely
- Tracking events capped to last 5 per item
- No JSON wrapping — structured plaintext

## Development

```bash
git clone https://github.com/Groupthink-dev/auspost-blade-mcp.git
cd auspost-blade-mcp
make install-dev
make test        # unit tests (mocked, no API key needed)
make test-cov    # with coverage
make test-e2e    # live API tests (requires AUSPOST_API_KEY)
make check       # lint + type-check
make run         # start server (stdio)
```

## AusPost API Limitations

- **No webhooks** — tracking is polling-based. `auspost_track` is rate-limited to 10 requests/minute, max 10 IDs per call.
- **No mixed tracking** — cannot combine Australia Post and StarTrack tracking IDs in a single call.
- **Orders are final** — once created via `auspost_create_order`, orders cannot be cancelled, deleted, or voided.
- **Labels max 250** — synchronous label generation supports up to 250 parcels per request.
- **Locations API** — the new Locations API requires partner agreement for bulk export. This MCP uses the PAC postcode search for location data, which returns geocoded suburbs.

## Sidereal Marketplace

This MCP is published as a **certified** provider in the Sidereal Marketplace. See `sidereal-plugin.yaml` for the full manifest including credential configuration, test endpoints, and contract mappings.

Contract: `postal-v1`

## License

MIT
