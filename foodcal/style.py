"""Terminal styling helpers. Colors disable themselves when output isn't a TTY."""

import os
import sys

_ENABLED = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

_CODES = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "reset": "\033[0m",
}


def _wrap(text, *codes):
    if not _ENABLED:
        return text
    prefix = "".join(_CODES[c] for c in codes)
    return f"{prefix}{text}{_CODES['reset']}"


def bold(text):
    return _wrap(text, "bold")


def dim(text):
    return _wrap(text, "dim")


def green(text):
    return _wrap(text, "green")


def yellow(text):
    return _wrap(text, "yellow")


def cyan(text):
    return _wrap(text, "cyan")


def header(text):
    """A section header with an underline."""
    return f"\n{_wrap(text, 'bold', 'cyan')}\n{dim('─' * len(text))}"


def success(text):
    return f"{green('✓')} {text}"


def warn(text):
    return f"{yellow('!')} {text}"


# Emoji per grocery category, to make the list easier to scan while shopping.
CATEGORY_ICONS = {
    "Produce": "🥬",
    "Meat & Seafood": "🥩",
    "Dairy": "🧀",
    "Eggs": "🥚",
    "Bakery": "🍞",
    "Frozen": "🧊",
    "Pantry & Dry Goods": "🥫",
    "Spices & Seasonings": "🧂",
    "Condiments & Sauces": "🍯",
    "Beverages": "🧃",
    "Other": "🛒",
}

# Rough walk-through-the-store order, so the printed list matches the aisles.
CATEGORY_ORDER = [
    "Produce",
    "Meat & Seafood",
    "Dairy",
    "Eggs",
    "Bakery",
    "Frozen",
    "Pantry & Dry Goods",
    "Condiments & Sauces",
    "Spices & Seasonings",
    "Beverages",
    "Other",
]


def sort_categories(categories):
    """Order categories by store layout, with any unknown ones last."""
    known = [c for c in CATEGORY_ORDER if c in categories]
    unknown = sorted(c for c in categories if c not in CATEGORY_ORDER)
    return known + unknown


def icon(category):
    return CATEGORY_ICONS.get(category, "🛒")
