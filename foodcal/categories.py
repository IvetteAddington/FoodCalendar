CATEGORY_KEYWORDS = {
    "Produce": [
        "onion", "garlic", "tomato", "potato", "carrot", "celery", "pepper",
        "lettuce", "spinach", "kale", "broccoli", "cauliflower", "zucchini",
        "squash", "mushroom", "corn", "pea", "bean sprout", "cabbage",
        "cucumber", "avocado", "lemon", "lime", "orange", "apple", "banana",
        "berry", "blueberry", "strawberry", "raspberry", "ginger", "jalapeño",
        "jalapeno", "cilantro", "parsley", "basil", "mint", "dill", "chive",
        "scallion", "green onion", "shallot", "leek", "asparagus", "artichoke",
        "eggplant", "beet", "radish", "turnip", "sweet potato", "yam",
        "mango", "pineapple", "peach", "pear", "plum", "grape", "melon",
        "watermelon", "cantaloupe", "coconut", "fig", "date", "pomegranate",
        "arugula", "romaine", "chard", "bok choy", "fennel", "okra",
        "snap pea", "snow pea", "green bean", "bell pepper", "serrano",
        "habanero", "poblano", "thai chili", "lemongrass", "thai basil",
    ],
    "Meat & Seafood": [
        "chicken", "beef", "pork", "lamb", "turkey", "duck", "veal",
        "bacon", "sausage", "ham", "prosciutto", "pancetta", "salami",
        "ground beef", "ground turkey", "ground pork", "steak", "roast",
        "rib", "thigh", "breast", "wing", "drumstick", "tenderloin",
        "salmon", "tuna", "shrimp", "prawn", "crab", "lobster", "scallop",
        "clam", "mussel", "oyster", "cod", "tilapia", "halibut", "trout",
        "sardine", "anchovy", "squid", "calamari", "octopus", "mahi",
        "swordfish", "sea bass", "snapper", "catfish",
    ],
    "Dairy": [
        "milk", "cream", "butter", "cheese", "yogurt", "sour cream",
        "cream cheese", "mozzarella", "cheddar", "parmesan", "ricotta",
        "feta", "gouda", "brie", "gruyere", "goat cheese", "cottage cheese",
        "half and half", "half-and-half", "whipping cream", "heavy cream",
        "buttermilk", "ghee", "mascarpone", "provolone", "swiss cheese",
    ],
    "Pantry & Dry Goods": [
        "flour", "sugar", "rice", "pasta", "noodle", "noodles", "bread", "tortilla",
        "oat", "cereal", "granola", "quinoa", "couscous", "lentil",
        "chickpea", "black bean", "kidney bean", "pinto bean", "navy bean",
        "cannellini", "white bean", "split pea", "barley", "farro",
        "bulgur", "polenta", "cornmeal", "breadcrumb", "panko",
        "baking powder", "baking soda", "yeast", "cornstarch",
        "cocoa", "chocolate", "vanilla", "brown sugar", "powdered sugar",
        "honey", "maple syrup", "molasses", "agave",
        "olive oil", "vegetable oil", "canola oil", "sesame oil",
        "coconut oil", "cooking spray", "peanut oil",
        "vinegar", "apple cider vinegar", "balsamic vinegar", "rice vinegar",
        "wine vinegar", "red wine vinegar", "white wine vinegar",
        "broth", "stock", "bouillon", "tomato paste", "tomato sauce",
        "crushed tomato", "diced tomato", "canned tomato", "tomato puree",
        "coconut milk", "almond milk", "oat milk",
        "peanut butter", "almond butter", "tahini",
        "jam", "jelly", "preserve",
        "nut", "almond", "walnut", "pecan", "cashew", "pistachio",
        "pine nut", "peanut", "sunflower seed", "pumpkin seed",
        "raisin", "dried cranberry", "dried fruit",
    ],
    "Spices & Seasonings": [
        "salt", "pepper", "black pepper", "white pepper", "ground pepper",
        "cumin", "paprika", "chili powder", "cayenne", "turmeric",
        "cinnamon", "nutmeg", "clove", "allspice", "cardamom",
        "coriander", "oregano", "thyme", "rosemary", "sage",
        "bay leaf", "marjoram", "tarragon", "lavender",
        "curry powder", "curry paste", "garam masala", "five spice",
        "smoked paprika", "chipotle", "ancho", "red pepper flake",
        "crushed red pepper", "italian seasoning", "herbs de provence",
        "old bay", "taco seasoning", "ranch seasoning",
        "garlic powder", "onion powder", "mustard powder",
        "saffron", "sumac", "za'atar", "star anise", "fennel seed", "fennel seeds",
        "celery seed", "poppy seed", "sesame seed", "caraway",
        "dried basil", "dried oregano", "dried thyme", "dried parsley",
        "msg", "bouillon cube",
    ],
    "Condiments & Sauces": [
        "soy sauce", "fish sauce", "oyster sauce", "hoisin",
        "worcestershire", "hot sauce", "sriracha", "tabasco",
        "ketchup", "mustard", "dijon", "mayonnaise", "mayo",
        "salsa", "pesto", "marinara", "bbq sauce", "teriyaki",
        "miso", "sambal", "gochujang", "harissa",
        "relish", "chutney", "capers", "olive",
        "ranch dressing", "italian dressing", "vinaigrette",
    ],
    "Bakery": [
        "bread loaf", "baguette", "ciabatta", "sourdough",
        "pita", "naan", "flatbread", "english muffin",
        "hamburger bun", "hot dog bun", "dinner roll",
        "croissant", "bagel", "crouton",
    ],
    "Frozen": [
        "frozen", "ice cream", "frozen pizza", "frozen vegetable",
        "frozen fruit", "frozen dinner", "puff pastry", "pie crust",
        "phyllo", "frozen corn", "frozen pea", "frozen spinach",
    ],
    "Beverages": [
        "wine", "beer", "juice", "coffee", "tea",
        "soda", "sparkling water", "tonic",
        "rum", "vodka", "whiskey", "bourbon", "tequila",
        "brandy", "sake", "mirin", "sherry", "marsala",
    ],
    "Eggs": [
        "egg", "eggs",
    ],
}


# Categories to check first (more specific matches before broad ones)
_PRIORITY_ORDER = [
    "Spices & Seasonings", "Condiments & Sauces", "Eggs", "Frozen",
    "Dairy", "Meat & Seafood", "Bakery", "Beverages",
    "Pantry & Dry Goods", "Produce",
]


import re

def _word_match(keyword, text):
    """Check if keyword appears as a whole word (not as part of another word)."""
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return re.search(pattern, text) is not None


def categorize_ingredient(ingredient_name):
    name_lower = ingredient_name.lower().strip()
    # Skip plain water — you don't need to buy it
    if name_lower == "water":
        return "Skip"
    for category in _PRIORITY_ORDER:
        keywords = CATEGORY_KEYWORDS.get(category, [])
        for keyword in keywords:
            if _word_match(keyword, name_lower):
                return category
    return "Other"
