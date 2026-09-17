import urllib.request

from recipe_scrapers import scrape_me, scrape_html
from recipe_scrapers._exceptions import WebsiteNotImplementedError


def _get_steps(scraper):
    """Pull cooking steps, if the site publishes them. Never fatal — a recipe
    without steps is still worth saving for its ingredients."""
    try:
        raw = scraper.instructions_list()
    except Exception:
        try:
            raw = (scraper.instructions() or "").split("\n")
        except Exception:
            return []
    return [step.strip() for step in (raw or []) if step and step.strip()]


def _get_meta(scraper):
    """Best-effort extras: servings, total time, image. All optional."""
    meta = {}
    for key, getter in (
        ("servings", lambda: scraper.yields()),
        ("total_time", lambda: scraper.total_time()),
        ("image", lambda: scraper.image()),
    ):
        try:
            value = getter()
            if value:
                meta[key] = value
        except Exception:
            pass
    return meta


def _scrape_wild(url):
    """Fetch raw HTML and parse using schema.org JSON-LD (works on most recipe blogs)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    scraper = scrape_html(html, org_url=url, supported_only=False)
    title = scraper.title()
    ingredients = scraper.ingredients()
    if not ingredients:
        raise ValueError("No ingredients found in page schema")
    return title, ingredients, _get_steps(scraper), _get_meta(scraper)


def scrape_recipe(url, interactive=True):
    """Scrape a recipe from a URL.

    With interactive=False, returns None instead of dropping into manual entry —
    so scripts and batch jobs can handle failures themselves rather than blocking
    on a prompt that has no terminal to read from.
    """
    def _give_up(message):
        print(f"Could not auto-extract recipe: {message}")
        if not interactive:
            return None
        print("Falling back to manual entry.\n")
        return manual_entry(url)

    # 1. Try the directly-supported scraper first
    try:
        scraper = scrape_me(url)
        title = scraper.title()
        ingredients = scraper.ingredients()
        if not ingredients:
            raise ValueError("No ingredients found")
        return {
            "title": title,
            "source": "url",
            "url": url,
            "ingredients": ingredients,
            "steps": _get_steps(scraper),
            **_get_meta(scraper),
        }
    except WebsiteNotImplementedError:
        pass
    except Exception as e:
        return _give_up(e)

    # 2. Fall back to wild-mode (JSON-LD schema) for unsupported sites
    try:
        title, ingredients, steps, meta = _scrape_wild(url)
        return {
            "title": title,
            "source": "url",
            "url": url,
            "ingredients": ingredients,
            "steps": steps,
            **meta,
        }
    except Exception as e:
        return _give_up(e)


def manual_entry(url=None):
    title = input("Recipe title: ").strip()
    if url is None:
        link = input("Link (optional, press Enter to skip): ").strip()
        if link:
            url = link
    print("Enter ingredients one per line (empty line to finish):")
    ingredients = []
    while True:
        line = input("  > ").strip()
        if not line:
            break
        ingredients.append(line)
    if not ingredients:
        print("No ingredients entered. Aborting.")
        return None
    return {
        "title": title,
        "source": "manual",
        "url": url,
        "ingredients": ingredients,
    }
