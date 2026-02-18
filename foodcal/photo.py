import base64
import json
import os
import sys
from pathlib import Path

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def extract_recipe_from_photo(image_path):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    path = Path(image_path)
    if not path.exists():
        print(f"Error: File not found: {image_path}")
        return None

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        print(f"Error: Unsupported image format '{suffix}'. Use: {', '.join(SUPPORTED_FORMATS)}")
        return None

    image_data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    media_type = MEDIA_TYPES[suffix]

    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract the recipe from this cookbook photo. "
                            "Return ONLY valid JSON with this exact format:\n"
                            '{"title": "Recipe Name", "ingredients": ["1 cup flour", "2 eggs", ...]}\n'
                            "Each ingredient should include the quantity, unit, and ingredient name "
                            "as a single string. Do not include cooking instructions."
                        ),
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text.strip()
    # Handle markdown code blocks in response
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        print("Error: Could not parse recipe from photo. Raw response:")
        print(response_text)
        return None

    title = data.get("title", "Unknown Recipe")
    ingredients = data.get("ingredients", [])

    if not ingredients:
        print("No ingredients were extracted from the photo.")
        return None

    # Show extracted recipe for user confirmation
    print(f"\nExtracted recipe: {title}")
    print("Ingredients:")
    for i, ing in enumerate(ingredients, 1):
        print(f"  {i}. {ing}")

    confirm = input("\nLooks correct? (y/n): ").strip().lower()
    if confirm != "y":
        print("Discarded. You can try again or enter manually.")
        return None

    return {
        "title": title,
        "source": "photo",
        "url": None,
        "ingredients": ingredients,
    }
