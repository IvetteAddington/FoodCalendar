import argparse
import sys

from .storage import DAYS, load_plan, save_plan, clear_plan, week_start_for
from .scraper import scrape_recipe, manual_entry
from .photo import extract_recipe_from_photo
from .ingredients import parse_and_combine
from .reminders import send_to_reminders
from . import style


def _resolve_week(args):
    """Get the week_of date string from the --week flag."""
    week_arg = getattr(args, "week", None)
    try:
        return week_start_for(week_arg)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _resolve_day(raw_day):
    """Accept full day names or short forms ('mon', 'tues', 'thu')."""
    day = raw_day.lower().strip()
    matches = [d for d in DAYS if d.startswith(day)]
    if len(matches) == 1:
        return matches[0]
    if day in DAYS:
        return day
    print(style.warn(f"Invalid day '{raw_day}'. Use: {', '.join(d[:3] for d in DAYS)}"))
    sys.exit(1)


def _week_label(week_of):
    """Human-friendly label for a week."""
    current = week_start_for()
    if week_of == current:
        return f"this week ({week_of})"
    return f"week of {week_of}"


def cmd_add(args):
    """Add a recipe from a URL to a specific day."""
    day = _resolve_day(args.day)

    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    if plan["recipes"][day] is not None:
        existing = plan["recipes"][day]["title"]
        overwrite = input(f"{day.capitalize()} already has '{existing}'. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Cancelled.")
            return

    print(f"Fetching recipe from: {args.url}")
    recipe = scrape_recipe(args.url)
    if recipe is None:
        return

    plan["recipes"][day] = recipe
    save_plan(plan)
    print(f"\nAdded '{recipe['title']}' to {day.capitalize()} ({_week_label(week_of)}).")


def cmd_add_photo(args):
    """Add a recipe from a cookbook photo to a specific day."""
    day = _resolve_day(args.day)

    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    if plan["recipes"][day] is not None:
        existing = plan["recipes"][day]["title"]
        overwrite = input(f"{day.capitalize()} already has '{existing}'. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Cancelled.")
            return

    print(f"Extracting recipe from photo: {args.image}")
    recipe = extract_recipe_from_photo(args.image)
    if recipe is None:
        return

    plan["recipes"][day] = recipe
    save_plan(plan)
    print(f"\nAdded '{recipe['title']}' to {day.capitalize()} ({_week_label(week_of)}).")


def cmd_add_manual(args):
    """Add a recipe by typing/pasting the title and ingredients."""
    day = _resolve_day(args.day)

    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    if plan["recipes"][day] is not None:
        existing = plan["recipes"][day]["title"]
        overwrite = input(f"{day.capitalize()} already has '{existing}'. Overwrite? (y/n): ").strip().lower()
        if overwrite != "y":
            print("Cancelled.")
            return

    recipe = manual_entry()
    if recipe is None:
        return

    plan["recipes"][day] = recipe
    save_plan(plan)
    print(f"\nAdded '{recipe['title']}' to {day.capitalize()} ({_week_label(week_of)}).")


