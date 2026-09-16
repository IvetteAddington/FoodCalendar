import subprocess
import sys


REMINDERS_LIST = "Grocery List"


def send_to_reminders(categorized_items):
    """Send shopping list items to Apple Reminders.

    Items are sent as plain ingredient names (no quantities, no category tags) —
    easiest to scan while pushing a cart. Category order still controls the
    sequence, so the list roughly follows the layout of the store.
    """
    all_items = []
    seen = set()
    for category, items in sorted(categorized_items.items()):
        for item in items:
            name = item["name"] if isinstance(item, dict) else str(item)
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            all_items.append(name)

    if not all_items:
        print("No items to send to Reminders.")
        return

    # Build a single AppleScript that creates the list (if needed) and adds all items
    item_lines = []
    for item in all_items:
        # Escape quotes for AppleScript
        escaped = item.replace("\\", "\\\\").replace('"', '\\"')
        item_lines.append(
            f'    make new reminder at end with properties {{name:"{escaped}"}}'
        )

    script = f"""
tell application "Reminders"
  if not (exists list "{REMINDERS_LIST}") then
    make new list with properties {{name:"{REMINDERS_LIST}"}}
  end if
  tell list "{REMINDERS_LIST}"
{chr(10).join(item_lines)}
  end tell
end tell
"""

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"Error adding to Reminders: {result.stderr.strip()}")
            if "not authorized" in result.stderr.lower() or "access" in result.stderr.lower():
                print(
                    "Tip: Go to System Settings > Privacy & Security > Reminders "
                    "and grant access to your terminal app."
                )
            return False
        print(f"Added {len(all_items)} items to '{REMINDERS_LIST}' in Apple Reminders.")
        return True
    except subprocess.TimeoutExpired:
        print("Timed out connecting to Reminders.")
        return False
    except FileNotFoundError:
        print("osascript not found. This feature requires macOS.")
        return False
