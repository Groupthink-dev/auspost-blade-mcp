"""Token-efficient output formatters for AusPost API responses."""

from __future__ import annotations


def format_postcodes(localities: list[dict]) -> str:
    """Compact postcode/suburb listing."""
    if not localities:
        return "No results found."
    lines = []
    for loc in localities:
        postcode = loc.get("postcode", "")
        name = loc.get("location", "")
        state = loc.get("state", "")
        category = loc.get("category", "")
        lat = loc.get("latitude")
        lng = loc.get("longitude")
        parts = [f"{postcode} {name}, {state}"]
        if category and category != "Delivery Area":
            parts.append(f"({category})")
        if lat and lng:
            parts.append(f"[{lat},{lng}]")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def format_countries(countries: list[dict]) -> str:
    """Compact country listing — code | name."""
    if not countries:
        return "No countries found."
    lines = [f"{c.get('code', '')} | {c.get('name', '')}" for c in countries]
    return f"{len(lines)} countries\n" + "\n".join(lines)


def format_parcel_sizes(sizes: list[dict]) -> str:
    """Standard box sizes reference."""
    if not sizes:
        return "No size data available."
    lines = []
    for s in sizes:
        name = s.get("name", "")
        length = s.get("length", "")
        width = s.get("width", "")
        height = s.get("height", "")
        lines.append(f"{name}: {length}x{width}x{height}cm")
    return "\n".join(lines)


def format_services(services: list[dict]) -> str:
    """Compact service listing with prices and options."""
    if not services:
        return "No services available for these parameters."
    lines = []
    for svc in services:
        code = svc.get("code", "")
        name = svc.get("name", "")
        price = svc.get("price", "")
        cover = svc.get("max_extra_cover", "")
        line = f"{code} | {name} | ${price}"
        if cover:
            line += f" | cover up to ${cover}"
        lines.append(line)
        # Show options compactly
        options = svc.get("options", {}).get("option", [])
        if isinstance(options, dict):
            options = [options]
        for opt in options:
            opt_code = opt.get("code", "")
            opt_name = opt.get("name", "")
            lines.append(f"  +{opt_code}: {opt_name}")
            suboptions = opt.get("suboptions", {}).get("option", [])
            if isinstance(suboptions, dict):
                suboptions = [suboptions]
            for sub in suboptions:
                lines.append(f"    +{sub.get('code', '')}: {sub.get('name', '')}")
    return "\n".join(lines)


def format_calculation(result: dict) -> str:
    """Formatted price calculation result."""
    service = result.get("service", "")
    delivery = result.get("delivery_time", "")
    total = result.get("total_cost", "")
    lines = [f"Service: {service}", f"Total: ${total}"]
    if delivery:
        lines.append(f"Delivery: {delivery}")
    costs = result.get("costs", {}).get("cost", [])
    if isinstance(costs, dict):
        costs = [costs]
    for c in costs:
        item = c.get("item", "")
        cost = c.get("cost", "")
        if cost and cost != "0.00":
            lines.append(f"  {item}: ${cost}")
    return "\n".join(lines)


def format_account(account: dict) -> str:
    """Account details summary."""
    lines = [
        f"Account: {account.get('account_number', '')}",
        f"Name: {account.get('name', '')}",
        f"Valid: {account.get('valid_from', '')} - {account.get('valid_to', '')}",
        f"Expired: {account.get('expired', '')}",
    ]
    details = account.get("details", {})
    if details.get("abn"):
        lines.append(f"ABN: {details['abn']}")
    if account.get("credit_blocked"):
        lines.append("** CREDIT BLOCKED **")
    products = account.get("postage_products", [])
    if products:
        prod_names = [p.get("type", p.get("product_id", "")) for p in products]
        lines.append(f"Products: {', '.join(prod_names)}")
    return "\n".join(lines)


def format_address_validation(result: dict) -> str:
    """Address validation result."""
    found = result.get("found", False)
    if found:
        return "Valid: address confirmed"
    results = result.get("results", [])
    if results:
        return f"Invalid. Suggestions: {', '.join(results)}"
    return "Invalid: no matching suburb/state/postcode combination"


def format_shipment(shipment: dict) -> str:
    """Compact shipment summary."""
    lines = [
        f"Shipment: {shipment.get('shipment_id', '')}",
        f"Ref: {shipment.get('shipment_reference', '')}",
    ]
    summary = shipment.get("shipment_summary", {})
    if summary:
        status = summary.get("status", "")
        cost = summary.get("total_cost", "")
        if status:
            lines.append(f"Status: {status}")
        if cost:
            lines.append(f"Cost: ${cost}")
    items = shipment.get("items", [])
    for item in items:
        item_id = item.get("item_id", "")
        tracking = item.get("tracking_details", {})
        article = tracking.get("article_id", "")
        weight = item.get("weight", "")
        product = item.get("product_id", "")
        lines.append(f"  Item {item_id}: {product} {weight}kg article={article}")
    return "\n".join(lines)


