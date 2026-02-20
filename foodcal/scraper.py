import urllib.request

from recipe_scrapers import scrape_me, scrape_html
from recipe_scrapers._exceptions import WebsiteNotImplementedError


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
    return title, ingredients


def scrape_recipe(url):
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
        }
    except WebsiteNotImplementedError:
        pass
    except Exception as e:
        print(f"Could not auto-extract recipe: {e}")
        print("Falling back to manual entry.\n")
        return manual_entry(url)

    # 2. Fall back to wild-mode (JSON-LD schema) for unsupported sites
    try:
        title, ingredients = _scrape_wild(url)
        return {
            "title": title,
            "source": "url",
            "url": url,
            "ingredients": ingredients,
        }
    except Exception as e:
        print(f"Could not auto-extract recipe: {e}")
        print("Falling back to manual entry.\n")
        return manual_entry(url)


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
