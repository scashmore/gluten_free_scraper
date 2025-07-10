import json
import logging
from recipescraper.pipelines import RecipePipeline

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Load JSON recipes
with open("gluten_free_recipes.json") as f:
    recipes = json.load(f)

# Create pipeline in dry-run mode
pipeline = RecipePipeline(dry_run=True)
pipeline.open_spider(None)

# Process each recipe
for i, item in enumerate(recipes, 1):
    print(f"\n===== DRY RUN: Recipe {i} - {item.get('title')} =====")
    pipeline.process_item(item, None)

pipeline.close_spider(None)