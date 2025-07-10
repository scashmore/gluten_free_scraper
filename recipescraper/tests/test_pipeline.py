import unittest
import logging
from unittest.mock import MagicMock, patch
from recipescraper.pipelines import RecipePipeline

logging.basicConfig(level=logging.DEBUG)

class TestRecipePipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = RecipePipeline()

        # Patch DB connection and cursor
        self.conn_patch = patch('recipescraper.pipelines.get_connection')
        self.mock_conn = self.conn_patch.start()
        self.mock_cursor = MagicMock()
        self.mock_conn.return_value.cursor.return_value = self.mock_cursor

        # Assign mocks
        self.pipeline.conn = self.mock_conn.return_value
        self.pipeline.cursor = self.mock_cursor

    def tearDown(self):
        self.conn_patch.stop()

    def test_parse_ingredient_line(self):
        test_cases = [
            ("2 cups sugar", (2.0, "cups", "sugar")),
            ("1/2 tsp salt", (0.5, "tsp", "salt")),
            ("1.25 tablespoons olive oil", (1.25, "tablespoons", "olive oil")),
            ("egg", (None, None, "egg")),
        ]
        for raw, expected in test_cases:
            result = self.pipeline.parse_ingredient_line(raw)
            self.assertEqual(result, expected)

    def test_flatten_instructions(self):
        instructions = [
            {"section": "Main", "steps": ["Step 1", "Step 2"]},
            {"section": "Finish", "steps": ["Step 3"]}
        ]
        result = self.pipeline.flatten_instructions(instructions)
        expected = "Main:\nStep 1\nStep 2\n\nFinish:\nStep 3"
        self.assertEqual(result, expected)

    def test_insert_recipe_calls_db(self):
        self.mock_cursor.lastrowid = 42
        item = {"title": "Test Recipe", "url": "http://example.com"}
        recipe_id = self.pipeline.insert_recipe(item)

        self.mock_cursor.execute.assert_called_once_with(
            "INSERT INTO recipes (title, url) VALUES (%s, %s)",
            ("Test Recipe", "http://example.com")
        )
        self.assertEqual(recipe_id, 42)

    def test_get_or_create_ingredient_inserts_new(self):
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.lastrowid = 5

        ingredient_id = self.pipeline.get_or_create_ingredient("parsley")

        self.mock_cursor.execute.assert_any_call(
            "SELECT id FROM ingredients WHERE name=%s", ("parsley",)
        )
        self.mock_cursor.execute.assert_any_call(
            "INSERT INTO ingredients (name) VALUES (%s)", ("parsley",)
        )
        self.assertEqual(ingredient_id, 5)

    def test_get_or_create_ingredient_returns_existing(self):
        self.mock_cursor.fetchone.return_value = (8,)

        ingredient_id = self.pipeline.get_or_create_ingredient("salt")

        self.mock_cursor.execute.assert_called_once_with(
            "SELECT id FROM ingredients WHERE name=%s", ("salt",)
        )
        self.assertEqual(ingredient_id, 8)
    
    def test_process_item_with_realistic_recipe(self):
        item = {
            "title": "Instant Pot Rice and Beans Recipe",
            "url": "https://mygluten-freekitchen.com/instant-pot-rice-and-beans-recipe/",
            "ingredients": [
                {
                    "section": "General",
                    "items": [
                        "2 large peppers (medium or hot)",
                        "1 can (16 oz.) black beans, drained and rinsed",
                        "1 can (16 oz.) pinto beans, drained and rinsed",
                        "1 can (15.5 oz.) enchilada sauce",
                        "1 can (14.5 oz.) petite diced tomatoes in sauce",
                        "1 1/2 cups white Basmati rice, uncooked",
                        "2 cups vegetable broth",
                        "1 cup sour cream",
                        "2 cups shredded Mexican cheese"
                    ]
                }
            ],
            "instructions": [
                {
                    "section": "Instructions",
                    "steps": [
                        "Slice the peppers, discard the seeds, and chop the peppers.",
                        "Drain and rinse beans and add to pressure cooker.",
                        "Add enchilada sauce and tomatoes to pressure cooker.",
                        "Add uncooked white rice to pressure cooker.",
                        "Pour vegetable broth over all. Don't stir!",
                        "Close the lid on your Instant Pot.",
                        "Stir in the sour cream.",
                        "Stir in the shredded cheese.",
                        "Serve immediately."
                    ]
                }
            ]
        }

        # Setup mocks
        self.mock_cursor.lastrowid = 101  # Pretend recipe_id
        self.mock_cursor.fetchone.side_effect = [None] * 9  # All ingredients are new

        # Run the method
        returned_item = self.pipeline.process_item(item, None)

        # Assertions
        self.assertEqual(returned_item["title"], "Instant Pot Rice and Beans Recipe")

        # Should insert 1 recipe
        self.mock_cursor.execute.assert_any_call(
            "INSERT INTO recipes (title, url) VALUES (%s, %s)",
            (item["title"], item["url"])
        )

        # Should insert 9 ingredients
        insert_ingredient_calls = [
            call for call in self.mock_cursor.execute.call_args_list
            if "INSERT INTO ingredients" in call.args[0]
        ]
        self.assertEqual(len(insert_ingredient_calls), 9)

        # Should insert 9 recipe_ingredients
        insert_recipe_ingredient_calls = [
            call for call in self.mock_cursor.execute.call_args_list
            if "INSERT INTO recipe_ingredients" in call.args[0]
        ]
        self.assertEqual(len(insert_recipe_ingredient_calls), 9)

        # Should update instructions
        self.mock_cursor.execute.assert_any_call(
            "UPDATE recipes SET instructions=%s WHERE id=%s",
            (self.pipeline.flatten_instructions(item["instructions"]), 101)
        )

        # Should commit
        self.pipeline.conn.commit.assert_called_once()


