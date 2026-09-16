"""Pantry staples — things you almost always have, so they stay off the grocery list.

Skipped items are still reported back to the user as a note, so you can eyeball
whether you're actually running low on any of them.
"""

# Things assumed to already be in the pantry.
PANTRY_STAPLES = {
    "Salt & pepper": [
        "salt", "kosher salt", "sea salt", "table salt", "coarse salt",
        "pepper", "black pepper", "white pepper", "ground pepper",
        "ground black pepper", "freshly ground black pepper", "peppercorn",
    ],
    "Dried spices": [
        "garlic powder", "onion powder", "paprika", "smoked paprika",
        "oregano", "basil", "thyme", "rosemary", "sage", "marjoram",
        "tarragon", "dill weed", "bay leaf", "parsley flakes",
        "cumin", "coriander", "chili powder", "cayenne", "red pepper flake",
        "crushed red pepper", "chili flake", "chile flake", "pepper flake",
        "turmeric", "curry powder", "garam masala",
        "cinnamon", "nutmeg", "allspice", "clove", "cardamom", "ginger powder",
        "ground ginger", "italian seasoning", "herbs de provence", "old bay",
        "mustard powder", "dry mustard", "celery seed", "fennel seed",
        "caraway", "star anise", "five spice", "poultry seasoning",
    ],
    "Oils & vinegars": [
        "olive oil", "extra virgin olive oil", "vegetable oil", "canola oil",
        "cooking spray", "nonstick spray", "peanut oil", "corn oil",
        "vinegar", "white vinegar", "distilled vinegar", "apple cider vinegar",
        "balsamic vinegar", "red wine vinegar", "white wine vinegar",
        "rice vinegar", "cider vinegar",
    ],
    "Baking basics": [
        "flour", "all-purpose flour", "all purpose flour", "bread flour",
        "sugar", "granulated sugar", "white sugar", "brown sugar",
        "powdered sugar", "confectioners sugar",
        "baking soda", "baking powder", "cornstarch", "corn starch",
        "vanilla", "vanilla extract", "yeast", "active dry yeast",
    ],
}

# Descriptive words that don't change what the item is: "freshly ground black
# pepper" is still just black pepper. Stripped before matching so these variants
# are recognised, without the loose suffix matching that made "red bell pepper"
# look like "pepper".
_MODIFIERS = (
    "freshly ground", "fresh ground", "coarsely ground", "finely ground",
    "freshly cracked", "extra virgin", "extra-virgin", "all-purpose", "all purpose",
    "ground", "dried", "dry", "kosher", "sea", "coarse", "fine", "whole",
    "cracked", "granulated", "powdered", "toasted", "unbleached", "pure",
)

# Herbs and aromatics that are a pantry spice when dried, but produce when fresh.
# Only for these does the word "fresh" in the recipe mean "buy it".
_FRESH_AMBIGUOUS = {
    "basil", "oregano", "thyme", "rosemary", "sage", "parsley", "dill",
    "mint", "cilantro", "marjoram", "tarragon", "ginger", "chive", "bay leaf",
}


def _strip_modifiers(name):
    """Remove leading descriptors so variants match their base staple."""
    result = name.lower().strip()
    changed = True
    while changed:
        changed = False
        for modifier in sorted(_MODIFIERS, key=len, reverse=True):
            if result.startswith(modifier + " "):
                result = result[len(modifier) + 1:].strip()
                changed = True
    return result


# Flattened lookup: staple name -> which group it belongs to. Keys are normalized
# the same way incoming ingredients are, so "ground ginger" in the list above is
# stored as "ginger" and matches however the recipe happens to word it.
_STAPLE_LOOKUP = {}
for _group, _items in PANTRY_STAPLES.items():
    for _item in _items:
        _STAPLE_LOOKUP.setdefault(_strip_modifiers(_item), _group)
        _STAPLE_LOOKUP.setdefault(_item.lower(), _group)


def is_pantry_staple(name, raw_text=""):
    """Return the staple group name if this ingredient is a pantry staple, else None.

    Matching is exact against the staple list (after stripping descriptors like
    "ground" or "kosher"), so compound ingredients such as "red bell pepper" or
    "sesame oil blend" are never mistaken for the staple they merely contain.
    """
    base = _strip_modifiers(name)
    if not base:
        return None

    # Try as written, then singular ("chili flakes" -> "chili flake").
    group = _STAPLE_LOOKUP.get(base)
    if group is None and base.endswith("es"):
        group = _STAPLE_LOOKUP.get(base[:-2])
    if group is None and base.endswith("s"):
        group = _STAPLE_LOOKUP.get(base[:-1])
    if group is None:
        return None

    # "fresh basil" is produce to buy; "basil" or "dried basil" is the spice jar.
    # Checked only for herbs, so "freshly ground black pepper" stays a staple.
    if base in _FRESH_AMBIGUOUS and "fresh" in (raw_text or "").lower():
        return None

    return group


def split_staples(items):
    """Split parsed items into (to_buy, skipped_staples).

    `items` is a list of dicts with at least "name" and "raw" keys.
    Returns the items to keep, plus a dict of {group: [names]} that were skipped.
    """
    to_buy = []
    skipped = {}

    for item in items:
        group = is_pantry_staple(item.get("name", ""), item.get("raw", ""))
        if group:
            skipped.setdefault(group, [])
            display_name = item.get("name", "").strip()
            if display_name and display_name not in skipped[group]:
                skipped[group].append(display_name)
        else:
            to_buy.append(item)

    return to_buy, skipped
