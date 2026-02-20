from collections import defaultdict
from fractions import Fraction

from ingredient_parser import parse_ingredient

from .categories import categorize_ingredient


def parse_and_combine(all_ingredients):
    """Parse a flat list of ingredient strings, combine duplicates, and categorize."""
    parsed = []
    for raw in all_ingredients:
        try:
            result = parse_ingredient(raw)
            names = result.name if isinstance(result.name, list) else [result.name]
            qty, unit = _extract_amount(result)
            for name_obj in names:
                name = name_obj.text.strip() if hasattr(name_obj, "text") else ""
                if name:
                    parsed.append({"name": name, "qty": qty, "unit": unit, "raw": raw})
        except Exception:
            parsed.append({"name": raw, "qty": None, "unit": None, "raw": raw})

    combined = _combine_duplicates(parsed)
    categorized = _categorize(combined)
    return categorized


def _extract_name(result):
    if result.name:
        names = result.name if isinstance(result.name, list) else [result.name]
        if names and hasattr(names[0], "text"):
            return names[0].text.strip()
    return ""


def _extract_amount(result):
    if not result.amount:
        return None, None
    amounts = result.amount if isinstance(result.amount, list) else [result.amount]
    if not amounts:
        return None, None
    amt = amounts[0]

    # Extract quantity — may be a Fraction or string
    qty = None
    if amt.quantity is not None:
        if isinstance(amt.quantity, Fraction):
            qty = float(amt.quantity)
        else:
            qty = _parse_quantity(str(amt.quantity))

    # Extract unit — may be a Unit object or string
    unit = None
    if amt.unit is not None:
        unit = str(amt.unit)

    return qty, unit


def _parse_quantity(qty_str):
    """Convert quantity string to a float. Handles fractions like '1/2'."""
    if not qty_str:
        return None
    qty_str = qty_str.strip()
    # Handle unicode fractions
    fraction_map = {"\u00bd": 0.5, "\u2153": 1/3, "\u2154": 2/3, "\u00bc": 0.25, "\u00be": 0.75, "\u215b": 0.125}
    for char, val in fraction_map.items():
        if char in qty_str:
            parts = qty_str.replace(char, "").strip()
            return float(parts) + val if parts else val

    try:
        if "/" in qty_str:
            parts = qty_str.split()
            total = 0.0
            for part in parts:
                if "/" in part:
                    num, denom = part.split("/")
                    total += float(num) / float(denom)
                else:
                    total += float(part)
            return total
        return float(qty_str)
    except (ValueError, ZeroDivisionError):
        return None


def _normalize_unit(unit):
    """Normalize unit to singular lowercase form for matching."""
    u = unit.lower().strip()
    if u.endswith("s") and u not in ("glass",):
        u = u[:-1]
    return u


def _combine_duplicates(parsed_items):
    """Group by normalized ingredient name and combine quantities where possible."""
    groups = defaultdict(list)
    for item in parsed_items:
        key = item["name"].lower().strip().rstrip("s")
        groups[key].append(item)

    combined = []
    for key, items in groups.items():
        if len(items) == 1:
            combined.append(items[0])
            continue

        # Try to combine items with matching units
        unit_groups = defaultdict(list)
        no_unit = []
        for item in items:
            if item["unit"] is not None:
                unit_groups[_normalize_unit(item["unit"]) if item["unit"] else ""].append(item)
            else:
                no_unit.append(item)

        for unit, unit_items in unit_groups.items():
            total_qty = 0
            can_sum = True
            for ui in unit_items:
                if ui["qty"] is not None:
                    total_qty += ui["qty"]
                else:
                    can_sum = False
                    break

            if can_sum and total_qty > 0:
                unit_str = unit_items[0]["unit"]
                raw_parts = [_format_qty(total_qty)]
                if unit_str:
                    raw_parts.append(unit_str)
                raw_parts.append(unit_items[0]["name"])
                combined.append({
                    "name": unit_items[0]["name"],
                    "qty": total_qty,
                    "unit": unit_str,
                    "raw": " ".join(raw_parts),
                })
            else:
                combined.extend(unit_items)

        combined.extend(no_unit)

    return combined


def _format_qty(qty):
    """Format quantity nicely (remove trailing .0)."""
    if qty is None:
        return ""
    if qty == int(qty):
        return str(int(qty))
    return f"{qty:.2f}".rstrip("0").rstrip(".")


def _categorize(combined_items):
    """Group combined items by grocery category."""
    categorized = defaultdict(list)
    for item in combined_items:
        category = categorize_ingredient(item["name"])
        if category == "Skip":
            continue
        display = _format_item(item)
        categorized[category].append(display)
    return dict(categorized)


def _format_item(item):
    """Format a combined item for display."""
    parts = []
    qty = item["qty"]
    unit = item["unit"]
    if qty is not None:
        parts.append(_format_qty(qty))
    if unit:
        if qty is not None and qty > 1 and not unit.endswith("s"):
            unit = unit + "s"
        parts.append(unit)
    parts.append(item["name"])
    return " ".join(parts)
