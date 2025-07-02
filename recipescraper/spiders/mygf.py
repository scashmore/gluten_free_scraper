import scrapy

class MyGfSpider(scrapy.Spider):
    name = 'mygf'
    allowed_domains = ['mygluten-freekitchen.com']
    start_urls = ['https://mygluten-freekitchen.com/recipes/']

    def parse(self, response):
        # Get all recipe page links on the listing page
        recipe_links = response.css('a::attr(href)').getall()
        # Filter for links that look like recipes (optional, or refine selector)
        for link in recipe_links:
            if '/recipes/' not in link and link.startswith('https://mygluten-freekitchen.com/'):
                yield response.follow(link, callback=self.parse_recipe)

    def parse_recipe(self, response):
        title = response.css('h1.entry-title::text').get()
        # Skip if not the proper structure for the recipe
        if not response.css('div.mv-create-ingredients') and not response.css('div.mv-create-instructions'):
            return

        # Ingredients section
        ingredients_sections = []
        ingredients_div = response.css('div.mv-create-ingredients')
        if ingredients_div:
            current_section = {"section": "General", "items": []}
            for el in ingredients_div.xpath("./*"):
                if el.root.tag == "h4":
                    # Save previous section if it has items
                    if current_section["items"]:
                        ingredients_sections.append(current_section)
                    current_section = {"section": el.css("::text").get().strip(), "items": []}
                elif el.root.tag == "ul":
                    items = el.css("li::text").getall()
                    current_section["items"].extend([i.strip() for i in items if i.strip()])
            if current_section["items"]:
                ingredients_sections.append(current_section)

        # Instructions section
        instructions_sections = []
        instructions_div = response.css('div.mv-create-instructions')
        if instructions_div:
            current_section = {"section": "Instructions", "steps": []}
            for el in instructions_div.xpath("./*"):
                if el.root.tag == "h4":
                    if current_section["steps"]:
                        instructions_sections.append(current_section)
                    current_section = {"section": el.css("::text").get().strip(), "steps": []}
                elif el.root.tag == "ol":
                    steps = el.css("li::text").getall()
                    current_section["steps"].extend([s.strip() for s in steps if s.strip()])
            if current_section["steps"]:
                instructions_sections.append(current_section)

        yield {
            "title": title.strip() if title else None,
            "ingredients": ingredients_sections,
            "instructions": instructions_sections,
            "url": response.url,
        }

