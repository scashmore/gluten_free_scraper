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
        yield {
            'title': response.css('h1.entry-title::text').get(),
            'ingredients': response.css('.wprm-recipe-ingredient-text::text').getall(),
            'instructions': response.css('.wprm-recipe-instruction-text::text').getall(),
            'url': response.url,
        }
