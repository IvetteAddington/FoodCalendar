import argparse
import sys

from .storage import DAYS, load_plan, save_plan, clear_plan, week_start_for
from .scraper import scrape_recipe, manual_entry
from .photo import extract_recipe_from_photo
from .ingredients import parse_and_combine
from .reminders import send_to_reminders


def _resolve_week(args):
    """Get the week_of date string from the --week flag."""
    week_arg = getattr(args, "week", None)
    try:
        return week_start_for(week_arg)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _week_label(week_of):
    """Human-friendly label for a week."""
    current = week_start_for()
    if week_of == current:
        return f"this week ({week_of})"
    return f"week of {week_of}"


def cmd_add(args):
    """Add a recipe from a URL to a specific day."""
    day = args.day.lower()
    if day not in DAYS:
        print(f"Invalid day '{day}'. Choose from: {', '.join(DAYS)}")
        sys.exit(1)

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
    day = args.day.lower()
    if day not in DAYS:
        print(f"Invalid day '{day}'. Choose from: {', '.join(DAYS)}")
        sys.exit(1)

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
    day = args.day.lower()
    if day not in DAYS:
        print(f"Invalid day '{day}'. Choose from: {', '.join(DAYS)}")
        sys.exit(1)

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


def cmd_plan(args):
    """Display the current week's meal plan."""
    week_of = _resolve_week(args)
    plan = load_plan(week_of)
    print(f"\nMeal Plan ({_week_label(week_of)})")
    print("=" * 45)
    for day in DAYS:
        recipe = plan["recipes"][day]
        if recipe:
            source_tag = f" [{recipe['source']}]" if recipe.get("source") else ""
            print(f"  {day.capitalize():<12} {recipe['title']}{source_tag}")
        else:
            print(f"  {day.capitalize():<12} —")
    print()


def cmd_remove(args):
    """Remove a recipe from a specific day."""
    day = args.day.lower()
    if day not in DAYS:
        print(f"Invalid day '{day}'. Choose from: {', '.join(DAYS)}")
        sys.exit(1)

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
        print("No recipes in your plan yet. Add some with 'foodcal add' or 'foodcal add-photo'.")
        return

    print(f"\nGenerating shopping list from {recipe_count} recipe(s) ({_week_label(week_of)})...\n")
    categorized = parse_and_combine(all_ingredients)

    # Print the shopping list
    print("Shopping List")
    print("=" * 40)
    for category in sorted(categorized.keys()):
        items = categorized[category]
        print(f"\n  {category}:")
        for item in sorted(items):
            print(f"    - {item}")
    print()

    # Send to Reminders
    send_to_reminders(categorized)


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
    add_parser.add_argument("--day", required=True, help="Day of the week (e.g., monday)")
    _add_week_arg(add_parser)
    add_parser.set_defaults(func=cmd_add)

    # add-photo
    photo_parser = subparsers.add_parser("add-photo", help="Add a recipe from a cookbook photo")
    photo_parser.add_argument("image", help="Path to the cookbook photo")
    photo_parser.add_argument("--day", required=True, help="Day of the week (e.g., monday)")
    _add_week_arg(photo_parser)
    photo_parser.set_defaults(func=cmd_add_photo)

    # add-manual
    manual_parser = subparsers.add_parser("add-manual", help="Add a recipe by typing/pasting ingredients")
    manual_parser.add_argument("--day", required=True, help="Day of the week (e.g., monday)")
    _add_week_arg(manual_parser)
    manual_parser.set_defaults(func=cmd_add_manual)

    # plan
    plan_parser = subparsers.add_parser("plan", help="View the current week's meal plan")
    _add_week_arg(plan_parser)
    plan_parser.set_defaults(func=cmd_plan)

    # remove
    remove_parser = subparsers.add_parser("remove", help="Remove a recipe from a day")
    remove_parser.add_argument("--day", required=True, help="Day to remove the recipe from")
    _add_week_arg(remove_parser)
    remove_parser.set_defaults(func=cmd_remove)

    # list
    list_parser = subparsers.add_parser("list", help="Generate shopping list & send to Reminders")
    _add_week_arg(list_parser)
    list_parser.set_defaults(func=cmd_list)

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
