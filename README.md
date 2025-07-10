# Gluten-Free Recipe Scraper

This is a web scraping project built with [Scrapy](https://scrapy.org/) that collects gluten-free recipes from [MyGluten-Free Kitchen](https://mygluten-freekitchen.com/recipes/). It extracts the recipe title, ingredients, instructions, and the URL from individual recipe pages and saves them to a MySQL database.

## Features

- Crawls recipe links from the site's recipe listing page
- Skips non-recipe pages like “Privacy Policy” and “About”
- Scrapes recipe title, ingredients (with sections), instructions, and URL
- Parses ingredient lines to extract quantity, unit, and ingredient name
- Stores recipes, ingredients, and their relationships in MySQL tables
- Supports dry-run mode to print or log SQL queries without inserting into the database
- Logs queries and supports debugging for troubleshooting parsing issues


## Improvements

- Check against recipes previously scraped and only add new/differing recipes
- Ingredient parsing currently imperfect — sometimes includes extra descriptive text or inconsistent units, e.g. “peanut butter at room temp (smooth or chunky)”
- Improve ingredient parsing with NLP or heuristic rules to better separate quantity, unit, and ingredient name
- Handle edge cases like ranges, optional ingredients, and multi-part descriptions

## Setup

1. **Create a virtual environment (optional but recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
    ```bash
    pip install scrapy mysql-connector-python
    ```

3. **Configure Database Connection**

    Update your recipescraper/db.py with your MySQL credentials and database info.

4. **Navigate to the project folder and run the spider**
    ```bash
    cd gluten_free_scraper
    scrapy crawl mygf
    ```

## Dry Run

You can run the scraper pipeline in **dry run** mode to see the SQL queries that *would* be executed without actually writing to the database.

**Use this command to run the spider with dry run enabled**

    ```bash
    scrapy crawl mygf -s DRY_RUN=True
    ```


## Database Structure & Logic

    ```plaintext
    +---------------------+  +---------------------+  +------------------------------+
    |      recipes        |  |     ingredients     |  |     recipe_ingredients       |
    |---------------------|  |---------------------|  |------------------------------|
    | id (PK)             |  | id (PK)             |  | recipe_id                    |(FK to recipes.id)
    | title               |  | name                |  | ingredient_id                |(FK to ingredients.id)
    | url                 |  +---------------------+  | quantity                     |
    | instructions        |                           | unit                         |
    +---------------------+                           | section_name                 |
                                                      +------------------------------+
   ```


The database is designed to normalize recipe and ingredient data for flexible querying and reuse of shared ingredients across multiple recipes.

- **`recipes`** stores core recipe metadata like the title and URL. The full instructions are also stored here, since it’s unlikely multiple recipes will have the exact same steps.

- **`ingredients`** is a lookup table containing unique ingredient names. Each ingredient is inserted only once to avoid duplicates.

- **`recipe_ingredients`** is a join table that maps which ingredients are used in which recipes, including additional context like:
  - **`quantity`** (e.g., `1.5`)
  - **`unit`** (e.g., `tsp`, `cup`)
  - **`section_name`** (e.g., `"Sauce"` or `"General"`) for grouping ingredients by logical recipe sections

### Insertion Logic

1. A recipe is inserted into `recipes`, and the new `recipe_id` is retrieved.
2. Each ingredient line is parsed into `quantity`, `unit`, and `ingredient_name`.
3. The ingredient is looked up in `ingredients`. If it doesn't exist, it’s inserted.
4. A row is added to `recipe_ingredients` with the `recipe_id`, `ingredient_id`, and parsed data.

### Example Queries You Can Run

- _“Show all recipes using peanut butter”_
    ```mysql
    SELECT r.id, r.title, r.url
    FROM recipes r
    JOIN recipe_ingredients ri ON r.id = ri.recipe_id
    JOIN ingredients i ON ri.ingredient_id = i.id
    WHERE i.name LIKE '%peanut butter%';
    ```

- _“Find quantities of chocolate chips used across recipes”_
    ```mysql
    SELECT r.title, ri.quantity, ri.unit
    FROM recipes r
    JOIN recipe_ingredients ri ON r.id = ri.recipe_id
    JOIN ingredients i ON ri.ingredient_id = i.id
    WHERE i.name LIKE '%chocolate chip%';
    ```


## How to Improve
**Ingredient Parsing** 

- Current parsing uses regex and sometimes captures extra descriptive text (e.g., “peanut butter at room temp (smooth or chunky)”) as part of the ingredient name or unit. This can cause inaccurate ingredient records.

**Advanced NLP** 

- Using natural language processing or heuristic rules can better separate quantities, units, and ingredient names.

**Unit Normalization** 

- Standardize unit names (e.g., “tsp.”, “teaspoon”, “tsp”) for consistency in the database.

**Handle Complex Ingredients**

- Support ingredient ranges, optional parts, and parenthetical notes more gracefully.

**Duplicate Checks**

- Before inserting ingredients or recipes, check for existing records to avoid duplicates.

**Logging and Debugging**

- Continue improving logging to track parsing issues and database operations.





