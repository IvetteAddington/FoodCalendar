from collections import defaultdict
from fractions import Fraction

from ingredient_parser import parse_ingredient

from .categories import categorize_ingredient
from .pantry import split_staples


def parse_and_combine(all_ingredients):
    """Parse ingredient strings, combine duplicates, drop pantry staples, categorize.

    Returns (categorized, skipped_staples) where `categorized` maps
    category -> list of {"display": "3/4 cup Parmesan cheese", "name": "Parmesan cheese"}.
    The "display" form is for the terminal; the bare "name" is what goes to Reminders.
    """
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

    to_buy, skipped = split_staples(parsed)
    combined = _combine_duplicates(to_buy)
    categorized = _categorize(combined)
    return categorized, skipped


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


# Decimal amounts that read better as fractions on a recipe.
_FRACTION_DISPLAY = {
    0.125: "1/8", 0.25: "1/4", 0.333: "1/3", 0.33: "1/3",
    0.375: "3/8", 0.5: "1/2", 0.625: "5/8", 0.666: "2/3",
    0.67: "2/3", 0.75: "3/4", 0.875: "7/8",
}


def _format_qty(qty):
    """Format quantity as a readable fraction where possible (0.75 -> 3/4)."""
    if qty is None:
        return ""
    if qty == int(qty):
        return str(int(qty))

    whole = int(qty)
    remainder = round(qty - whole, 3)

    for value, text in _FRACTION_DISPLAY.items():
        if abs(remainder - value) < 0.01:
            return f"{whole} {text}" if whole else text

    # Fall back to a tidy fraction, then to a decimal.
    frac = Fraction(qty).limit_denominator(8)
    if abs(float(frac) - qty) < 0.01:
        if frac.numerator > frac.denominator:
            whole, num = divmod(frac.numerator, frac.denominator)
            return f"{whole} {num}/{frac.denominator}" if num else str(whole)
        return f"{frac.numerator}/{frac.denominator}"

    return f"{qty:.2f}".rstrip("0").rstrip(".")


def _categorize(combined_items):
    """Group combined items by grocery category.

    Each entry carries both a detailed "display" string (for the terminal) and a
    bare "name" (for Apple Reminders, where quantities just add noise).
    """
    categorized = defaultdict(list)
    seen = defaultdict(set)
    for item in combined_items:
        category = categorize_ingredient(item["name"])
        if category == "Skip":
            continue
        name = item["name"].strip()
        # Don't list the same ingredient name twice in one category.
        if name.lower() in seen[category]:
            continue
        seen[category].add(name.lower())
        categorized[category].append({
            "display": _format_item(item),
            "name": name,
        })
    return dict(categorized)


def _format_item(item):
    """Format a combined item for terminal display, with quantity and unit."""
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
