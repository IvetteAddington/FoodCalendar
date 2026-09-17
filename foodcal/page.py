"""Build a phone-friendly HTML page for a week's meals.

Written for the place it gets used: a phone propped on a kitchen counter, read at
arm's length with your hands busy. Bigger type than a normal page, today's meal
picked out, and ingredients you can tick off while shopping or prepping.
"""

import html
from datetime import date, timedelta

from .storage import DAYS, load_plan
from .ingredients import parse_and_combine
from .style import CATEGORY_ICONS, sort_categories


def _esc(text):
    return html.escape(str(text or ""))


def _date_for(week_of, day_name):
    monday = date.fromisoformat(week_of)
    return monday + timedelta(days=DAYS.index(day_name))


def _range_label(week_of):
    monday = date.fromisoformat(week_of)
    sunday = monday + timedelta(days=6)
    if monday.month == sunday.month:
        return f"{monday.strftime('%B')} {monday.day}–{sunday.day}, {sunday.year}"
    return (
        f"{monday.strftime('%B')} {monday.day} – "
        f"{sunday.strftime('%B')} {sunday.day}, {sunday.year}"
    )


def _meta_bits(recipe):
    bits = []
    if recipe.get("total_time"):
        bits.append(f"{recipe['total_time']} min")
    if recipe.get("servings"):
        bits.append(_esc(recipe["servings"]))
    return bits


def _render_day(day, recipe, week_of):
    day_date = _date_for(week_of, day)
    iso = day_date.isoformat()
    date_label = day_date.strftime("%b %-d")

    if not recipe:
        return f"""
      <section class="day day--empty" data-date="{iso}">
        <header class="day__head">
          <h2 class="day__name">{day.capitalize()}</h2>
          <span class="day__date">{date_label}</span>
        </header>
        <p class="day__none">Nothing planned</p>
      </section>"""

    meta = _meta_bits(recipe)
    meta_html = ""
    if meta:
        spans = "".join(f"<span>{bit}</span>" for bit in meta)
        meta_html = f'<div class="meta">{spans}</div>'

    items = "".join(
        f"""
            <li>
              <label>
                <input type="checkbox" data-key="{_esc(f'{iso}|{i}')}">
                <span>{_esc(ing)}</span>
              </label>
            </li>"""
        for i, ing in enumerate(recipe.get("ingredients", []))
    )

    steps = recipe.get("steps") or []
    if steps:
        step_items = "".join(f"<li>{_esc(s)}</li>" for s in steps)
        method = f"""
        <div class="block">
          <h3 class="block__title">Method</h3>
          <ol class="steps">{step_items}</ol>
        </div>"""
    elif recipe.get("url"):
        method = f"""
        <div class="block">
          <h3 class="block__title">Method</h3>
          <p class="fallback">Steps aren't saved for this one.
            <a href="{_esc(recipe['url'])}" target="_blank" rel="noopener">Open the original recipe</a>.</p>
        </div>"""
    else:
        method = ""

    source = ""
    if recipe.get("url"):
        source = (
            f'<a class="source" href="{_esc(recipe["url"])}" '
            f'target="_blank" rel="noopener">View original</a>'
        )

    return f"""
      <section class="day" data-date="{iso}">
        <header class="day__head">
          <h2 class="day__name">{day.capitalize()}</h2>
          <span class="day__date">{date_label}</span>
        </header>
        <div class="day__body">
          <h3 class="recipe">{_esc(recipe['title'])}</h3>
          {meta_html}
          <div class="block">
            <h3 class="block__title">Ingredients</h3>
            <ul class="ings">{items}</ul>
          </div>
          {method}
          {source}
        </div>
      </section>"""


def _render_grocery(week_of):
    plan = load_plan(week_of)
    all_ings = []
    for day in DAYS:
        r = plan["recipes"][day]
        if r:
            all_ings.extend(r.get("ingredients", []))
    if not all_ings:
        return "", 0

    categorized, skipped = parse_and_combine(all_ings)
    if not categorized:
        return "", 0

    groups = []
    count = 0
    for cat in sort_categories(categorized.keys()):
        rows = ""
        for item in sorted(categorized[cat], key=lambda i: i["name"].lower()):
            rows += f"""
              <li>
                <label>
                  <input type="checkbox" data-key="{_esc(f'shop|{item["name"]}')}">
                  <span>{_esc(item['display'])}</span>
                </label>
              </li>"""
            count += 1
        groups.append(f"""
          <div class="aisle">
            <h3 class="aisle__name">{CATEGORY_ICONS.get(cat, '')} {_esc(cat)}</h3>
            <ul class="ings">{rows}</ul>
          </div>""")

    skipped_html = ""
    if skipped:
        lines = "".join(
            f"<li><b>{_esc(g)}</b> {_esc(', '.join(sorted(skipped[g])))}</li>"
            for g in sorted(skipped)
        )
        skipped_html = f"""
        <div class="pantry">
          <h3 class="block__title">Assumed in your pantry</h3>
          <ul>{lines}</ul>
        </div>"""

    return f"""
      <section class="shop" id="shop">
        <header class="shop__head">
          <h2>Grocery list</h2>
          <span class="count">{count} items</span>
        </header>
        <div class="aisles">{''.join(groups)}</div>
        {skipped_html}
      </section>""", count