def cmd_quick(args):
    """Walk through the week, pasting a recipe URL for each day."""
    week_of = _resolve_week(args)
    plan = load_plan(week_of)

    print(style.header(f"Quick plan — {_week_label(week_of)}"))
    print(style.dim("  Paste a recipe URL for each day."))
    print(style.dim("  Press Enter to skip a day, or type 'done' to stop.\n"))

    added = 0
    for day in DAYS:
        existing = plan["recipes"][day]
        label = style.bold(f"{day.capitalize():<10}")
        hint = style.dim(f"(now: {existing['title']})") if existing else ""

        try:
            url = input(f"  {label} {hint} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(style.dim("\n  Stopped."))
            break

        if url.lower() in ("done", "q", "quit"):
            break
        if not url:
            continue

        recipe = scrape_recipe(url)
        if recipe is None:
            print(style.warn(f"    Couldn't read that one — skipping {day.capitalize()}."))
            continue

        plan["recipes"][day] = recipe
        save_plan(plan)
        added += 1
        print(f"    {style.success(recipe['title'])}")

    if added:
        print(f"\n{style.success(f'Added {added} recipe(s).')}")
        print(style.dim("  Build the grocery list:  foodcal list"))
    else:
        print(style.dim("\n  Nothing added."))
    print()


def cmd_plan(args):
    """Display the current week's meal plan."""
    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    print(style.header(f"Meal Plan — {_week_label(week_of)}"))
    filled = 0
    for day in DAYS:
        recipe = plan["recipes"][day]
        if recipe:
            filled += 1
            source_tag = style.dim(f"  ({recipe['source']})") if recipe.get("source") else ""
            print(f"  {style.bold(day.capitalize()):<21} {recipe['title']}{source_tag}")
        else:
            print(f"  {day.capitalize():<12} {style.dim('—')}")

    print()
    if filled == 0:
        print(style.dim("  Nothing planned yet. Add a recipe:"))
        print(style.dim("    foodcal add <url> --day monday"))
    else:
        print(style.dim(f"  {filled} of 7 days planned.  Build the list:  foodcal list"))
    print()


def cmd_remove(args):
    """Remove a recipe from a specific day."""
    day = _resolve_day(args.day)

    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    if plan["recipes"][day] is None:
        print(f"No recipe set for {day.capitalize()}.")
        return

    removed = plan["recipes"][day]["title"]
    plan["recipes"][day] = None
    save_plan(plan)
    print(f"Removed '{removed}' from {day.capitalize()} ({_week_label(week_of)}).")


def cmd_list(args):
    """Generate the combined shopping list and send to Apple Reminders."""
    week_of = _resolve_week(args)
    plan = load_plan(week_of)

    all_ingredients = []
    recipe_count = 0
    for day in DAYS:
        recipe = plan["recipes"][day]
        if recipe:
            all_ingredients.extend(recipe["ingredients"])
            recipe_count += 1

    if not all_ingredients:
        print(style.warn("No recipes in your plan yet."))
        print(style.dim("  Add one:  foodcal add <url> --day monday"))
        return

    print(style.dim(f"\nBuilding list from {recipe_count} recipe(s) — {_week_label(week_of)}..."))
    categorized, skipped = parse_and_combine(all_ingredients)

    if not categorized:
        print(style.warn("Everything in this plan is already a pantry staple."))
        return

    print(style.header("Shopping List"))
    total = 0
    for category in style.sort_categories(categorized.keys()):
        items = categorized[category]
        print(f"\n  {style.icon(category)} {style.bold(category)}")
        for item in sorted(items, key=lambda i: i["name"].lower()):
            print(f"      {item['display']}")
            total += 1

    print(f"\n  {style.dim(f'{total} items')}")
    _print_skipped(skipped)

    print()
    send_to_reminders(categorized)


def _print_skipped(skipped):
    """Show which pantry staples were left off, in case any need restocking."""
    if not skipped:
        return
    print(style.dim("\n  Assumed already in your pantry (not added):"))
    for group in sorted(skipped.keys()):
        names = ", ".join(sorted(skipped[group]))
        print(style.dim(f"      {group}: {names}"))
    print(style.dim("  Low on any? Add them to Reminders by hand."))


def cmd_ingredients(args):
    """Display ingredients per recipe in the terminal."""
    week_of = _resolve_week(args)
    plan = load_plan(week_of)

    recipes_found = [(day, plan["recipes"][day]) for day in DAYS if plan["recipes"][day]]

    if not recipes_found:
        print("No recipes in your plan yet. Add some with 'foodcal add' or 'foodcal add-photo'.")
        return

    print(f"\nIngredients for {_week_label(week_of)}:\n")
    for day, recipe in recipes_found:
        print(f"  {recipe['title']}")
        for ingredient in recipe["ingredients"]:
            print(f"    - {ingredient}")
        print()


def cmd_clear(args):
    """Clear the current week's meal plan."""
    week_of = _resolve_week(args)
    confirm = input(f"Clear the meal plan for {_week_label(week_of)}? (y/n): ").strip().lower()
    if confirm == "y":
        clear_plan(week_of)
        print("Meal plan cleared.")
    else:
        print("Cancelled.")


def _add_week_arg(parser):
    """Add the --week argument to a subparser."""
    parser.add_argument(
        "--week",
        default=None,
        help="Which week: 'this' (default), 'next', or a date like 2026-02-23",
    )


def main():
    parser = argparse.ArgumentParser(
        prog="foodcal",
        description="Weekly meal planner & shopping list generator",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # add
    add_parser = subparsers.add_parser("add", help="Add a recipe from a URL")
    add_parser.add_argument("url", help="Recipe URL to scrape")
    add_parser.add_argument("--day", required=True, help="Day of the week — full or short (monday, mon, tue)")
    _add_week_arg(add_parser)
    add_parser.set_defaults(func=cmd_add)

    # add-photo
    photo_parser = subparsers.add_parser("add-photo", help="Add a recipe from a cookbook photo")
    photo_parser.add_argument("image", help="Path to the cookbook photo")
    photo_parser.add_argument("--day", required=True, help="Day of the week — full or short (monday, mon, tue)")
    _add_week_arg(photo_parser)
    photo_parser.set_defaults(func=cmd_add_photo)

    # add-manual
    manual_parser = subparsers.add_parser("add-manual", help="Add a recipe by typing/pasting ingredients")
    manual_parser.add_argument("--day", required=True, help="Day of the week — full or short (monday, mon, tue)")
    _add_week_arg(manual_parser)
    manual_parser.set_defaults(func=cmd_add_manual)

    # quick
    quick_parser = subparsers.add_parser("quick", help="Plan the whole week in one pass")
    _add_week_arg(quick_parser)
    quick_parser.set_defaults(func=cmd_quick)

    # plan
    plan_parser = subparsers.add_parser("plan", help="View the current week's meal plan")
    _add_week_arg(plan_parser)
    plan_parser.set_defaults(func=cmd_plan)

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove a recipe from a day")
    remove_parser.add_argument("--day", required=True, help="Day to remove the recipe from (monday, mon, tue)")
    _add_week_arg(remove_parser)
    remove_parser.set_defaults(func=cmd_remove)

    # list
    list_parser = subparsers.add_parser("list", help="Generate shopping list & send to Reminders")
    _add_week_arg(list_parser)
    list_parser.set_defaults(func=cmd_list)

    # ingredients
    ingredients_parser = subparsers.add_parser("ingredients", help="Show ingredient list in terminal only")
    _add_week_arg(ingredients_parser)
    ingredients_parser.set_defaults(func=cmd_ingredients)

    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear the entire meal plan")
    _add_week_arg(clear_parser)
    clear_parser.set_defaults(func=cmd_clear)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
