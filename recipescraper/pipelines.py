import re
import logging
from recipescraper.db import get_connection

logger = logging.getLogger(__name__)

class RecipePipeline:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None

    def open_spider(self, spider):
        if not self.dry_run:
            self.conn = get_connection()
            self.cursor = self.conn.cursor()
            logger.info("Opened database connection.")
        else:
            logger.info("Dry run mode enabled: No database connection.")

    def close_spider(self, spider):
        if not self.dry_run and self.conn:
            self.cursor.close()
            self.conn.close()
            logger.info("Closed database connection.")

    def process_item(self, item, spider):
        recipe_id = self.insert_recipe(item)

        for section in item.get('ingredients', []):
            section_name = section.get('section')
            for ingredient_line in section.get('items', []):
                quantity, unit, ingredient_name = self.parse_ingredient_line(ingredient_line)
                ingredient_id = self.get_or_create_ingredient(ingredient_name)
                self.insert_recipe_ingredient(recipe_id, ingredient_id, quantity, unit, section_name)

        instructions_text = self.flatten_instructions(item.get('instructions', []))
        self.update_recipe_instructions(recipe_id, instructions_text)

        if not self.dry_run:
            self.conn.commit()
            logger.info("Committed recipe to database.")
        else:
            logger.info("Dry run: skipped commit.")

        return item

    def insert_recipe(self, item):
        sql = "INSERT INTO recipes (title, url) VALUES (%s, %s)"
        params = (item['title'], item['url'])
        if self.dry_run:
            logger.debug(f"[DRY RUN] SQL: {sql} | Params: {params}")
            return 0  # Dummy ID
        self.cursor.execute(sql, params)
        return self.cursor.lastrowid

    def get_or_create_ingredient(self, name):
        sql_select = "SELECT id FROM ingredients WHERE name=%s"
        sql_insert = "INSERT INTO ingredients (name) VALUES (%s)"
        if self.dry_run:
            logger.debug(f"[DRY RUN] SELECT id FROM ingredients WHERE name={name}")
            logger.debug(f"[DRY RUN] If not found, INSERT INTO ingredients (name) VALUES ({name})")
            return 0  # Dummy ID
        self.cursor.execute(sql_select, (name,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        self.cursor.execute(sql_insert, (name,))
        return self.cursor.lastrowid

    def insert_recipe_ingredient(self, recipe_id, ingredient_id, quantity, unit, section_name):
        sql = """
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, section_name)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (recipe_id, ingredient_id, quantity, unit, section_name)
        if self.dry_run:
            logger.debug(f"[DRY RUN] SQL: {sql.strip()} | Params: {params}")
        else:
            self.cursor.execute(sql, params)

    def flatten_instructions(self, instructions):
        parts = []
        for section in instructions:
            steps = section.get('steps', [])
            parts.append(f"{section.get('section', '')}:\n" + "\n".join(steps))
        return "\n\n".join(parts)

    def update_recipe_instructions(self, recipe_id, instructions_text):
        sql = "UPDATE recipes SET instructions=%s WHERE id=%s"
        params = (instructions_text, recipe_id)
        if self.dry_run:
            logger.debug(f"[DRY RUN] SQL: {sql} | Params: {params}")
        else:
            self.cursor.execute(sql, params)

    def parse_ingredient_line(self, line):
        quantity = None
        unit = None
        ingredient_name = line

        pattern = r"^\s*(\d+\/\d+|\d+\.\d+|\d+)?(?:\s+([^\s]+))?\s+(.*)$"
        m = re.match(pattern, line)
        if m:
            qty_str = m.group(1)
            unit_candidate = m.group(2)
            rest = m.group(3).strip()

            if qty_str:
                try:
                    if '/' in qty_str:
                        num, denom = qty_str.split('/')
                        quantity = float(num) / float(denom)
                    else:
                        quantity = float(qty_str)
                except Exception:
                    quantity = None

                if unit_candidate:
                    unit = unit_candidate

                ingredient_name = rest
            else:
                ingredient_name = line.strip()

        return quantity, unit, ingredient_name.lower()