def build_page(week_of):
    """Return the full HTML for one week."""
    plan = load_plan(week_of)
    days_html = "".join(
        _render_day(day, plan["recipes"][day], week_of) for day in DAYS
    )
    shop_html, _ = _render_grocery(week_of)
    planned = sum(1 for d in DAYS if plan["recipes"][d])

    return f"""<title>Dinners</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>
  :root {{
    --ground: #FBFBF9;
    --surface: #FFFFFF;
    --ink: #18211C;
    --muted: #6B766F;
    --rule: #E3E6E1;
    --accent: #1F6F4B;
    --accent-ink: #FFFFFF;
    --accent-soft: #EDF4F0;
    --shadow: 0 1px 2px rgba(24, 33, 28, .05), 0 6px 18px rgba(24, 33, 28, .05);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ground: #0F1411;
      --surface: #171D19;
      --ink: #E7EBE6;
      --muted: #94A09A;
      --rule: #273029;
      --accent: #6FC095;
      --accent-ink: #0F1411;
      --accent-soft: #1A241E;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 6px 18px rgba(0,0,0,.28);
    }}
  }}
  :root[data-theme="dark"] {{
    --ground: #0F1411;
    --surface: #171D19;
    --ink: #E7EBE6;
    --muted: #94A09A;
    --rule: #273029;
    --accent: #6FC095;
    --accent-ink: #0F1411;
    --accent-soft: #1A241E;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 6px 18px rgba(0,0,0,.28);
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    background: var(--ground);
    color: var(--ink);
    font-family: "Source Serif 4", Georgia, serif;
    font-size: 17px;
    line-height: 1.6;
    -webkit-text-size-adjust: 100%;
  }}

  .wrap {{
    max-width: 44rem;
    margin: 0 auto;
    padding: 2rem 1.125rem 5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }}

  /* ---- masthead ---- */
  .top {{ display: flex; flex-direction: column; gap: .35rem; margin-bottom: .5rem; }}
  .eyebrow {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .72rem; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; color: var(--accent);
  }}
  .top h1 {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: clamp(1.9rem, 7vw, 2.6rem);
    font-weight: 800; letter-spacing: -.02em; line-height: 1.05;
    margin: 0; text-wrap: balance;
  }}
  .top .sub {{ color: var(--muted); font-size: .95rem; }}
  .jump {{
    align-self: flex-start; margin-top: .4rem;
    font-family: Archivo, system-ui, sans-serif;
    font-size: .8rem; font-weight: 600; letter-spacing: .02em;
    color: var(--accent); background: var(--accent-soft);
    border: 1px solid var(--rule); border-radius: 999px;
    padding: .4rem .85rem; cursor: pointer;
  }}
  .jump:hover {{ border-color: var(--accent); }}
  .jump:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .jump[hidden] {{ display: none; }}

  /* ---- day cards ---- */
  .day {{
    background: var(--surface);
    border: 1px solid var(--rule);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow);
  }}
  .day__head {{
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 1rem; padding: .85rem 1.15rem;
    border-bottom: 1px solid var(--rule);
  }}
  .day__name {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .95rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; margin: 0;
  }}
  .day__date {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .78rem; font-weight: 500; color: var(--muted);
    font-variant-numeric: tabular-nums;
  }}
  .day__body {{ padding: 1.15rem; display: flex; flex-direction: column; gap: 1.35rem; }}

  .day--empty .day__head {{ border-bottom: none; }}
  .day__none {{
    margin: 0; padding: 0 1.15rem 1rem;
    color: var(--muted); font-style: italic; font-size: .95rem;
  }}

  /* today */
  .day--today {{ border-color: var(--accent); }}
  .day--today .day__head {{ background: var(--accent); border-bottom-color: var(--accent); }}
  .day--today .day__name,
  .day--today .day__date {{ color: var(--accent-ink); }}
  .day--today .day__date::after {{
    content: " · Today"; font-weight: 700;
  }}

  .recipe {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: 1.45rem; font-weight: 700; letter-spacing: -.015em;
    line-height: 1.2; margin: 0; text-wrap: balance;
  }}
  .meta {{
    display: flex; flex-wrap: wrap; gap: .5rem;
    margin-top: -.9rem;
  }}
  .meta span {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .72rem; font-weight: 600; letter-spacing: .06em;
    text-transform: uppercase; color: var(--muted);
    border: 1px solid var(--rule); border-radius: 999px;
    padding: .2rem .6rem;
  }}

  .block {{ display: flex; flex-direction: column; gap: .6rem; }}
  .block__title {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .72rem; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; color: var(--muted);
    margin: 0; padding-bottom: .4rem; border-bottom: 1px solid var(--rule);
  }}

  .ings {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }}
  .ings li + li {{ border-top: 1px solid var(--rule); }}
  .ings label {{
    display: flex; align-items: flex-start; gap: .7rem;
    padding: .55rem 0; cursor: pointer;
  }}
  .ings input {{
    appearance: none; flex: 0 0 auto;
    width: 1.15rem; height: 1.15rem; margin-top: .22rem;
    border: 1.5px solid var(--muted); border-radius: 5px;
    background: transparent; cursor: pointer;
    transition: background .12s ease, border-color .12s ease;
  }}
  .ings input:checked {{ background: var(--accent); border-color: var(--accent); }}
  .ings input:checked::after {{
    content: ""; display: block;
    width: .3rem; height: .58rem; margin: .06rem auto 0;
    border: solid var(--accent-ink);
    border-width: 0 2px 2px 0; transform: rotate(45deg);
  }}
  .ings input:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .ings input:checked + span {{ color: var(--muted); text-decoration: line-through; }}

  .steps {{
    margin: 0; padding-left: 1.3rem;
    display: flex; flex-direction: column; gap: .85rem;
  }}
  .steps li {{ padding-left: .3rem; }}
  .steps li::marker {{
    font-family: Archivo, system-ui, sans-serif;
    font-weight: 700; color: var(--accent); font-size: .95rem;
  }}

  .fallback {{ margin: 0; color: var(--muted); font-size: .95rem; }}
  a {{ color: var(--accent); }}
  .source {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .78rem; font-weight: 600; letter-spacing: .04em;
    text-transform: uppercase; text-decoration: none;
    align-self: flex-start;
  }}
  .source:hover {{ text-decoration: underline; }}

  /* ---- grocery ---- */
  .shop {{
    background: var(--surface); border: 1px solid var(--rule);
    border-radius: 14px; box-shadow: var(--shadow);
    margin-top: 1.25rem; overflow: hidden;
  }}
  .shop__head {{
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 1rem; padding: .95rem 1.15rem; border-bottom: 1px solid var(--rule);
  }}
  .shop__head h2 {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .95rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; margin: 0;
  }}
  .count {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .78rem; color: var(--muted); font-variant-numeric: tabular-nums;
  }}
  .aisles {{ padding: 1.15rem; display: flex; flex-direction: column; gap: 1.35rem; }}
  .aisle {{ display: flex; flex-direction: column; gap: .5rem; }}
  .aisle__name {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .72rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: var(--muted); margin: 0;
  }}
  .pantry {{
    padding: 1.15rem; border-top: 1px solid var(--rule);
    display: flex; flex-direction: column; gap: .5rem;
  }}
  .pantry ul {{ margin: 0; padding-left: 1.1rem; color: var(--muted); font-size: .92rem; }}
  .pantry b {{
    font-family: Archivo, system-ui, sans-serif;
    font-size: .72rem; letter-spacing: .08em; text-transform: uppercase;
    color: var(--ink); margin-right: .35rem;
  }}

  .foot {{
    text-align: center; color: var(--muted);
    font-family: Archivo, system-ui, sans-serif; font-size: .78rem;
    margin-top: 1rem;
  }}

  @media (prefers-reduced-motion: reduce) {{
    * {{ transition: none !important; animation: none !important; }}
  }}
</style>

<div class="wrap">
  <div class="top">
    <span class="eyebrow">Meal plan</span>
    <h1>Dinners</h1>
    <span class="sub">{_range_label(week_of)} · {planned} of 7 days planned</span>
    <button class="jump" id="jump" hidden>Jump to today</button>
  </div>
{days_html}
{shop_html}
  <p class="foot">Regenerate with <code>foodcal page</code></p>
</div>

<script>
  (function () {{
    // Mark today's card, so the page answers "what's for dinner" at a glance.
    var today = new Date();
    var iso = today.getFullYear() + "-" +
              String(today.getMonth() + 1).padStart(2, "0") + "-" +
              String(today.getDate()).padStart(2, "0");
    var card = document.querySelector('.day[data-date="' + iso + '"]');
    if (card) {{
      card.classList.add("day--today");
      var jump = document.getElementById("jump");
      jump.hidden = false;
      jump.addEventListener("click", function () {{
        card.scrollIntoView({{ behavior: "smooth", block: "start" }});
      }});
    }}

    // Remember ticked items, so a checked list survives closing the page
    // mid-shop or mid-cook.
    var KEY = "foodcal:{week_of}";
    var saved = {{}};
    try {{ saved = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{}}

    var boxes = document.querySelectorAll('input[type="checkbox"]');
    boxes.forEach(function (box) {{
      var k = box.dataset.key;
      if (saved[k]) box.checked = true;
      box.addEventListener("change", function () {{
        saved[k] = box.checked;
        try {{ localStorage.setItem(KEY, JSON.stringify(saved)); }} catch (e) {{}}
      }});
    }});
  }})();
</script>
"""
