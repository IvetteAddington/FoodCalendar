from recipe_scrapers import scrape_me


def scrape_recipe(url):
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
