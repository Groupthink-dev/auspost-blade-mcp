# AusPost Blade MCP — Tool Workflows

## Getting started

Start with `auspost_postcode_search` to validate postcodes, then use service lookup + calculate for pricing.

## Common workflows

### Price a domestic parcel

1. `auspost_domestic_services` — find available services for your route and parcel dimensions
2. `auspost_domestic_calculate` — get the exact price for a specific service code

### Price an international parcel

1. `auspost_country_list` — find the 2-letter ISO code (if needed)
2. `auspost_international_services` — available services for that country and weight
3. `auspost_international_calculate` — exact price with optional extras

### Ship a parcel (eParcel contract required)

1. `auspost_validate_address` — check the recipient address
2. `auspost_create_shipment` — create the shipment (requires `AUSPOST_WRITE_ENABLED=true`)
3. `auspost_create_labels` — generate a shipping label PDF
4. `auspost_get_labels` — retrieve the label URL once ready
5. `auspost_create_order` — finalise for despatch (irreversible, requires `confirm=true`)

### Track a parcel

1. `auspost_track` — pass up to 10 tracking IDs (comma-separated). Rate limited to 10 calls/minute.

## Token-saving tips

- Use `auspost_domestic_services` before `auspost_domestic_calculate` — the services call shows prices for all available services in one call.
- `auspost_parcel_sizes` returns compact reference data for standard box dimensions — useful context before pricing.
- Tracking output is automatically capped to the last 5 events per item.
- Combine multiple tracking IDs in a single `auspost_track` call (comma-separated, max 10).

## Service code reference

Common domestic service codes:
- `AUS_PARCEL_REGULAR` — Parcel Post (standard)
- `AUS_PARCEL_EXPRESS` — Express Post
- Satchel variants available via `auspost_domestic_services`

Use `auspost_domestic_services` or `auspost_international_services` to discover all available codes for a specific route.
