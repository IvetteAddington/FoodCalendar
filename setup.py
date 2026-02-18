from setuptools import setup, find_packages

setup(
    name="foodcal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "recipe-scrapers>=15.0.0",
        "ingredient-parser-nlp>=1.0.0",
        "anthropic>=0.40.0",
    ],
    entry_points={
        "console_scripts": [
            "foodcal=foodcal.cli:main",
        ],
    },
    python_requires=">=3.10",
)
