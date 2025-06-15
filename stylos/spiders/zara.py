import scrapy


class ZaraSpider(scrapy.Spider):
    name = "zara"
    allowed_domains = ["zara.com"]
    start_urls = ["https://zara.com"]

    def parse(self, response):
        pass