def format_shipments(data: dict) -> str:
    """Multiple shipments listing."""
    shipments = data.get("shipments", [])
    if not shipments:
        return "No shipments found."
    blocks = [format_shipment(s) for s in shipments]
    pagination = data.get("pagination", {})
    total = pagination.get("total_number_of_records")
    header = f"{len(shipments)} shipments"
    if total:
        header += f" (of {total} total)"
    return header + "\n\n" + "\n---\n".join(blocks)


def format_order(order: dict) -> str:
    """Order summary."""
    lines = [
        f"Order: {order.get('order_id', '')}",
        f"Ref: {order.get('order_reference', '')}",
        f"Created: {order.get('order_creation_date', '')}",
    ]
    summary = order.get("order_summary", {})
    if summary:
        lines.append(f"Cost: ${summary.get('total_cost', '')}")
        lines.append(f"Status: {summary.get('status', '')}")
        lines.append(f"Shipments: {summary.get('number_of_shipments', '')}")
        lines.append(f"Items: {summary.get('number_of_items', '')}")
    shipments = order.get("shipments", [])
    for s in shipments:
        lines.append(f"  Shipment {s.get('shipment_id', '')} — {s.get('shipment_summary', {}).get('status', '')}")
    return "\n".join(lines)


def format_labels(labels: dict) -> str:
    """Label generation result."""
    label_list = labels.get("labels", [])
    if not label_list:
        return "No labels generated."
    lines = []
    for label in label_list:
        req_id = label.get("request_id", "")
        status = label.get("status", "")
        url = label.get("url", "")
        line = f"Label {req_id}: {status}"
        if url:
            line += f"\n  URL: {url}"
        lines.append(line)
    return "\n".join(lines)


def format_prices(data: dict) -> str:
    """Item pricing result."""
    items = data.get("items", [])
    if not items:
        return "No pricing data returned."
    lines = []
    for item in items:
        product = item.get("product_id", "")
        product_type = item.get("product_type", "")
        price = item.get("calculated_price", "")
        gst = item.get("calculated_gst", "")
        ref = item.get("item_reference", "")
        line = f"{product} ({product_type}): ${price} (GST ${gst})"
        if ref:
            line = f"{ref} — {line}"
        lines.append(line)
        bundled = item.get("bundled_price")
        if bundled and bundled != price:
            lines.append(f"  Bundled: ${bundled}")
    return "\n".join(lines)


def format_tracking(data: dict) -> str:
    """Tracking results — compact event timeline."""
    results = data.get("tracking_results", [])
    if not results:
        return "No tracking data returned."
    blocks = []
    for result in results:
        tracking_id = result.get("tracking_id", "")
        status = result.get("status", "")
        lines = [f"Track: {tracking_id} — {status}"]
        errors = result.get("errors", [])
        if errors:
            for err in errors:
                lines.append(f"  Error: {err.get('message', err.get('code', ''))}")
            blocks.append("\n".join(lines))
            continue
        trackable = result.get("trackable_items", [])
        for item in trackable:
            article = item.get("article_id", "")
            item_status = item.get("status", "")
            product = item.get("product_type", "")
            lines.append(f"  {article} ({product}): {item_status}")
            events = item.get("events", [])
            for event in events[-5:]:  # Last 5 events for token efficiency
                date = event.get("date", "")
                location = event.get("location", "")
                desc = event.get("description", "")
                lines.append(f"    {date} | {location} | {desc}")
            if len(events) > 5:
                lines.append(f"    ... +{len(events) - 5} earlier events")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def format_locations(localities: list[dict]) -> str:
    """Location search results (post offices, parcel lockers)."""
    if not localities:
        return "No locations found."
    lines = []
    for loc in localities:
        postcode = loc.get("postcode", "")
        name = loc.get("location", "")
        state = loc.get("state", "")
        category = loc.get("category", "")
        lat = loc.get("latitude", "")
        lng = loc.get("longitude", "")
        line = f"{name}, {state} {postcode}"
        if category:
            line += f" ({category})"
        if lat and lng:
            line += f" [{lat},{lng}]"
        lines.append(line)
    return f"{len(lines)} locations\n" + "\n".join(lines)
