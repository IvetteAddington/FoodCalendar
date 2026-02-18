import json
from datetime import datetime, timedelta, date
from pathlib import Path

FOODCAL_DIR = Path.home() / ".foodcal"
PLANS_DIR = FOODCAL_DIR / "plans"

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def ensure_dir():
    FOODCAL_DIR.mkdir(exist_ok=True)
    PLANS_DIR.mkdir(exist_ok=True)


def week_start_for(week_arg=None):
    """Return the Monday date (as string) for the given week argument.

    Args:
        week_arg: None/"this" for current week, "next" for next week,
                  or a date string (YYYY-MM-DD) to target that week.
    """
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())

    if week_arg is None or week_arg == "this":
        return monday.isoformat()
    elif week_arg == "next":
        return (monday + timedelta(weeks=1)).isoformat()
    else:
        # Parse as a date and find its Monday
        try:
            target = date.fromisoformat(week_arg)
            target_monday = target - timedelta(days=target.weekday())
            return target_monday.isoformat()
        except ValueError:
            raise ValueError(
                f"Invalid week '{week_arg}'. Use 'this', 'next', or a date like 2026-02-23."
            )


def _plan_file(week_of):
    return PLANS_DIR / f"plan_{week_of}.json"


def _empty_plan(week_of):
    return {
        "week_of": week_of,
        "recipes": {day: None for day in DAYS},
    }


def load_plan(week_of=None):
    ensure_dir()
    if week_of is None:
        week_of = week_start_for()
    path = _plan_file(week_of)
    if not path.exists():
        # Migrate from old single-file format if it exists
        old_file = FOODCAL_DIR / "current_plan.json"
        if old_file.exists():
            with open(old_file, "r") as f:
                old_plan = json.load(f)
            if old_plan.get("week_of") == week_of:
                save_plan(old_plan)
                old_file.unlink()
                return old_plan
        return _empty_plan(week_of)
    with open(path, "r") as f:
        return json.load(f)


def save_plan(plan):
    ensure_dir()
    week_of = plan["week_of"]
    with open(_plan_file(week_of), "w") as f:
        json.dump(plan, f, indent=2)


def clear_plan(week_of=None):
    if week_of is None:
        week_of = week_start_for()
    save_plan(_empty_plan(week_of))
