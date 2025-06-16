import scrapy


class MangoSpider(scrapy.Spider):
    name = "mango"
    allowed_domains = ["shop.mango.com"]
    start_urls = ["https://shop.mango.com"]

    def parse(self, response):
        yield {
            'url': response.url,
        }
