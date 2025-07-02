# Gluten-Free Recipe Scraper

This is a web scraping project built with [Scrapy](https://scrapy.org/) that collects gluten-free recipes from [MyGluten-Free Kitchen](https://mygluten-freekitchen.com/recipes/). It extracts the recipe title, ingredients, instructions, and the URL from individual recipe pages and saves them to a structured JSON file.

## Features

- Crawls recipe links from the site's recipe listing page
- Extracts:
  - Recipe title
  - Ingredients (grouped by section)
  - Instructions (grouped by section)
  - Recipe URL
- Skips non-recipe pages like “Privacy Policy” and “About”
- Exports structured data to a JSON file

## Improvements
- Check against recipes previously scrapped and only add new/differing recipies

## Setup

1. **Create a virtual environment (optional but recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate

2. **Install Scrappy**
   ```bash
   pip install scrapy

3. **Navigate to the project folder and run the spider**
   ```bash
   cd gluten_free_scraper
   scrapy crawl mygf -o gluten_free_recipes.json

