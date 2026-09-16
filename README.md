# foodcal

A terminal meal planner that turns a week of recipes into a categorized grocery
list and pushes it straight to Apple Reminders.

Plan the week, run one command, and your phone has the shopping list — sorted in
roughly the order you walk the store, with pantry staples left off.

```
foodcal add https://www.allrecipes.com/recipe/223042/chicken-parmesan/ --day mon
foodcal list
```

---

## Everyday use

**Plan the whole week in one pass** (easiest way in):

```bash
foodcal quick
```

Walks you through Monday→Sunday. Paste a recipe URL for each day, press Enter to
skip a day, type `done` to stop early.

**Add recipes one at a time:**

```bash
foodcal add <url> --day mon              # scrape from a recipe site
foodcal add-photo cookbook.jpg --day tue # read a photo of a cookbook page
foodcal add-manual --day wed             # type or paste it yourself
```

**See what's planned:**

```bash
foodcal plan          # the week's meals
foodcal ingredients   # every ingredient, grouped by recipe
```

**Build the grocery list** (prints it, and sends it to Apple Reminders):

```bash
foodcal list
```

**Fix a recipe that scraped badly:**

```bash
foodcal edit --day mon
```

Opens that day's ingredients in your editor (`$EDITOR`, or nano). One per line —
correct them, save, close. Deleting a line drops that ingredient.

**Change your mind:**

```bash
foodcal remove --day wed   # clear one day
foodcal clear              # clear the whole week
```

---

## When a recipe doesn't parse cleanly

Recipe sites sometimes drop the actual food word. A real example:

```
1 small red, quartered (or ½ a large onion)
```

That means a red onion, but "onion" never appears in the line, so the parser
only sees "red". You'll get told right after adding the recipe:

```
! 1 ingredient(s) didn't parse cleanly:
      1 small red, quartered (or ½ a large onion)
        → read as 'red'
  Fix them with:  foodcal edit --day mon
```

Run that, change the line to `1 small red onion, quartered`, and it lands in
Produce where it belongs.

---

## Planning ahead

Every command takes `--week`:

```bash
foodcal add <url> --day mon --week next    # next week
foodcal plan --week next
foodcal list --week 2026-10-05             # any specific week
```

Weeks run Monday–Sunday. A date lands on whatever week contains it.

Days accept short forms — `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun` — or
full names.

---

## Pantry staples

Things you almost always have on hand never make the list: salt and pepper,
common dried spices, cooking oils and vinegars, and baking basics (flour, sugar,
baking soda, vanilla).

After each list, you'll see what was left off:

```
  Assumed already in your pantry (not added):
      Salt & pepper: salt, black pepper
      Oils & vinegars: olive oil
```

If you're actually low on something, add it to Reminders yourself.

**Fresh herbs are never skipped.** "Fresh basil" is produce you buy; plain or
dried basil is the jar in your cupboard. The same holds for ginger, garlic,
parsley, cilantro, and the rest — if the recipe says *fresh*, it goes on the list.

To change what counts as a staple, edit `PANTRY_STAPLES` in `foodcal/pantry.py`.

---

## What lands on your phone

The terminal shows quantities, because that's what you need while cooking:

```
  🧀 Dairy
      3/4 cup Parmesan cheese
      1/2 cup provolone cheese
```

Apple Reminders gets just the names, because that's what you need while shopping:

```
  [ ] Parmesan cheese
  [ ] provolone cheese
```

Items go into a list called **Grocery List** (created automatically if missing),
added in store-walking order: produce → meat → dairy → eggs → bakery → frozen →
pantry → condiments → spices → beverages.

---

## Setup

Requires Python 3.10+ and macOS (Apple Reminders integration uses AppleScript).

```bash
cd ~/Projects/2026Projects/FoodCalendar
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Run `foodcal` from anywhere** — symlink it onto your PATH:

```bash
ln -sf ~/Projects/2026Projects/FoodCalendar/venv/bin/foodcal /usr/local/bin/foodcal
```

Photo import (`add-photo`) uses Claude's vision API and needs a key:

```bash
export ANTHROPIC_API_KEY="your-key-here"   # add to ~/.zshrc to make it stick
```

### First run

macOS will ask for permission the first time something writes to Reminders. If
it's denied, grant it under **System Settings → Privacy & Security → Reminders**
for your terminal app.

---

## Where things live

| Path | What it is |
|---|---|
| `~/.foodcal/plans/plan_YYYY-MM-DD.json` | One file per week, named by that week's Monday |
| `foodcal/cli.py` | Commands and terminal output |
| `foodcal/scraper.py` | Recipe-site scraping |
| `foodcal/photo.py` | Cookbook-photo extraction (Claude vision) |
| `foodcal/ingredients.py` | Parsing, combining duplicates, fractions |
| `foodcal/categories.py` | Which grocery aisle an ingredient belongs to |
| `foodcal/pantry.py` | Staples that get skipped |
| `foodcal/reminders.py` | Sending to Apple Reminders |
| `foodcal/style.py` | Colors, icons, store ordering |

Plans are plain JSON — safe to open, edit, or back up.

---

## If something breaks

**A recipe URL won't scrape.** Not every site is supported. Fall back to
`foodcal add-manual --day mon` and paste the ingredients in.

**An ingredient landed in the wrong aisle.** Add the keyword to the right list in
`foodcal/categories.py`.

**Something you buy keeps getting skipped.** Remove it from `PANTRY_STAPLES` in
`foodcal/pantry.py`.

**Nothing reaches Reminders.** Check the Reminders permission above, and confirm
a list named "Grocery List" exists (or let the app create it).
